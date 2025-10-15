use std::collections::HashMap;

use crate::models::members::memberhinge::{AxisMode, MemberHinge};
use nalgebra::DMatrix;

fn submatrix_by_indices(k: &DMatrix<f64>, rows: &[usize], cols: &[usize]) -> DMatrix<f64> {
    let mut out = DMatrix::<f64>::zeros(rows.len(), cols.len());
    for (i_out, &i_in) in rows.iter().enumerate() {
        for (j_out, &j_in) in cols.iter().enumerate() {
            out[(i_out, j_out)] = k[(i_in, j_in)];
        }
    }
    out
}

/// Local 12-DOF index helper.
/// Local ordering: [uX,uY,uZ,thX,thY,thZ]_A, then [uX,uY,uZ,thX,thY,thZ]_B
fn local_dof_index(is_end_b: bool, is_rot: bool, axis: usize) -> usize {
    let base = if is_end_b { 6 } else { 0 };
    if is_rot {
        base + 3 + axis
    } else {
        base + axis
    }
}

/// Convert Option<f64> to AxisMode (Rigid / Release / Spring(k))
pub fn axis_mode_from_option(value: Option<f64>) -> AxisMode {
    match value {
        None => AxisMode::Rigid,
        Some(k) if k > 0.0 => AxisMode::Spring(k),
        Some(_) => AxisMode::Release,
    }
}

/// Per-end modes (LOCAL axes) directly from hinges.
/// Returns (A_trans, A_rot, B_trans, B_rot).
pub fn modes_from_single_ends(
    a: Option<&MemberHinge>,
    b: Option<&MemberHinge>,
) -> ([AxisMode; 3], [AxisMode; 3], [AxisMode; 3], [AxisMode; 3]) {
    let (vx_a, vy_a, vz_a, mx_a, my_a, mz_a) = a
        .map(|h| {
            (
                h.translational_release_vx,
                h.translational_release_vy,
                h.translational_release_vz,
                h.rotational_release_mx,
                h.rotational_release_my,
                h.rotational_release_mz,
            )
        })
        .unwrap_or((None, None, None, None, None, None));

    let (vx_b, vy_b, vz_b, mx_b, my_b, mz_b) = b
        .map(|h| {
            (
                h.translational_release_vx,
                h.translational_release_vy,
                h.translational_release_vz,
                h.rotational_release_mx,
                h.rotational_release_my,
                h.rotational_release_mz,
            )
        })
        .unwrap_or((None, None, None, None, None, None));

    let a_trans = [
        axis_mode_from_option(vx_a),
        axis_mode_from_option(vy_a),
        axis_mode_from_option(vz_a),
    ];
    let a_rot = [
        axis_mode_from_option(mx_a),
        axis_mode_from_option(my_a),
        axis_mode_from_option(mz_a),
    ];
    let b_trans = [
        axis_mode_from_option(vx_b),
        axis_mode_from_option(vy_b),
        axis_mode_from_option(vz_b),
    ];
    let b_rot = [
        axis_mode_from_option(mx_b),
        axis_mode_from_option(my_b),
        axis_mode_from_option(mz_b),
    ];

    (a_trans, a_rot, b_trans, b_rot)
}

