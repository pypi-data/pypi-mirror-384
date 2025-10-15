// src/models/fers/fers.rs
use crate::functions::geometry::{
    compute_num_dofs_from_members, dof_index, local_to_global_with_releases,
};
use crate::functions::results::{compute_member_results_from_displacement, extract_displacements};
use crate::functions::rigid_graph::RigidGraph;
use crate::functions::support_utils::{
    add_support_springs_to_operator, constrain_single_dof, detect_zero_energy_dofs,
};
use crate::models::settings::analysissettings::RigidStrategy;
use nalgebra::DMatrix;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};
use utoipa::ToSchema;

use crate::functions::hinge_and_release_operations::{
    build_local_truss_translational_spring_k, modes_from_single_ends,
};
use crate::functions::load_assembler::{
    assemble_distributed_loads, assemble_nodal_loads, assemble_nodal_moments,
};
use crate::functions::reactions::{
    compose_support_reaction_vector_equilibrium, extract_reaction_nodes,
};

use crate::models::imperfections::imperfectioncase::ImperfectionCase;
use crate::models::loads::loadcase::LoadCase;
use crate::models::loads::loadcombination::LoadCombination;
use crate::models::members::enums::MemberType;
use crate::models::members::memberset::MemberSet;
use crate::models::members::{
    material::Material, memberhinge::MemberHinge, section::Section, shapepath::ShapePath,
};
use crate::models::results::resultbundle::ResultsBundle;
use crate::models::results::results::{ResultType, Results};
use crate::models::results::resultssummary::ResultsSummary;
use crate::models::settings::settings::Settings;
use crate::models::supports::nodalsupport::NodalSupport;
use crate::models::supports::supportconditiontype::SupportConditionType;

#[derive(Serialize, Deserialize, ToSchema, Debug)]
pub struct FERS {
    pub member_sets: Vec<MemberSet>,
    pub load_cases: Vec<LoadCase>,
    pub load_combinations: Vec<LoadCombination>,
    pub imperfection_cases: Vec<ImperfectionCase>,
    pub settings: Settings,
    pub results: Option<ResultsBundle>,
    pub memberhinges: Option<Vec<MemberHinge>>,
    pub materials: Vec<Material>,
    pub sections: Vec<Section>,
    pub nodal_supports: Vec<NodalSupport>,
    pub shape_paths: Option<Vec<ShapePath>>,
}

const AXIAL_SLACK_TOLERANCE_DEFAULT: f64 = 1.0e-6;

struct RigidElimination {
    s: DMatrix<f64>,
    full_to_red: HashMap<usize, usize>,
}

pub struct AssemblyContext<'a> {
    pub material_by_id: HashMap<u32, &'a Material>,
    pub section_by_id: HashMap<u32, &'a Section>,
    pub hinge_by_id: HashMap<u32, &'a MemberHinge>,
    pub support_by_id: HashMap<u32, &'a NodalSupport>,
}

impl<'a> AssemblyContext<'a> {
    pub fn new(model: &'a FERS) -> Self {
        let (material_by_id, section_by_id, hinge_by_id, support_by_id) = model.build_lookup_maps();
        Self {
            material_by_id,
            section_by_id,
            hinge_by_id,
            support_by_id,
        }
    }
}

pub const TRANSLATION_AXES: [(&str, usize); 3] = [("X", 0), ("Y", 1), ("Z", 2)];
pub const ROTATION_AXES: [(&str, usize); 3] = [("X", 3), ("Y", 4), ("Z", 5)];

impl FERS {
    pub fn build_lookup_maps(
        &self,
    ) -> (
        HashMap<u32, &Material>,
        HashMap<u32, &Section>,
        HashMap<u32, &MemberHinge>,
        HashMap<u32, &NodalSupport>,
    ) {
        let material_map: HashMap<u32, &Material> =
            self.materials.iter().map(|m| (m.id, m)).collect();
        let section_map: HashMap<u32, &Section> = self.sections.iter().map(|s| (s.id, s)).collect();
        let memberhinge_map: HashMap<u32, &MemberHinge> = self
            .memberhinges
            .iter()
            .flatten()
            .map(|mh| (mh.id, mh))
            .collect();
        let support_map: HashMap<u32, &NodalSupport> =
            self.nodal_supports.iter().map(|s| (s.id, s)).collect();

        (material_map, section_map, memberhinge_map, support_map)
    }

    fn build_operator_with_supports(
        &self,
        active_map: &std::collections::HashMap<u32, bool>,
        displacement: Option<&nalgebra::DMatrix<f64>>,
    ) -> Result<nalgebra::DMatrix<f64>, String> {
        let mut k = self.assemble_global_stiffness_matrix(active_map)?;
        if let Some(u) = displacement {
            let k_geo = self.assemble_geometric_stiffness_matrix_with_active(u, active_map)?;
            k += k_geo;
        }
        add_support_springs_to_operator(&self.member_sets, &self.nodal_supports, &mut k)?;
        Ok(k)
    }

