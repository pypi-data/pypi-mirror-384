// src/functions/support_utils.rs
use std::collections::{BTreeMap, HashMap, HashSet};

use crate::functions::geometry::{compute_num_dofs_from_members, dof_index};
use crate::models::fers::fers::{FERS, ROTATION_AXES, TRANSLATION_AXES};
use crate::models::members::enums::MemberType;
use crate::models::members::memberset::MemberSet;
use crate::models::supports::nodalsupport::NodalSupport;
use crate::models::supports::supportcondition::SupportCondition;
use crate::models::supports::supportconditiontype::SupportConditionType;
use nalgebra::DMatrix;

pub fn visit_unique_supported_nodes<F>(
    member_sets: &[MemberSet],
    nodal_supports: &[NodalSupport],
    mut visitor: F,
) -> Result<(), String>
where
    F: FnMut(u32, usize, &NodalSupport) -> Result<(), String>,
{
    let support_by_id: HashMap<u32, &NodalSupport> =
        nodal_supports.iter().map(|s| (s.id, s)).collect();

    let mut seen: HashSet<u32> = HashSet::new();

    for member_set in member_sets {
        for member in &member_set.members {
            for node in [&member.start_node, &member.end_node] {
                if !seen.insert(node.id) {
                    continue;
                }
                if let Some(support_id) = node.nodal_support {
                    if let Some(support) = support_by_id.get(&support_id) {
                        let base_index = dof_index(node.id, 0);
                        visitor(node.id, base_index, support)?;
                    }
                }
            }
        }
    }
    Ok(())
}