/// Apply end releases and semi-rigid springs to a LOCAL 12x12 beam stiffness.
/// Static condensation on the released DOFs (with optional node-to-ground spring).
pub fn apply_end_releases_to_local_beam_k(
    k_local_in: &DMatrix<f64>, // must be 12x12
    a_trans: [AxisMode; 3],
    a_rot: [AxisMode; 3],
    b_trans: [AxisMode; 3],
    b_rot: [AxisMode; 3],
) -> Result<DMatrix<f64>, String> {
    if k_local_in.nrows() != 12 || k_local_in.ncols() != 12 {
        return Err("apply_end_releases_to_local_beam_k: matrix must be 12x12".to_string());
    }

    struct RelInfo {
        local_index: usize, // 0..11
        k_series: f64,      // >= 0.0 ; 0.0 = free release
    }

    let mut rels: Vec<RelInfo> = Vec::new();

    let mut consider = |is_end_b: bool, is_rot: bool, modes: [AxisMode; 3]| {
        for (axis, mode) in modes.iter().enumerate() {
            match *mode {
                AxisMode::Rigid => { /* no interface */ }
                AxisMode::Release => {
                    rels.push(RelInfo {
                        local_index: local_dof_index(is_end_b, is_rot, axis),
                        k_series: 0.0,
                    });
                }
                AxisMode::Spring(kval) => {
                    let kpos = if kval.is_finite() { kval.max(0.0) } else { 0.0 };
                    rels.push(RelInfo {
                        local_index: local_dof_index(is_end_b, is_rot, axis),
                        k_series: kpos,
                    });
                }
            }
        }
    };

    consider(false, false, a_trans);
    consider(false, true, a_rot);
    consider(true, false, b_trans);
    consider(true, true, b_rot);

    if rels.is_empty() {
        return Ok(k_local_in.clone());
    }

    // Map each affected local DOF to an internal interface DOF at the end of the matrix.
    let n_rel = rels.len();
    let n_aug = 12 + n_rel;

    let mut loc_to_int: HashMap<usize, usize> = HashMap::new();
    for (p, r) in rels.iter().enumerate() {
        loc_to_int.insert(r.local_index, 12 + p);
    }

    // Augmented matrix: move member stiffness on affected DOFs to the interface side.
    let mut k_aug = DMatrix::<f64>::zeros(n_aug, n_aug);

    for i in 0..12 {
        for j in 0..12 {
            let val = k_local_in[(i, j)];
            if val == 0.0 {
                continue;
            }
            let ii = *loc_to_int.get(&i).unwrap_or(&i);
            let jj = *loc_to_int.get(&j).unwrap_or(&j);
            k_aug[(ii, jj)] += val;
        }
    }

    // Add series springs: node DOF <-> interface DOF
    for r in &rels {
        let node_i = r.local_index;
        let int_i = *loc_to_int
            .get(&r.local_index)
            .expect("internal index exists");
        let k = r.k_series;

        if k > 0.0 {
            // Two-node spring between node_i and int_i: [+k -k; -k +k]
            k_aug[(node_i, node_i)] += k;
            k_aug[(int_i, int_i)] += k;
            k_aug[(node_i, int_i)] -= k;
            k_aug[(int_i, node_i)] -= k;
        }
        // Release (k=0): node and interface are uncoupled; member lives only on interface side.
    }

    // Condense interface DOFs back to 12x12
    let keep_idx: Vec<usize> = (0..12).collect();
    let elim_idx: Vec<usize> = (0..n_rel).map(|p| 12 + p).collect();

    let k_kk = submatrix_by_indices(&k_aug, &keep_idx, &keep_idx);
    let k_kr = submatrix_by_indices(&k_aug, &keep_idx, &elim_idx);
    let k_rk = submatrix_by_indices(&k_aug, &elim_idx, &keep_idx);
    let k_rr = submatrix_by_indices(&k_aug, &elim_idx, &elim_idx);

    let x = k_rr.lu().solve(&k_rk).ok_or_else(|| {
        "apply_end_releases_to_local_beam_k: interface block is singular (check release pattern)"
            .to_string()
    })?;

    let k_eff = &k_kk - &(k_kr * x);
    Ok(k_eff)
}

/// LOCAL 12x12 matrix for node-to-ground translational springs at ends A and B (trusses).
/// Only translations are considered; rotations are ignored.
pub fn build_local_truss_translational_spring_k(
    a_trans: [AxisMode; 3],
    b_trans: [AxisMode; 3],
) -> DMatrix<f64> {
    let mut k = DMatrix::<f64>::zeros(12, 12);

    for (axis, mode) in a_trans.iter().enumerate() {
        if let AxisMode::Spring(ka) = *mode {
            let i = local_dof_index(false, false, axis);
            k[(i, i)] += ka.max(0.0);
        }
    }

    for (axis, mode) in b_trans.iter().enumerate() {
        if let AxisMode::Spring(kb) = *mode {
            let i = local_dof_index(true, false, axis);
            k[(i, i)] += kb.max(0.0);
        }
    }

    k
}