    fn build_rigid_elimination_partial_using_hinges(&self) -> Result<RigidElimination, String> {
        use std::collections::{HashMap, HashSet};

        #[derive(Clone, Copy)]
        struct RigidInfo {
            a: u32,
            b: u32,
            r: (f64, f64, f64),
        }

        let node_has_elastic_or_support = |node_id: u32| -> bool {
            if self.nodal_supports.iter().any(|s| s.id == node_id) {
                return true;
            }
            for ms in &self.member_sets {
                for m in &ms.members {
                    if (m.start_node.id == node_id || m.end_node.id == node_id)
                        && !matches!(m.member_type, MemberType::Rigid)
                    {
                        return true;
                    }
                }
            }
            false
        };

        // Build rigid edges once
        let rigid = RigidGraph::build(&self.member_sets)?;
        let mut rigid_elems: Vec<RigidInfo> = rigid
            .edges_sorted_master_first()
            .into_iter()
            .map(|e| RigidInfo {
                a: e.master,
                b: e.slave,
                r: e.r,
            })
            .collect();

        // Prefer the anchored end as master
        for info in &mut rigid_elems {
            let a_anchored = node_has_elastic_or_support(info.a);
            let b_anchored = node_has_elastic_or_support(info.b);
            if !a_anchored && b_anchored {
                std::mem::swap(&mut info.a, &mut info.b);
                info.r = (-info.r.0, -info.r.1, -info.r.2);
            }
        }

        let number_of_dofs = compute_num_dofs_from_members(&self.member_sets);

        // Eliminate slave DOFs and zero-energy DOFs (except masters)
        let mut eliminated: HashSet<usize> = HashSet::new();
        for info in &rigid_elems {
            for d in 0..6 {
                eliminated.insert(dof_index(info.b, d));
            }
        }

        let zero_energy = detect_zero_energy_dofs(self);
        let master_nodes: HashSet<u32> = rigid_elems.iter().map(|ri| ri.a).collect();
        for idx in zero_energy {
            let node_id: u32 = (idx / 6) as u32 + 1;
            if !master_nodes.contains(&node_id) {
                eliminated.insert(idx);
            }
        }

        // Map FULL→RED
        let mut full_to_red: HashMap<usize, usize> = HashMap::new();
        let mut red_to_full: Vec<usize> = Vec::new();
        let mut seen: HashSet<usize> = HashSet::new();
        for set in &self.member_sets {
            for member in &set.members {
                for node in [&member.start_node, &member.end_node] {
                    for d in 0..6 {
                        let fi = dof_index(node.id, d);
                        if !eliminated.contains(&fi) && seen.insert(fi) {
                            full_to_red.insert(fi, red_to_full.len());
                            red_to_full.push(fi);
                        }
                    }
                }
            }
        }

        let n_red = red_to_full.len();
        let mut s = DMatrix::<f64>::zeros(number_of_dofs, n_red);

        // Identity for retained DOFs
        for (fi, &col) in &full_to_red {
            s[(*fi, col)] = 1.0;
        }

        // Slave rows: [u_b;θ_b] = C(r)[u_a;θ_a]
        for info in &rigid_elems {
            let c = FERS::rigid_map_c(info.r.0, info.r.1, info.r.2);
            for i in 0..6 {
                let row_b = dof_index(info.b, i);
                for j in 0..6 {
                    let row_a_j = dof_index(info.a, j);
                    let coeff = c[(i, j)];
                    if coeff == 0.0 {
                        continue;
                    }
                    for col in 0..n_red {
                        s[(row_b, col)] += coeff * s[(row_a_j, col)];
                    }
                }
            }
        }

        Ok(RigidElimination { s, full_to_red })
    }

    pub fn get_member_count(&self) -> usize {
        self.member_sets.iter().map(|ms| ms.members.len()).sum()
    }

    fn assemble_element_into_global_12(
        global: &mut nalgebra::DMatrix<f64>,
        i0: usize,
        j0: usize,
        ke: &nalgebra::DMatrix<f64>,
    ) {
        debug_assert_eq!(ke.nrows(), 12);
        debug_assert_eq!(ke.ncols(), 12);
        for i in 0..6 {
            for j in 0..6 {
                global[(i0 + i, i0 + j)] += ke[(i, j)];
                global[(i0 + i, j0 + j)] += ke[(i, j + 6)];
                global[(j0 + i, i0 + j)] += ke[(i + 6, j)];
                global[(j0 + i, j0 + j)] += ke[(i + 6, j + 6)];
            }
        }
    }

