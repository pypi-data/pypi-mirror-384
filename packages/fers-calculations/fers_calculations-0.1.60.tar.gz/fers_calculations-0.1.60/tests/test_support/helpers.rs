use std::collections::BTreeMap;

use fers_calculations::models::fers::fers::FERS;
use fers_calculations::models::loads::distributedload::DistributedLoad;
use fers_calculations::models::loads::distributionshape::DistributionShape;
use fers_calculations::models::loads::loadcase::LoadCase;
use fers_calculations::models::loads::nodalload::NodalLoad;
use fers_calculations::models::loads::nodalmoment::NodalMoment;
use fers_calculations::models::members::enums::MemberType;
use fers_calculations::models::members::material::Material;
use fers_calculations::models::members::member::Member;
use fers_calculations::models::members::memberset::MemberSet;
use fers_calculations::models::members::section::Section;
use fers_calculations::models::nodes::node::Node;
use fers_calculations::models::results::resultbundle::ResultsBundle;
use fers_calculations::models::settings::analysissettings::{
    AnalysisOptions, AnalysisOrder, Dimensionality, RigidStrategy,
};
use fers_calculations::models::settings::generalinfo::GeneralInfo;
use fers_calculations::models::settings::settings::Settings;
use fers_calculations::models::supports::nodalsupport::NodalSupport;
use fers_calculations::models::supports::supportcondition::SupportCondition;
use fers_calculations::models::supports::supportconditiontype::SupportConditionType;

/// Build Settings with AnalysisOption + GeneralInfo.
pub fn make_settings_with_strategy(strategy: RigidStrategy) -> Settings {
    Settings {
        id: 1,
        analysis_options: AnalysisOptions {
            id: 1,
            solve_loadcases: true,
            solver: "Direct".to_string(),
            tolerance: 1.0e-9,
            dimensionality: Dimensionality::ThreeDimensional,
            order: AnalysisOrder::Nonlinear,
            max_iterations: Some(20),
            rigid_strategy: strategy,
        },
        general_info: GeneralInfo {
            project_name: "Test Project".to_string(),
            author: "Tests".to_string(),
            version: "0.0.1".to_string(),
        },
    }
}

/// Create a fully empty FERS model with valid Settings and Results bundle.
pub fn make_fers_with_strategy(strategy: RigidStrategy) -> FERS {
    FERS {
        member_sets: Vec::new(),
        load_cases: Vec::new(),
        load_combinations: Vec::new(),
        imperfection_cases: Vec::new(),
        settings: make_settings_with_strategy(strategy),
        results: Some(ResultsBundle {
            loadcases: BTreeMap::new(),
            loadcombinations: BTreeMap::new(),
            unity_checks_overview: None,
        }),
        memberhinges: None,
        materials: Vec::new(),
        sections: Vec::new(),
        nodal_supports: Vec::new(),
        shape_paths: None,
    }
}

/// Add a Material (e.g., S235) and return its id.
pub fn add_material_s235(model: &mut FERS, id: u32) -> u32 {
    model.materials.push(Material {
        id,
        name: "S235".to_string(),
        e_mod: 210.0e9,
        g_mod: 81.0e9,
        density: 7850.0,
        yield_stress: 235.0e6,
    });
    id
}

/// Add a Section and return its id.
pub fn add_section(
    model: &mut FERS,
    id: u32,
    name: &str,
    material_id: u32,
    area_m2: f64,
    i_y_m4: f64,
    i_z_m4: f64,
    j_m4: f64,
) -> u32 {
    model.sections.push(Section {
        id,
        name: name.to_string(),
        material: material_id, // <-- u32 (not i32)
        i_y: i_y_m4,
        i_z: i_z_m4,
        j: j_m4,
        area: area_m2,
        b: None,
        h: None,
        shape_path: None,
    });
    id
}

