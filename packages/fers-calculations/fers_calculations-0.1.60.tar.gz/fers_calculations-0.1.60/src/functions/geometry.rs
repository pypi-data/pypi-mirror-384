use crate::functions::hinge_and_release_operations::{
    apply_end_releases_to_local_beam_k, modes_from_single_ends,
};
use crate::models::members::member::Member;
use crate::models::members::memberhinge::MemberHinge;
use nalgebra::DMatrix;
use std::collections::HashMap;

// src/functions/geometry.rs
use crate::models::members::memberset::MemberSet;

/// Returns the six degrees of freedom indices for the given node.
/// The first three are for translational DOFs (X, Y, Z) and the next three for rotational DOFs (RX, RY, RZ).
pub fn get_dof_indices(node_id: usize) -> (usize, usize, usize, usize, usize, usize) {
    let base_index = (node_id - 1) * 6;
    (
        base_index,     // X translation
        base_index + 1, // Y translation
        base_index + 2, // Z translation
        base_index + 3, // X rotation
        base_index + 4, // Y rotation
        base_index + 5, // Z rotation
    )
}

pub fn dof_index(node_id: u32, local_dof: usize) -> usize {
    (node_id as usize - 1) * 6 + local_dof
}

pub fn compute_num_dofs_from_members(member_sets: &[MemberSet]) -> usize {
    let max_node = member_sets
        .iter()
        .flat_map(|ms| ms.members.iter())
        .flat_map(|m| [m.start_node.id, m.end_node.id])
        .max()
        .unwrap_or(0) as usize;
    max_node * 6
}

pub fn local_to_global_with_releases(
    member: &Member,
    k_local_base: &DMatrix<f64>,
    hinge_by_id: &HashMap<u32, &MemberHinge>,
) -> Result<DMatrix<f64>, String> {
    let a_h = member
        .start_hinge
        .and_then(|id| hinge_by_id.get(&id).copied());
    let b_h = member
        .end_hinge
        .and_then(|id| hinge_by_id.get(&id).copied());
    let (a_trans, a_rot, b_trans, b_rot) = modes_from_single_ends(a_h, b_h);

    let k_local_mod =
        apply_end_releases_to_local_beam_k(k_local_base, a_trans, a_rot, b_trans, b_rot)?;

    let t = member.calculate_transformation_matrix_3d();
    Ok(t.transpose() * k_local_mod * t)
}