    pub fn assemble_global_stiffness_matrix(
        &self,
        active_map: &std::collections::HashMap<u32, bool>,
    ) -> Result<nalgebra::DMatrix<f64>, String> {
        use crate::models::members::enums::MemberType;

        self.validate_node_ids()?;
        let assembly_context = AssemblyContext::new(self);

        let number_of_dofs: usize = compute_num_dofs_from_members(&self.member_sets);

        let mut global_stiffness_matrix =
            nalgebra::DMatrix::<f64>::zeros(number_of_dofs, number_of_dofs);

        for member_set in &self.member_sets {
            for member in &member_set.members {
                // Build a 12x12 GLOBAL element matrix according to the member behavior
                let element_global_opt: Option<nalgebra::DMatrix<f64>> = match member.member_type {
                    MemberType::Normal => {
                        let Some(_) = member.section else {
                            return Err(format!(
                                "Member {} (Normal) is missing a section id.",
                                member.id
                            ));
                        };

                        // 1) Local base K
                        let k_local_base = member
                            .calculate_stiffness_matrix_3d(
                                &assembly_context.material_by_id,
                                &assembly_context.section_by_id,
                            )
                            .ok_or_else(|| {
                                format!("Member {} failed to build local stiffness.", member.id)
                            })?;

                        // 2) Apply end releases / semi-rigid springs and transform to GLOBAL in one place
                        let k_global = local_to_global_with_releases(
                            member,
                            &k_local_base,
                            &assembly_context.hinge_by_id,
                        )?;

                        Some(k_global)
                    }

                    MemberType::Truss => {
                        let mut k_global: nalgebra::Matrix<
                            f64,
                            nalgebra::Dyn,
                            nalgebra::Dyn,
                            nalgebra::VecStorage<f64, nalgebra::Dyn, nalgebra::Dyn>,
                        > = member
                            .calculate_truss_stiffness_matrix_3d(
                                &assembly_context.material_by_id,
                                &assembly_context.section_by_id,
                            )
                            .ok_or_else(|| {
                                format!(
                                    "Member {} (Truss) failed to build truss stiffness.",
                                    member.id
                                )
                            })?;

                        // Optional: translational node-to-ground springs from hinges (LOCAL → GLOBAL)
                        let a_h = member
                            .start_hinge
                            .and_then(|id| assembly_context.hinge_by_id.get(&id).copied());
                        let b_h = member
                            .end_hinge
                            .and_then(|id| assembly_context.hinge_by_id.get(&id).copied());
                        let (a_trans, _a_rot, b_trans, _b_rot) = modes_from_single_ends(a_h, b_h);

                        let k_s_local = build_local_truss_translational_spring_k(a_trans, b_trans);
                        if k_s_local.iter().any(|v| *v != 0.0) {
                            let t = member.calculate_transformation_matrix_3d();
                            let k_s_global = t.transpose() * k_s_local * t;
                            k_global += k_s_global;
                        }

                        Some(k_global)
                    }

                    MemberType::Tension | MemberType::Compression => {
                        let is_active: bool = *active_map.get(&member.id).unwrap_or(&true);
                        if is_active {
                            member.calculate_truss_stiffness_matrix_3d(
                                &assembly_context.material_by_id,
                                &assembly_context.section_by_id,
                            )
                        } else {
                            None
                        }
                    }
                    MemberType::Rigid => {
                        match self.settings.analysis_options.rigid_strategy {
                            RigidStrategy::LinearMpc => None,
                            RigidStrategy::RigidMember => {
                                // ------------- pick a base section id -------------
                                let pick_base_section =
                                    |m: &crate::models::members::member::Member| -> Option<u32> {
                                        // 1) explicit
                                        if let Some(id) = m.section {
                                            return Some(id);
                                        }
                                        // 2) neighbor section
                                        for ms2 in &self.member_sets {
                                            for mn in &ms2.members {
                                                if !matches!(mn.member_type, MemberType::Rigid)
                                                    && (mn.start_node.id == m.start_node.id
                                                        || mn.start_node.id == m.end_node.id
                                                        || mn.end_node.id == m.start_node.id
                                                        || mn.end_node.id == m.end_node.id)
                                                {
                                                    if let Some(sec) = mn.section {
                                                        return Some(sec);
                                                    }
                                                }
                                            }
                                        }
                                        // 3) first section in the model
                                        self.sections.first().map(|s| s.id)
                                    };

                                let base_sec_id = pick_base_section(member)
                .ok_or_else(|| format!(
                    "RigidMember needs at least one section in the model or a section on rigid member {}.",
                    member.id
                ))?;

                                // ------------- get E of that base section -------------
                                let e_member = self
                                    .sections
                                    .iter()
                                    .find(|s| s.id == base_sec_id)
                                    .and_then(|sec| {
                                        self.materials.iter().find(|mat| mat.id == sec.material)
                                    })
                                    .map(|mat| mat.e_mod)
                                    .unwrap_or(210.0e9);

                                let e_target = self.max_e_mod_in_model() * 1.0e6;
                                // guard against absurd factors
                                let factor = (e_target / e_member.max(1.0)).clamp(1.0, 1.0e8);

                                // ------------- build local K using the base section -------------
                                // We need member.section = Some(base_sec_id) for the call; do it on a clone.
                                let mut tmp: crate::models::members::member::Member =
                                    (*member).clone(); // ensure your Member derives Clone
                                tmp.section = Some(base_sec_id);

                                let k_local_base = tmp
                                    .calculate_stiffness_matrix_3d(
                                        &assembly_context.material_by_id,
                                        &assembly_context.section_by_id,
                                    )
                                    .ok_or_else(|| {
                                        format!(
                                            "Rigid member {} failed to build local K.",
                                            member.id
                                        )
                                    })?;

                                let k_local_scaled = k_local_base * factor;

                                // no geometric stiff for rigid members (keeps them “kinematic” in 2nd order)
                                let k_global = local_to_global_with_releases(
                                    &tmp, // use tmp (has the section) for releases/T
                                    &k_local_scaled,
                                    &assembly_context.hinge_by_id,
                                )?;

                                Some(k_global)
                            }
                        }
                    }
                };

                if let Some(element_global) = element_global_opt {
                    let start_index = (member.start_node.id as usize - 1) * 6;
                    let end_index = (member.end_node.id as usize - 1) * 6;

                    Self::assemble_element_into_global_12(
                        &mut global_stiffness_matrix,
                        start_index,
                        end_index,
                        &element_global,
                    );
                }
            }
        }

        Ok(global_stiffness_matrix)
    }