/// Convenience: IPE180-like section using your strong-axis inertia constant (i_z).
pub fn add_section_ipe180_like(model: &mut FERS, id: u32, material_id: u32, i_z_m4: f64) -> u32 {
    let area = 26.2e-4;
    let i_y = 1.0e-6;
    let j = 1.0e-5;
    add_section(model, id, "IPE180", material_id, area, i_y, i_z_m4, j)
}

/// Fully fixed support (all DOFs fixed).
pub fn make_fixed_support(id: u32) -> NodalSupport {
    let fixed = SupportCondition {
        condition_type: SupportConditionType::Fixed,
        stiffness: None,
    };

    let mut displacement_conditions: BTreeMap<String, SupportCondition> = BTreeMap::new();
    displacement_conditions.insert("X".to_string(), fixed.clone());
    displacement_conditions.insert("Y".to_string(), fixed.clone());
    displacement_conditions.insert("Z".to_string(), fixed.clone());

    let mut rotation_conditions: BTreeMap<String, SupportCondition> = BTreeMap::new();
    rotation_conditions.insert("X".to_string(), fixed.clone());
    rotation_conditions.insert("Y".to_string(), fixed.clone());
    rotation_conditions.insert("Z".to_string(), fixed);

    NodalSupport {
        id,
        classification: None,
        displacement_conditions,
        rotation_conditions,
    }
}

/// Custom support using explicit condition types per axis.
pub fn make_support_custom(
    id: u32,
    dx: SupportConditionType,
    dy: SupportConditionType,
    dz: SupportConditionType,
    rx: SupportConditionType,
    ry: SupportConditionType,
    rz: SupportConditionType,
) -> NodalSupport {
    let mut displacement_conditions: BTreeMap<String, SupportCondition> = BTreeMap::new();
    displacement_conditions.insert(
        "X".to_string(),
        SupportCondition {
            condition_type: dx,
            stiffness: None,
        },
    );
    displacement_conditions.insert(
        "Y".to_string(),
        SupportCondition {
            condition_type: dy,
            stiffness: None,
        },
    );
    displacement_conditions.insert(
        "Z".to_string(),
        SupportCondition {
            condition_type: dz,
            stiffness: None,
        },
    );

    let mut rotation_conditions: BTreeMap<String, SupportCondition> = BTreeMap::new();
    rotation_conditions.insert(
        "X".to_string(),
        SupportCondition {
            condition_type: rx,
            stiffness: None,
        },
    );
    rotation_conditions.insert(
        "Y".to_string(),
        SupportCondition {
            condition_type: ry,
            stiffness: None,
        },
    );
    rotation_conditions.insert(
        "Z".to_string(),
        SupportCondition {
            condition_type: rz,
            stiffness: None,
        },
    );

    NodalSupport {
        id,
        classification: None,
        displacement_conditions,
        rotation_conditions,
    }
}

/// Construct a Node with explicit id and optional support id.
pub fn make_node(id: u32, x: f64, y: f64, z: f64, support_id: Option<u32>) -> Node {
    Node {
        id,
        X: x,
        Y: y,
        Z: z,
        nodal_support: support_id,
    }
}

/// Helper to copy a &Node into an owned Node (Node is not Clone).
fn copy_node(n: &Node) -> Node {
    Node {
        id: n.id,
        X: n.X,
        Y: n.Y,
        Z: n.Z,
        nodal_support: n.nodal_support,
    }
}

/// Create a Normal beam member between two Nodes (accepts &Node; copies internally).
pub fn make_beam_member(id: u32, start: &Node, end: &Node, section_id: u32) -> Member {
    Member {
        id,
        start_node: copy_node(start),
        end_node: copy_node(end),
        rotation_angle: 0.0,
        classification: "Normal".to_string(),
        weight: 0.0,
        member_type: MemberType::Normal,
        section: Some(section_id),
        start_hinge: None,
        end_hinge: None,
        reference_member: None,
        reference_node: None,
        chi: None,
    }
}