pub fn detect_zero_energy_dofs(fers: &FERS) -> std::collections::HashSet<usize> {
    use std::collections::HashSet;

    let number_of_dofs: usize = compute_num_dofs_from_members(&fers.member_sets);

    let mut has_stiffness = vec![false; number_of_dofs];
    let mut is_directly_constrained = vec![false; number_of_dofs];
    let mut is_directly_loaded = vec![false; number_of_dofs];

    // 1) Mark stiffness participation per element type
    for set in &fers.member_sets {
        for member in &set.members {
            let i0 = (member.start_node.id as usize - 1) * 6;
            let j0 = (member.end_node.id as usize - 1) * 6;

            match member.member_type {
                MemberType::Normal => {
                    for d in 0..6 {
                        has_stiffness[i0 + d] = true;
                    }
                    for d in 0..6 {
                        has_stiffness[j0 + d] = true;
                    }
                }
                // Truss/Tension/Compression: translations only, no rotations
                MemberType::Truss | MemberType::Tension | MemberType::Compression => {
                    for d in 0..3 {
                        has_stiffness[i0 + d] = true;
                    }
                    for d in 0..3 {
                        has_stiffness[j0 + d] = true;
                    }
                    // leave rotations false here
                }
                // Rigid: handled by rigid graph/MPC, no direct stiffness rows to keep
                MemberType::Rigid => {}
            }
        }
    }

    let support_by_id: std::collections::HashMap<u32, &NodalSupport> =
        fers.nodal_supports.iter().map(|s| (s.id, s)).collect();

    for set in &fers.member_sets {
        for member in &set.members {
            for node in [&member.start_node, &member.end_node] {
                let base_full = (node.id as usize - 1) * 6;

                if let Some(sup_id) = node.nodal_support {
                    if let Some(sup) = support_by_id.get(&sup_id) {
                        // Translations
                        for (axis_label, local_dof) in TRANSLATION_AXES {
                            if let Some(cond) =
                                sup.displacement_conditions.get(axis_label).or_else(|| {
                                    sup.displacement_conditions
                                        .get(&axis_label.to_ascii_lowercase())
                                })
                            {
                                let idx = base_full + local_dof;
                                // Fixed or explicit spring => keep
                                if matches!(cond.condition_type, SupportConditionType::Fixed)
                                    || cond.stiffness.unwrap_or(0.0) > 0.0
                                {
                                    is_directly_constrained[idx] = true;
                                }
                            }
                        }
                        // Rotations
                        for (axis_label, local_dof) in ROTATION_AXES {
                            if let Some(cond) =
                                sup.rotation_conditions.get(axis_label).or_else(|| {
                                    sup.rotation_conditions
                                        .get(&axis_label.to_ascii_lowercase())
                                })
                            {
                                let idx = base_full + local_dof;
                                if matches!(cond.condition_type, SupportConditionType::Fixed)
                                    || cond.stiffness.unwrap_or(0.0) > 0.0
                                {
                                    is_directly_constrained[idx] = true;
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // 3) Mark direct nodal loads (forces map to translations, moments map to rotations)
    for lc in &fers.load_cases {
        for nl in &lc.nodal_loads {
            // direction is [dx, dy, dz] in your model => translations
            let base_full = (nl.node as usize - 1) * 6;
            let direction_values = [nl.direction.0, nl.direction.1, nl.direction.2];
            for (comp, local_dof) in [(0usize, 0usize), (1usize, 1usize), (2usize, 2usize)] {
                if direction_values[comp].abs() != 0.0 && nl.magnitude.abs() > 0.0 {
                    is_directly_loaded[base_full + local_dof] = true;
                }
            }
            for nm in &lc.nodal_moments {
                // moments excite rotations
                let base_full = (nm.node as usize - 1) * 6;
                let direction_values = [nm.direction.0, nm.direction.1, nm.direction.2];
                for (comp, local_dof) in [(0usize, 3usize), (1usize, 4usize), (2usize, 5usize)] {
                    if direction_values[comp].abs() != 0.0 && nm.magnitude.abs() > 0.0 {
                        is_directly_loaded[base_full + local_dof] = true;
                    }
                }
            }
        }
    }

    // 4) Decide zero-energy DOFs
    let mut zero_energy: HashSet<usize> = HashSet::new();
    for dof in 0..number_of_dofs {
        let has_any_stiffness = has_stiffness[dof];
        let constrained = is_directly_constrained[dof];
        let loaded = is_directly_loaded[dof];

        if !has_any_stiffness && !constrained && !loaded {
            zero_energy.insert(dof);
        }
    }

    zero_energy
}

/// Case-insensitive fetch of a support condition from a per-axis map.
pub fn get_support_condition<'a>(
    map: &'a BTreeMap<String, SupportCondition>,
    axis_label: &str,
) -> Option<&'a SupportCondition> {
    map.get(axis_label)
        .or_else(|| map.get(&axis_label.to_ascii_lowercase()))
}

pub fn add_support_springs_to_operator(
    member_sets: &[MemberSet],
    nodal_supports: &[NodalSupport],
    k_global: &mut DMatrix<f64>,
) -> Result<(), String> {
    visit_unique_supported_nodes(
        member_sets,
        nodal_supports,
        |_node_id, base_index, support| {
            // Translational springs
            for (axis_label, local_dof) in TRANSLATION_AXES {
                if let Some(cond) =
                    get_support_condition(&support.displacement_conditions, axis_label)
                {
                    if let SupportConditionType::Spring = cond.condition_type {
                        let k = spring_stiffness_or_error(
                            support.id,
                            axis_label,
                            "displacement",
                            cond.stiffness,
                        )?;
                        k_global[(base_index + local_dof, base_index + local_dof)] += k;
                    }
                }
            }

            // Rotational springs
            for (axis_label, local_dof) in ROTATION_AXES {
                if let Some(cond) = get_support_condition(&support.rotation_conditions, axis_label)
                {
                    if let SupportConditionType::Spring = cond.condition_type {
                        let k = spring_stiffness_or_error(
                            support.id,
                            axis_label,
                            "rotation",
                            cond.stiffness,
                        )?;
                        k_global[(base_index + local_dof, base_index + local_dof)] += k;
                    }
                }
            }

            Ok(())
        },
    )
}

/// Validate stiffness option and return k > 0 (uniform error text).
pub fn spring_stiffness_or_error(
    owner_id: u32,
    axis_label: &str,
    kind_label: &str,
    stiffness: Option<f64>,
) -> Result<f64, String> {
    let k = stiffness.ok_or_else(|| {
        format!(
            "Support {} {} {} is Spring but stiffness is missing.",
            owner_id, kind_label, axis_label
        )
    })?;
    if k <= 0.0 {
        return Err(format!(
            "Support {} {} {} Spring stiffness must be positive.",
            owner_id, kind_label, axis_label
        ));
    }
    Ok(k)
}

/// Strong Dirichlet on a single DOF.
pub fn constrain_single_dof(
    k: &mut DMatrix<f64>,
    rhs: &mut DMatrix<f64>,
    dof_index: usize,
    prescribed: f64,
) {
    for j in 0..k.ncols() {
        k[(dof_index, j)] = 0.0;
    }
    for i in 0..k.nrows() {
        k[(i, dof_index)] = 0.0;
    }
    k[(dof_index, dof_index)] = 1.0;
    rhs[(dof_index, 0)] = prescribed;
}