    fn max_e_mod_in_model(&self) -> f64 {
        let mut e_max = 0.0_f64;
        for m in &self.materials {
            if m.e_mod.is_finite() && m.e_mod > e_max {
                e_max = m.e_mod;
            }
        }
        if e_max <= 0.0 {
            210.0e9_f64
        } else {
            e_max
        }
    }

    fn assemble_geometric_stiffness_matrix_with_active(
        &self,
        displacement: &nalgebra::DMatrix<f64>,
        active_map: &std::collections::HashMap<u32, bool>,
    ) -> Result<nalgebra::DMatrix<f64>, String> {
        use crate::models::members::enums::MemberType;
        let assembly_context: AssemblyContext<'_> = AssemblyContext::new(self);
        let n = compute_num_dofs_from_members(&self.member_sets);
        let mut k_geo = nalgebra::DMatrix::<f64>::zeros(n, n);

        for member_set in &self.member_sets {
            for member in &member_set.members {
                // Skip rigid: enforced by MPC; contributes no element geometry
                if matches!(member.member_type, MemberType::Rigid) {
                    continue;
                }
                // Skip deactivated tension/compression
                if matches!(
                    member.member_type,
                    MemberType::Tension | MemberType::Compression
                ) && !*active_map.get(&member.id).unwrap_or(&true)
                {
                    continue;
                }

                let n_axial = member.calculate_axial_force_3d(
                    displacement,
                    &assembly_context.material_by_id,
                    &assembly_context.section_by_id,
                );
                let k_g_local_base = member.calculate_geometric_stiffness_matrix_3d(n_axial);

                let k_g_global = local_to_global_with_releases(
                    member,
                    &k_g_local_base,
                    &assembly_context.hinge_by_id,
                )?;

                let i0 = (member.start_node.id as usize - 1) * 6;
                let j0 = (member.end_node.id as usize - 1) * 6;
                Self::assemble_element_into_global_12(&mut k_geo, i0, j0, &k_g_global);
            }
        }
        Ok(k_geo)
    }

    pub fn validate_node_ids(&self) -> Result<(), String> {
        // Collect all node IDs in a HashSet for quick lookup
        let mut node_ids: HashSet<u32> = HashSet::new();

        // Populate node IDs from all members
        for member_set in &self.member_sets {
            for member in &member_set.members {
                node_ids.insert(member.start_node.id);
                node_ids.insert(member.end_node.id);
            }
        }

        // Ensure IDs start at 1 and are consecutive
        let max_id = *node_ids.iter().max().unwrap_or(&0);
        for id in 1..=max_id {
            if !node_ids.contains(&id) {
                return Err(format!(
                    "Node ID {} is missing. Node IDs must be consecutive starting from 1.",
                    id
                ));
            }
        }

        Ok(())
    }

    fn update_active_set(
        &self,
        displacement: &nalgebra::DMatrix<f64>,
        active_map: &mut std::collections::HashMap<u32, bool>,
        axial_slack_tolerance: f64,
        material_map: &std::collections::HashMap<u32, &Material>,
        section_map: &std::collections::HashMap<u32, &Section>,
    ) -> bool {
        use crate::models::members::enums::MemberType;

        let mut changed = false;
        for member_set in &self.member_sets {
            for member in &member_set.members {
                match member.member_type {
                    MemberType::Tension => {
                        let n = member.calculate_axial_force_3d(
                            displacement,
                            material_map,
                            section_map,
                        );
                        let should_be_active = n >= -axial_slack_tolerance;
                        if active_map.get(&member.id).copied().unwrap_or(true) != should_be_active {
                            active_map.insert(member.id, should_be_active);
                            changed = true;
                        }
                    }
                    MemberType::Compression => {
                        let n = member.calculate_axial_force_3d(
                            displacement,
                            material_map,
                            section_map,
                        );
                        let should_be_active = n <= axial_slack_tolerance;
                        if active_map.get(&member.id).copied().unwrap_or(true) != should_be_active {
                            active_map.insert(member.id, should_be_active);
                            changed = true;
                        }
                    }
                    _ => {}
                }
            }
        }
        changed
    }

    pub fn assemble_load_vector_for_combination(
        &self,
        combination_id: u32,
    ) -> Result<DMatrix<f64>, String> {
        let num_dofs = compute_num_dofs_from_members(&self.member_sets);
        let mut f_comb = DMatrix::<f64>::zeros(num_dofs, 1);

        // Find the combination by its load_combination_id field
        let combo = self
            .load_combinations
            .iter()
            .find(|lc| lc.load_combination_id == combination_id)
            .ok_or_else(|| format!("LoadCombination {} not found.", combination_id))?;

        // Now iterate the HashMap<u32, f64>
        for (&case_id, &factor) in &combo.load_cases_factors {
            let f_case = self.assemble_load_vector_for_case(case_id);
            f_comb += f_case * factor;
        }

        Ok(f_comb)
    }

    fn rigid_map_c(r_x: f64, r_y: f64, r_z: f64) -> nalgebra::SMatrix<f64, 6, 6> {
        use nalgebra::{Matrix3, SMatrix};

        let i3 = Matrix3::<f64>::identity();
        let skew = Matrix3::<f64>::new(0.0, -r_z, r_y, r_z, 0.0, -r_x, -r_y, r_x, 0.0);

        // [u_b; θ_b] = [I  -[r]_x; 0  I] [u_a; θ_a]
        let mut c = SMatrix::<f64, 6, 6>::zeros();
        c.fixed_view_mut::<3, 3>(0, 0).copy_from(&i3);
        c.fixed_view_mut::<3, 3>(0, 3).copy_from(&(-skew));
        c.fixed_view_mut::<3, 3>(3, 3).copy_from(&i3);
        c
    }

