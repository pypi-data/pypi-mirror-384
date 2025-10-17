mod utils;

use dotenv::dotenv;
use fers_calculations::limits::enforce_limits;
use fers_calculations::limits::LimitPolicy;
use fers_calculations::models::fers::fers::FERS;
use std::fs;
use std::io::Write;
use utils::logging;
use utoipa::OpenApi;

#[derive(OpenApi)]
#[openapi(
    components(schemas(FERS)),
    paths(),
    info(
        title = "FERS Structural Analysis API",
        version = "0.1.0",
        description = "OpenAPI for FERS structural analysis application."
    )
)]
struct ApiDoc;

fn print_usage_and_exit(exit_code: i32) -> ! {
    eprintln!(
        "Usage:
  main [--input <path> | <path>] [--openapi [path]]

Examples:
  main CrossCheckModel.json
  main --input CrossCheckModel.json
  main --openapi
  main --openapi openapi.json

Notes:
  --openapi will generate the OpenAPI spec to the given path (default: openapi.json)
  and then exit without running an analysis."
    );
    std::process::exit(exit_code);
}

fn main() {
    logging::init_logger();
    dotenv().ok();

    // ----------------------------
    // Argument parsing
    // ----------------------------
    // Supported:
    //   --openapi [path]        → write OpenAPI JSON and exit
    //   --input <path> | <path> → input JSON for analysis (positional or via --input)
    //   --help                  → print usage
    let mut input_json_path_opt: Option<String> = None;
    let mut openapi_out_opt: Option<String> = None;

    let mut args = std::env::args().skip(1).peekable();
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--help" | "-h" => {
                print_usage_and_exit(0);
            }
            "--openapi" => {
                // Optional next token as output path unless it looks like another flag
                if let Some(next) = args.peek() {
                    if !next.starts_with("--") {
                        openapi_out_opt = Some(args.next().unwrap());
                    } else {
                        openapi_out_opt = Some("openapi.json".to_string());
                    }
                } else {
                    openapi_out_opt = Some("openapi.json".to_string());
                }
            }
            "--input" => {
                let Some(path) = args.next() else {
                    eprintln!("Error: --input requires a path.");
                    print_usage_and_exit(2);
                };
                input_json_path_opt = Some(path);
            }
            // First bare argument can be treated as input path if not set yet
            _ if !arg.starts_with("--") && input_json_path_opt.is_none() => {
                input_json_path_opt = Some(arg);
            }
            other => {
                eprintln!("Error: Unknown argument '{}'.", other);
                print_usage_and_exit(2);
            }
        }
    }

    // If --openapi was requested, write the file and exit early.
    if let Some(openapi_out_path) = openapi_out_opt {
        write_openapi_json_to_file(&openapi_out_path);
        println!("OpenAPI JSON written to '{}'.", openapi_out_path);
        return;
    }

    let input_json_path: String =
        input_json_path_opt.unwrap_or_else(|| "091_Loadcombinations_cantilever.json".to_string());

    // ----------------------------
    // Read and parse input model
    // ----------------------------
    let file_content: String = match std::fs::read_to_string(&input_json_path) {
        Ok(content) => content,
        Err(error) => {
            eprintln!("Failed to read JSON file '{}': {}", &input_json_path, error);
            std::process::exit(1);
        }
    };

    let mut fers_data: fers_calculations::models::fers::fers::FERS =
        match serde_json::from_str(&file_content) {
            Ok(model) => model,
            Err(error) => {
                eprintln!(
                    "Input JSON in '{}' was not well-formatted: {}",
                    &input_json_path, error
                );
                std::process::exit(1);
            }
        };

    // ----------------------------
    // Limits policy and enforcement
    // ----------------------------
    let limit_policy: LimitPolicy = LimitPolicy::free();

    if let Err(error) = enforce_limits(&fers_data, &limit_policy) {
        log::error!("Aborting due to limits enforcement: {}", error);
        eprintln!("Error: {}", error);
        std::process::exit(1);
    }

    // ----------------------------
    // Log analysis configuration
    // ----------------------------
    let analysis_options = &fers_data.settings.analysis_options;
    log::info!(
        "Analysis configuration → order={:?}, rigid_strategy={:?}, solve_loadcases={}, max_iterations={}, tolerance={}",
        analysis_options.order,
        analysis_options.rigid_strategy,
        analysis_options.solve_loadcases,
        analysis_options.max_iterations.unwrap_or(20),
        analysis_options.tolerance
    );
    log::info!(
        "Model summary → member_sets={}, members_total={}, load_cases={}, load_combinations={}",
        fers_data.member_sets.len(),
        fers_data.get_member_count(),
        fers_data.load_cases.len(),
        fers_data.load_combinations.len()
    );

    // ----------------------------
    // Prepare solver settings
    // ----------------------------
    use fers_calculations::models::settings::analysissettings::AnalysisOrder;
    let use_second_order_solver: bool = matches!(analysis_options.order, AnalysisOrder::Nonlinear);
    let maximum_iterations: usize = analysis_options.max_iterations.unwrap_or(20) as usize;
    let tolerance: f64 = analysis_options.tolerance;

    // Collect identifiers before mutating through solves
    let load_case_identifiers: Vec<u32> = fers_data
        .load_cases
        .iter()
        .map(|load_case| load_case.id)
        .collect();
    let load_combination_identifiers: Vec<u32> = fers_data
        .load_combinations
        .iter()
        .map(|combination| combination.id)
        .collect();

    // ----------------------------
    // Solve load cases (optional)
    // ----------------------------
    if analysis_options.solve_loadcases {
        for load_case_identifier in load_case_identifiers {
            if use_second_order_solver {
                log::info!(
                    "Solving load case {} with second-order (Newton–Raphson), tolerance={}, max_iterations={}",
                    load_case_identifier,
                    tolerance,
                    maximum_iterations
                );
                match fers_data.solve_for_load_case_second_order(
                    load_case_identifier,
                    maximum_iterations,
                    tolerance,
                ) {
                    Ok(results) => log::debug!(
                        "Results (second-order) LC {}: {:#?}",
                        load_case_identifier,
                        results
                    ),
                    Err(error) => log::error!(
                        "Error while solving load case {} (second-order): {}",
                        load_case_identifier,
                        error
                    ),
                }
            } else {
                log::info!(
                    "Solving load case {} with first-order (linear).",
                    load_case_identifier
                );
                match fers_data.solve_for_load_case(load_case_identifier) {
                    Ok(results) => log::debug!(
                        "Results (first-order) LC {}: {:#?}",
                        load_case_identifier,
                        results
                    ),
                    Err(error) => log::error!(
                        "Error while solving load case {} (first-order): {}",
                        load_case_identifier,
                        error
                    ),
                }
            }
        }
    } else {
        log::info!("Skipping load cases because 'solve_loadcases' is set to false.");
    }

    // ----------------------------
    // Solve load combinations (always if any)
    // ----------------------------
    for load_combination_identifier in load_combination_identifiers {
        if use_second_order_solver {
            log::info!(
                "Solving load combination {} with second-order (Newton–Raphson), tolerance={}, max_iterations={}",
                load_combination_identifier,
                tolerance,
                maximum_iterations
            );
            match fers_data.solve_for_load_combination_second_order(
                load_combination_identifier,
                maximum_iterations,
                tolerance,
            ) {
                Ok(results) => log::debug!(
                    "Results (second-order) combination {}: {:#?}",
                    load_combination_identifier,
                    results
                ),
                Err(error) => log::error!(
                    "Error while solving combination {} (second-order): {}",
                    load_combination_identifier,
                    error
                ),
            }
        } else {
            log::info!(
                "Solving load combination {} with first-order (linear).",
                load_combination_identifier
            );
            match fers_data.solve_for_load_combination(load_combination_identifier) {
                Ok(results) => log::debug!(
                    "Results (first-order) combination {}: {:#?}",
                    load_combination_identifier,
                    results
                ),
                Err(error) => log::error!(
                    "Error while solving combination {} (first-order): {}",
                    load_combination_identifier,
                    error
                ),
            }
        }
    }

    // ----------------------------
    // Persist results embedded in the model
    // ----------------------------
    let output_results_path: &str = "internal_results.json";
    match fers_calculations::models::fers::fers::FERS::save_results_to_json(
        &fers_data,
        output_results_path,
    ) {
        Ok(()) => {
            log::info!("Internal results written to '{}'.", output_results_path);
        }
        Err(error) => {
            log::error!(
                "Failed to write internal results to JSON file '{}': {}",
                output_results_path,
                error
            );
        }
    }
}

#[allow(dead_code)]
fn print_readable_vector(vector: &nalgebra::DMatrix<f64>, label: &str) {
    let dof_labels = ["UX", "UY", "UZ", "RX", "RY", "RZ"];
    log::debug!("{}:", label);

    let num_nodes = vector.nrows() / 6;

    for node_index in 0..num_nodes {
        log::debug!("  Node {}:", node_index + 1);
        for dof_index in 0..6 {
            let value = vector[(node_index * 6 + dof_index, 0)];
            log::debug!("    {:<3}: {:10.4}", dof_labels[dof_index], value);
        }
    }
}

fn write_openapi_json_to_file(file_path: &str) {
    let openapi = ApiDoc::openapi();
    let json_content = openapi.to_json().expect("Failed to generate OpenAPI JSON");

    let mut file = fs::File::create(file_path).expect("Failed to create the OpenAPI JSON file");
    file.write_all(json_content.as_bytes())
        .expect("Failed to write OpenAPI JSON to the file");

    log::debug!("OpenAPI JSON written to '{}'", file_path);
}
