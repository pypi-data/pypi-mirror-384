mod utils;

use dotenv::dotenv;
use fers_calculations::limits::enforce_limits;
use fers_calculations::limits::LicenseTier;
use fers_calculations::limits::LimitPolicy;
use fers_calculations::models::fers::fers::FERS;
use log::debug;
use log::error;
use std::fs;
use std::io::Write;
use std::process;
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

fn main() {
    // Initialize the logger
    logging::init_logger();
    dotenv().ok();

    let args: Vec<String> = std::env::args().collect();
    if args.len() > 1 && args[1] == "--openapi" {
        write_openapi_json_to_file("openapi.json");
        return;
    }

    // Read and parse JSON input file
    // let file_content = fs::read_to_string("083_Double_cantilever_rope_double_supported.json")
    //     .expect("Failed to read the JSON file");
    let file_content =
        fs::read_to_string("CrossCheckModel.json").expect("Failed to read the JSON file");
    // let file_content = fs::read_to_string("001_cantilever_with_end_load.json")
    //     .expect("Failed to read the JSON file");
    // let file_content = fs::read_to_string("004_triangular.json").expect("Failed to read the JSON file");
    let mut fers_data: FERS =
        serde_json::from_str(&file_content).expect("JSON was not well-formatted");

    let tier = match std::env::var("FERS_PREMIUM").ok().as_deref() {
        Some("1") | Some("true") | Some("TRUE") => LicenseTier::Premium,
        _ => LicenseTier::Free,
    };
    let policy = LimitPolicy::with_tier(tier);

    if let Err(e) = enforce_limits(&fers_data, &policy) {
        error!("Aborting: {}", e);
        eprintln!("Error: {}", e);
        process::exit(1);
    }

    // Ensure there is at least one load case in the data
    if let Some(first_load_case_id) = fers_data.load_cases.first().map(|lc| lc.id) {
        // Perform structural analysis for the first load case
        match fers_data.solve_for_load_case(first_load_case_id) {
            Ok(results) => {
                debug!("Results for Load Case {}:", first_load_case_id);
                debug!("{:#?}", results);

                // Save internal results
                if let Err(e) = FERS::save_results_to_json(&fers_data, "internal_results.json") {
                    debug!("Failed to write internal results to JSON file: {}", e);
                } else {
                    debug!("Internal results written to 'internal_results.json'");
                }
            }
            Err(e) => {
                debug!(
                    "Error during analysis for Load Case {}: {}",
                    first_load_case_id, e
                );
            }
        }
    } else {
        debug!("No load cases found in the input data.");
    }
}

#[allow(dead_code)]
fn print_readable_vector(vector: &nalgebra::DMatrix<f64>, label: &str) {
    let dof_labels = ["UX", "UY", "UZ", "RX", "RY", "RZ"]; // Translational and rotational DOFs
    debug!("{}:", label);

    let num_nodes = vector.nrows() / 6; // Number of nodes (6 DOFs per node)

    for node_index in 0..num_nodes {
        debug!("  Node {}:", node_index + 1);
        for dof_index in 0..6 {
            let value = vector[(node_index * 6 + dof_index, 0)];
            debug!("    {:<3}: {:10.4}", dof_labels[dof_index], value);
        }
    }
}

fn write_openapi_json_to_file(file_path: &str) {
    let openapi = ApiDoc::openapi();
    let json_content = openapi.to_json().expect("Failed to generate OpenAPI JSON");

    // Write JSON to a file
    let mut file = fs::File::create(file_path).expect("Failed to create the OpenAPI JSON file");
    file.write_all(json_content.as_bytes())
        .expect("Failed to write OpenAPI JSON to the file");

    debug!("OpenAPI JSON written to '{}'", file_path);
}