    fn reduce_system(
        k_full: &DMatrix<f64>,
        f_full: &DMatrix<f64>,
        elim: &RigidElimination,
    ) -> (DMatrix<f64>, DMatrix<f64>) {
        let k_red = elim.s.transpose() * k_full * &elim.s;
        let f_red = elim.s.transpose() * f_full;
        (k_red, f_red)
    }

    fn expand_solution(elim: &RigidElimination, u_red: &DMatrix<f64>) -> DMatrix<f64> {
        &elim.s * u_red
    }

    fn constrain_linear_constraint_penalty(
        &self,
        k_red: &mut nalgebra::DMatrix<f64>,
        rhs_red: &mut nalgebra::DMatrix<f64>,
        a_column: &nalgebra::DMatrix<f64>, // shape (n_red, 1)
        prescribed: f64,
        penalty_factor: f64,
    ) {
        let n_red_rows: usize = k_red.nrows();
        let n_red_cols: usize = k_red.ncols();
        debug_assert_eq!(n_red_rows, n_red_cols, "Reduced stiffness must be square.");
        debug_assert_eq!(
            a_column.nrows(),
            n_red_rows,
            "Constraint vector length must match reduced system size."
        );
        debug_assert_eq!(a_column.ncols(), 1, "Constraint vector must be a column.");

        // Scale penalty from the matrix magnitude to mitigate conditioning issues.
        let mut max_diag: f64 = 0.0;
        for i in 0..n_red_rows {
            let value: f64 = k_red[(i, i)].abs();
            if value > max_diag {
                max_diag = value;
            }
        }
        if max_diag <= 0.0 {
            max_diag = 1.0;
        }
        let alpha: f64 = penalty_factor * max_diag;

        // K += alpha * a * a^T
        for i in 0..n_red_rows {
            let ai: f64 = a_column[(i, 0)];
            if ai == 0.0 {
                continue;
            }
            for j in 0..n_red_rows {
                let aj: f64 = a_column[(j, 0)];
                if aj == 0.0 {
                    continue;
                }
                k_red[(i, j)] += alpha * ai * aj;
            }
        }

        // rhs += alpha * a * prescribed
        if prescribed != 0.0 {
            for i in 0..n_red_rows {
                rhs_red[(i, 0)] += alpha * a_column[(i, 0)] * prescribed;
            }
        }
    }

    /// Try to detect whether a constraint vector is essentially "one-hot" on a single reduced DOF.
    /// Returns Some(pivot_index) if exactly or approximately one-hot, otherwise None.
    fn detect_one_hot_constraint(
        &self,
        a_column: &nalgebra::DMatrix<f64>,
        tolerance_ratio: f64,
    ) -> Option<usize> {
        debug_assert_eq!(a_column.ncols(), 1, "Constraint vector must be a column.");
        let n: usize = a_column.nrows();

        // Find the entry with the largest absolute value
        let mut max_val: f64 = 0.0;
        let mut max_idx: usize = 0;
        for i in 0..n {
            let v: f64 = a_column[(i, 0)].abs();
            if v > max_val {
                max_val = v;
                max_idx = i;
            }
        }
        if max_val == 0.0 {
            return None;
        }

        // Sum of squares of all other coefficients
        let mut sum_sq_other: f64 = 0.0;
        for i in 0..n {
            if i == max_idx {
                continue;
            }
            let v: f64 = a_column[(i, 0)];
            sum_sq_other += v * v;
        }

        // If the energy of others is small relative to the pivot, treat it as one-hot
        if sum_sq_other <= (tolerance_ratio * tolerance_ratio) * (max_val * max_val) {
            Some(max_idx)
        } else {
            None
        }
    }