/// Create a Rigid link member between two Nodes (accepts &Node; copies internally).
pub fn make_rigid_member(id: u32, start: &Node, end: &Node) -> Member {
    Member {
        id,
        start_node: copy_node(start),
        end_node: copy_node(end),
        rotation_angle: 0.0,
        classification: "Rigid".to_string(),
        weight: 0.0,
        member_type: MemberType::Rigid,
        section: None,
        start_hinge: None,
        end_hinge: None,
        reference_member: None,
        reference_node: None,
        chi: None,
    }
}

/// Create a Tension-only truss member between two Nodes (accepts &Node; copies internally).
pub fn make_tension_only_member(id: u32, start: &Node, end: &Node, section_id: u32) -> Member {
    Member {
        id,
        start_node: copy_node(start),
        end_node: copy_node(end),
        rotation_angle: 0.0,
        classification: "Tension".to_string(),
        weight: 0.0,
        member_type: MemberType::Tension,
        section: Some(section_id),
        start_hinge: None,
        end_hinge: None,
        reference_member: None,
        reference_node: None,
        chi: None,
    }
}

/// Wrap Members into a MemberSet and push it, returning the id.
pub fn add_member_set(model: &mut FERS, id: u32, members: Vec<Member>) -> u32 {
    model.member_sets.push(MemberSet {
        id,
        members,
        classification: None,
        l_y: None,
        l_z: None,
    });
    id
}

/// Create and push a LoadCase, returning its id.
pub fn add_load_case(model: &mut FERS, id: u32, name: &str) -> u32 {
    model.load_cases.push(LoadCase {
        id,
        name: name.to_string(),
        nodal_loads: Vec::new(),
        nodal_moments: Vec::new(),
        distributed_loads: Vec::new(),
        rotation_imperfections: Vec::new(),
        translation_imperfections: Vec::new(),
    });
    id
}

/// Push a NodalLoad to an existing LoadCase (direction is a tuple).
pub fn add_nodal_load(
    model: &mut FERS,
    id: u32,
    load_case_id: u32,
    node_id: u32,
    magnitude: f64,
    direction: (f64, f64, f64),
) {
    let lc = model
        .load_cases
        .iter_mut()
        .find(|lc| lc.id == load_case_id)
        .expect("LoadCase not found");
    lc.nodal_loads.push(NodalLoad {
        id,
        node: node_id,
        load_case: load_case_id,
        magnitude,
        direction,
        load_type: "Force".to_string(),
    });
}

/// Push a NodalMoment to an existing LoadCase (direction is a tuple).
pub fn add_nodal_moment(
    model: &mut FERS,
    id: u32,
    load_case_id: u32,
    node_id: u32,
    magnitude: f64,
    direction: (f64, f64, f64),
) {
    let lc = model
        .load_cases
        .iter_mut()
        .find(|lc| lc.id == load_case_id)
        .expect("LoadCase not found");
    lc.nodal_moments.push(NodalMoment {
        id,
        node: node_id,
        load_case: load_case_id,
        magnitude,
        direction,
        load_type: "Moment".to_string(),
    });
}

/// Push a Uniform DistributedLoad to an existing LoadCase (direction is a tuple).
pub fn add_distributed_load_uniform(
    model: &mut FERS,
    _id: u32, // not used by DistributedLoad struct in your code
    load_case_id: u32,
    member_id: u32,
    magnitude_n_per_m: f64,
    direction: (f64, f64, f64),
    start_frac: f64,
    end_frac: f64,
) {
    let lc = model
        .load_cases
        .iter_mut()
        .find(|lc| lc.id == load_case_id)
        .expect("LoadCase not found");

    lc.distributed_loads.push(DistributedLoad {
        member: member_id,
        load_case: load_case_id,
        distribution_shape: DistributionShape::Uniform,
        magnitude: magnitude_n_per_m,
        end_magnitude: magnitude_n_per_m,
        direction,
        start_frac,
        end_frac,
    });
}