    fn apply_boundary_conditions_reduced(
        &self,
        elim: &RigidElimination,
        k_red: &mut nalgebra::DMatrix<f64>,
        rhs_red: &mut nalgebra::DMatrix<f64>,
    ) -> Result<(), String> {
        let support_map: HashMap<u32, &NodalSupport> =
            self.nodal_supports.iter().map(|s| (s.id, s)).collect();

        // Tunables: penalty factor and one-hot tolerance
        const BC_PENALTY_FACTOR: f64 = 1.0e8; // increase if constraints look too soft; decrease if conditioning suffers
        const ONE_HOT_TOL_RATIO: f64 = 1.0e-6; // if all other coefficients are <= 1e-6 of the pivot, treat as one-hot

        let n_red: usize = k_red.nrows();
        debug_assert_eq!(n_red, k_red.ncols(), "Reduced stiffness must be square.");
        debug_assert_eq!(
            rhs_red.nrows(),
            n_red,
            "RHS size must match reduced system size."
        );
        debug_assert_eq!(rhs_red.ncols(), 1, "RHS must be a column vector.");

        for ms in &self.member_sets {
            for m in &ms.members {
                for node in [&m.start_node, &m.end_node] {
                    let Some(support_id) = node.nodal_support else {
                        continue;
                    };
                    let Some(support) = support_map.get(&support_id) else {
                        continue;
                    };

                    let base_full = (node.id as usize - 1) * 6;

                    // Handle translational constraints
                    for (axis_label, local_dof) in TRANSLATION_AXES {
                        let cond_opt =
                            support.displacement_conditions.get(axis_label).or_else(|| {
                                support
                                    .displacement_conditions
                                    .get(&axis_label.to_ascii_lowercase())
                            });
                        let is_fixed: bool = cond_opt
                            .map(|c| matches!(c.condition_type, SupportConditionType::Fixed))
                            .unwrap_or(true);
                        if !is_fixed {
                            continue;
                        }

                        let fi: usize = base_full + local_dof;
                        if let Some(ri) = elim.full_to_red.get(&fi).copied() {
                            // Retained DOF: constrain exactly
                            constrain_single_dof(k_red, rhs_red, ri, 0.0);
                        } else {
                            // Slave DOF: enforce (S_row * u_red) = 0
                            let mut a_column = nalgebra::DMatrix::<f64>::zeros(n_red, 1);
                            for j in 0..n_red {
                                a_column[(j, 0)] = elim.s[(fi, j)];
                            }

                            // If the constraint is essentially one-hot, constrain that single DOF exactly.
                            if let Some(pivot_j) =
                                self.detect_one_hot_constraint(&a_column, ONE_HOT_TOL_RATIO)
                            {
                                constrain_single_dof(k_red, rhs_red, pivot_j, 0.0);
                            } else {
                                self.constrain_linear_constraint_penalty(
                                    k_red,
                                    rhs_red,
                                    &a_column,
                                    0.0, // prescribed displacement is zero
                                    BC_PENALTY_FACTOR,
                                );
                            }
                        }
                    }

                    // Handle rotational constraints
                    for (axis_label, local_dof) in ROTATION_AXES {
                        let cond_opt = support.rotation_conditions.get(axis_label).or_else(|| {
                            support
                                .rotation_conditions
                                .get(&axis_label.to_ascii_lowercase())
                        });
                        let is_fixed: bool = cond_opt
                            .map(|c| matches!(c.condition_type, SupportConditionType::Fixed))
                            .unwrap_or(true);
                        if !is_fixed {
                            continue;
                        }

                        let fi: usize = base_full + local_dof;
                        if let Some(ri) = elim.full_to_red.get(&fi).copied() {
                            // Retained rotational DOF: constrain exactly
                            constrain_single_dof(k_red, rhs_red, ri, 0.0);
                        } else {
                            // Slave rotational DOF: enforce (S_row * u_red) = 0
                            let mut a_column = nalgebra::DMatrix::<f64>::zeros(n_red, 1);
                            for j in 0..n_red {
                                a_column[(j, 0)] = elim.s[(fi, j)];
                            }

                            if let Some(pivot_j) =
                                self.detect_one_hot_constraint(&a_column, ONE_HOT_TOL_RATIO)
                            {
                                constrain_single_dof(k_red, rhs_red, pivot_j, 0.0);
                            } else {
                                self.constrain_linear_constraint_penalty(
                                    k_red,
                                    rhs_red,
                                    &a_column,
                                    0.0,
                                    BC_PENALTY_FACTOR,
                                );
                            }
                        }
                    }
                }
            }
        }

        Ok(())
    }

    pub fn assemble_load_vector_for_case(&self, load_case_id: u32) -> DMatrix<f64> {
        let num_dofs = compute_num_dofs_from_members(&self.member_sets);
        let mut f = DMatrix::<f64>::zeros(num_dofs, 1);

        if let Some(load_case) = self.load_cases.iter().find(|lc| lc.id == load_case_id) {
            assemble_nodal_loads(load_case, &mut f);
            assemble_nodal_moments(load_case, &mut f);
            assemble_distributed_loads(load_case, &self.member_sets, &mut f, load_case_id);
        }
        f
    }

    fn init_active_map_tie_comp(&self) -> HashMap<u32, bool> {
        let mut map = HashMap::new();
        for ms in &self.member_sets {
            for member in &ms.members {
                if matches!(
                    member.member_type,
                    MemberType::Tension | MemberType::Compression
                ) {
                    map.insert(member.id, true);
                }
            }
        }
        map
    }

    fn solve_first_order_common(
        &mut self,
        load_vector_full: nalgebra::DMatrix<f64>,
        name: String,
        result_type: ResultType,
    ) -> Result<Results, String> {
        let tolerance: f64 = self.settings.analysis_options.tolerance;
        let max_it: usize = self.settings.analysis_options.max_iterations.unwrap_or(20) as usize;
        let axial_slack_tolerance: f64 = AXIAL_SLACK_TOLERANCE_DEFAULT;

        let mut active_map = self.init_active_map_tie_comp();
        let mut u_full =
            nalgebra::DMatrix::<f64>::zeros(compute_num_dofs_from_members(&self.member_sets), 1);

        let assembly_context: AssemblyContext<'_> = AssemblyContext::new(self);

        // Build rigid elimination (S) once; it depends only on topology/hinges
        let elim = self.build_rigid_elimination_partial_using_hinges()?;

        let mut converged = false;
        for _iter in 0..max_it {
            // Linear operator (no geometric stiffness) for first-order analysis
            let k_full = self.build_operator_with_supports(&active_map, None)?;

            // Reduce system: K_r = Sᵀ K S,  f_r = Sᵀ f
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, &load_vector_full, &elim);

            // Apply boundary conditions in REDUCED space
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;

            // Solve reduced system
            let u_red = k_red.lu().solve(&f_red).ok_or_else(|| {
                "Reduced stiffness matrix is singular or near-singular".to_string()
            })?;

            // Expand to FULL space
            let u_full_new = Self::expand_solution(&elim, &u_red);

            // Active-set update (Tension/Compression) uses FULL displacement
            let delta = &u_full_new - &u_full;
            u_full = u_full_new;

            let changed = self.update_active_set(
                &u_full,
                &mut active_map,
                axial_slack_tolerance,
                &assembly_context.material_by_id,
                &assembly_context.section_by_id,
            );

            if delta.norm() < tolerance && !changed {
                converged = true;
                break;
            }
        }

        if !converged {
            return Err(format!(
                "Active-set iteration did not converge within {} iterations",
                max_it
            ));
        }

        // ---------------------------
        // Build reactions including MPCs
        // ---------------------------
        // Recompute the FINAL linear operator with the final active_map,
        // then form the reduced residual r_r = K_r u_r - f_r with the UNMODIFIED K_r, f_r
        // Map to FULL space: r_full = S r_red
        // Keep only true support reactions
        let r_support = compose_support_reaction_vector_equilibrium(
            self,
            &result_type,      // <- pass the ResultType you're solving
            &u_full,           // <- final full displacement vector
            Some(&active_map), // <- so ties/struts respect active set
        )?;

        // Store masked reactions
        let mut sum_rx = 0.0;
        let mut sum_ry = 0.0;
        let mut sum_rz = 0.0;
        for (i, val) in r_support.iter().enumerate() {
            match i % 6 {
                0 => sum_rx += val,
                1 => sum_ry += val,
                2 => sum_rz += val,
                _ => {}
            }
        }

        // Sum of EXTERNAL loads per axis (global vector you assembled)
        let mut sum_fx = 0.0;
        let mut sum_fy = 0.0;
        let mut sum_fz = 0.0;
        for (i, val) in load_vector_full.iter().enumerate() {
            match i % 6 {
                0 => sum_fx += val,
                1 => sum_fy += val,
                2 => sum_fz += val,
                _ => {}
            }
        }

        log::debug!(
            "Equil check: sum reactions [Fx,Fy,Fz] = [{:.6}, {:.6}, {:.6}]",
            sum_rx,
            sum_ry,
            sum_rz
        );
        log::debug!(
            "Equil check: sum external [Fx,Fy,Fz]  = [{:.6}, {:.6}, {:.6}]",
            sum_fx,
            sum_fy,
            sum_fz
        );

        // Store masked reactions
        let results = self
            .build_and_store_results(
                name.clone(),
                result_type.clone(),
                &u_full,
                &r_support,
                Some(&active_map),
            )?
            .clone();

        Ok(results)
    }

    fn solve_second_order_common(
        &mut self,
        load_vector_full: nalgebra::DMatrix<f64>,
        name: String,
        result_type: ResultType,
        max_iterations: usize,
        tolerance: f64,
    ) -> Result<Results, String> {
        let axial_slack_tolerance: f64 = AXIAL_SLACK_TOLERANCE_DEFAULT;

        let mut active_map = self.init_active_map_tie_comp();
        let n_full = compute_num_dofs_from_members(&self.member_sets);
        let mut u_full = nalgebra::DMatrix::<f64>::zeros(n_full, 1);

        let assembly_context: AssemblyContext<'_> = AssemblyContext::new(self);

        // Build rigid elimination (S) once; it depends only on topology/hinges
        let elim = self.build_rigid_elimination_partial_using_hinges()?;

        let mut converged = false;
        for _iter in 0..max_iterations {
            // Tangent operator (includes geometric stiffness) for Newton–Raphson
            let k_tangent_full = self.build_operator_with_supports(&active_map, Some(&u_full))?;

            // Reduce: K_tr = Sᵀ K_tangent S, f_r = Sᵀ f
            let (k_red_tangent, f_red) =
                Self::reduce_system(&k_tangent_full, &load_vector_full, &elim);

            // Current reduced displacement u_r = Sᵀ u
            let mut u_red = elim.s.transpose() * &u_full;

            // Residual in reduced space (before BC application): r_r = K_tr u_r − f_r
            let mut r_red = &k_red_tangent * &u_red - &f_red;

            // Apply BCs in REDUCED space, then solve for Δu_r from K_tr,BC Δu_r = −r_r,BC
            let mut k_treated = k_red_tangent.clone();
            self.apply_boundary_conditions_reduced(&elim, &mut k_treated, &mut r_red)?;
            let delta_red = k_treated
                .lu()
                .solve(&(-&r_red))
                .ok_or_else(|| "Tangent stiffness singular.".to_string())?;

            // Update reduced, expand to FULL
            u_red += &delta_red;
            let u_full_new = Self::expand_solution(&elim, &u_red);

            // Check convergence and update active set
            let delta_full = &u_full_new - &u_full;
            u_full = u_full_new;

            let changed = self.update_active_set(
                &u_full,
                &mut active_map,
                axial_slack_tolerance,
                &assembly_context.material_by_id,
                &assembly_context.section_by_id,
            );

            if delta_full.norm() < tolerance && !changed {
                converged = true;
                break;
            }
        }

        if !converged {
            return Err(format!(
                "Newton–Raphson with active set did not converge in {} iterations",
                max_iterations
            ));
        }

        // ---------------------------
        // Build reactions including MPCs
        // ---------------------------
        // Use the LINEAR operator (no geometric stiffness) to compute final reactions,
        // matching classic practice and your previous intent/comments.
        // Map to FULL space reactions
        let r_support = compose_support_reaction_vector_equilibrium(
            self,
            &result_type,      // <- pass the ResultType you're solving
            &u_full,           // <- final full displacement vector
            Some(&active_map), // <- so ties/struts respect active set
        )?;

        let results = self
            .build_and_store_results(
                name.clone(),
                result_type.clone(),
                &u_full,
                &r_support,
                Some(&active_map),
            )?
            .clone();
        Ok(results)
    }

    pub fn solve_for_load_case(&mut self, load_case_id: u32) -> Result<Results, String> {
        let load_vector = self.assemble_load_vector_for_case(load_case_id);
        let load_case = self
            .load_cases
            .iter()
            .find(|lc| lc.id == load_case_id)
            .ok_or_else(|| format!("LoadCase {} not found.", load_case_id))?;
        self.solve_first_order_common(
            load_vector,
            load_case.name.clone(),
            ResultType::Loadcase(load_case_id),
        )
    }
    pub fn solve_for_load_case_second_order(
        &mut self,
        load_case_id: u32,
        max_iterations: usize,
        tolerance: f64,
    ) -> Result<Results, String> {
        let load_vector = self.assemble_load_vector_for_case(load_case_id);
        let load_case = self
            .load_cases
            .iter()
            .find(|lc| lc.id == load_case_id)
            .ok_or_else(|| format!("LoadCase {} not found.", load_case_id))?;
        self.solve_second_order_common(
            load_vector,
            load_case.name.clone(),
            ResultType::Loadcase(load_case_id),
            max_iterations,
            tolerance,
        )
    }
    pub fn solve_for_load_combination(&mut self, combination_id: u32) -> Result<Results, String> {
        let load_vector = self.assemble_load_vector_for_combination(combination_id)?;
        let combo = self
            .load_combinations
            .iter()
            .find(|lc| lc.load_combination_id == combination_id)
            .ok_or_else(|| format!("LoadCombination {} not found.", combination_id))?;
        self.solve_first_order_common(
            load_vector,
            combo.name.clone(),
            ResultType::Loadcombination(combination_id),
        )
    }
    pub fn solve_for_load_combination_second_order(
        &mut self,
        combination_id: u32,
        max_iterations: usize,
        tolerance: f64,
    ) -> Result<Results, String> {
        let load_vector = self.assemble_load_vector_for_combination(combination_id)?;
        let combo = self
            .load_combinations
            .iter()
            .find(|lc| lc.load_combination_id == combination_id)
            .ok_or_else(|| format!("LoadCombination {} not found.", combination_id))?;
        self.solve_second_order_common(
            load_vector,
            combo.name.clone(),
            ResultType::Loadcombination(combination_id),
            max_iterations,
            tolerance,
        )
    }

    pub fn build_and_store_results(
        &mut self,
        name: String,
        result_type: ResultType,
        displacement_vector: &DMatrix<f64>,
        global_reaction_vector: &DMatrix<f64>,
        active_map: Option<&std::collections::HashMap<u32, bool>>,
    ) -> Result<&Results, String> {
        // 1) Element/member results
        let member_results = compute_member_results_from_displacement(
            self,
            &result_type,
            displacement_vector,
            active_map,
        );

        // 2) Node displacements
        let displacement_nodes = extract_displacements(self, displacement_vector);

        // 3) Reactions: already computed via compose_support_reaction_vector_equilibrium(...)
        let reaction_nodes: BTreeMap<u32, crate::models::results::reaction::ReactionNodeResult> =
            extract_reaction_nodes(self, global_reaction_vector);

        // 4) Pack results & store
        let total_members: usize = self.member_sets.iter().map(|set| set.members.len()).sum();
        let total_supports: usize = self.nodal_supports.len();

        let results = Results {
            name: name.clone(),
            result_type: result_type.clone(),
            displacement_nodes,
            reaction_nodes,
            member_results,
            summary: ResultsSummary {
                total_displacements: total_members,
                total_reaction_forces: total_supports,
                total_member_forces: total_members,
            },
            unity_checks: None,
        };

        let bundle = self.results.get_or_insert_with(|| ResultsBundle {
            loadcases: BTreeMap::new(),
            loadcombinations: BTreeMap::new(),
            unity_checks_overview: None,
        });

        match result_type {
            ResultType::Loadcase(_) => {
                if bundle.loadcases.insert(name.clone(), results).is_some() {
                    return Err(format!("Duplicate load case name `{}`", name));
                }
                Ok(bundle.loadcases.get(&name).unwrap())
            }
            ResultType::Loadcombination(_) => {
                if bundle
                    .loadcombinations
                    .insert(name.clone(), results)
                    .is_some()
                {
                    return Err(format!("Duplicate load combination name `{}`", name));
                }
                Ok(bundle.loadcombinations.get(&name).unwrap())
            }
        }
    }

    pub fn save_results_to_json(fers_data: &FERS, file_path: &str) -> Result<(), std::io::Error> {
        let json = serde_json::to_string_pretty(fers_data)?;
        std::fs::write(file_path, json)
    }
}
