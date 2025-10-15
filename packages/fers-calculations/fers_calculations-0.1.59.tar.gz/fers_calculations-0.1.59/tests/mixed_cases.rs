#[path = "test_support/mod.rs"]
mod test_support;

use fers_calculations::models::members::memberhinge::MemberHinge;
use fers_calculations::models::settings::analysissettings::RigidStrategy;
use fers_calculations::models::supports::supportconditiontype::SupportConditionType;
use test_support::formulas::*;
use test_support::helpers::*;
use test_support::*;

// ===================== 041 =====================

fn test_041_rigid_member_end_load_impl(strategy: RigidStrategy) {
    let mut model = make_fers_with_strategy(strategy);

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    // Fixed at node 1
    model.nodal_supports.push(make_fixed_support(1));

    let length_elastic = 5.0_f64;
    let length_rigid = 5.0_f64;
    let force_newton = 1000.0_f64;
    let r_x = length_rigid;

    let n1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let n2 = make_node(2, length_elastic, 0.0, 0.0, None);
    let n3 = make_node(3, length_elastic + length_rigid, 0.0, 0.0, None);

    let m_el = make_beam_member(1, &n1, &n2, sec_id);
    let m_rg = make_rigid_member(2, &n2, &n3);
    add_member_set(&mut model, 1, vec![m_el, m_rg]);

    let lc_id = add_load_case(&mut model, 1, "End Load");
    add_nodal_load(&mut model, 1, lc_id, 2, force_newton, (0.0, -1.0, 0.0));

    model.solve_for_load_case(lc_id).expect("Analysis failed");

    let res = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("End Load")
        .unwrap();

    let dy_2 = res.displacement_nodes.get(&2).unwrap().dy;
    let dy_3 = res.displacement_nodes.get(&3).unwrap().dy;
    let rz_2 = res.displacement_nodes.get(&2).unwrap().rz;
    let rz_3 = res.displacement_nodes.get(&3).unwrap().rz;
    let mz_1 = res.reaction_nodes.get(&1).unwrap().nodal_forces.mz;

    let steel_e = 210.0e9_f64;
    let dy_expected = cantilever_end_point_load_deflection_at_free_end(
        force_newton,
        length_elastic,
        steel_e,
        SECOND_MOMENT_STRONG_AXIS_IN_M4,
    );
    let mz_expected =
        cantilever_end_point_load_fixed_end_moment_magnitude(force_newton, length_elastic);
    let rz_expected =
        -force_newton * length_elastic.powi(2) / (2.0 * steel_e * SECOND_MOMENT_STRONG_AXIS_IN_M4);

    assert_close(dy_2, dy_expected, TOL_ABSOLUTE_DISPLACEMENT_IN_METER);
    assert_close(mz_1.abs(), mz_expected, TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER);

    assert!((rz_2 - rz_3).abs() < TOL_ABSOLUTE_ROTATION_IN_RADIAN);
    assert!((rz_2 - rz_expected).abs() < TOL_ABSOLUTE_ROTATION_IN_RADIAN);

    assert_close(dy_3, dy_2 + rz_2 * r_x, TOL_ABSOLUTE_DISPLACEMENT_IN_METER);
}

#[test]
fn test_041_rigid_member_end_load_rigid_member() {
    test_041_rigid_member_end_load_impl(RigidStrategy::RigidMember);
}

#[test]
fn test_041_rigid_member_end_load_mpc_linear() {
    test_041_rigid_member_end_load_impl(RigidStrategy::LinearMpc);
}

// ===================== 042 =====================

fn test_042_rigid_member_reversed_end_load_impl(strategy: RigidStrategy) {
    // ---------------- Model setup ----------------
    let mut model = make_fers_with_strategy(strategy);

    // Material and section
    let material_id = add_material_s235(&mut model, 1);
    let section_id =
        add_section_ipe180_like(&mut model, 1, material_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    // Fixed support at node 1
    model.nodal_supports.push(make_fixed_support(1));

    // Geometry
    let length_elastic = 5.0_f64;
    let length_rigid = 5.0_f64;
    let total_length = length_elastic + length_rigid;

    let node1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let node2 = make_node(2, length_elastic, 0.0, 0.0, None);
    let node3 = make_node(3, total_length, 0.0, 0.0, None);

    // Members:
    // - Elastic beam: node1 -> node2
    // - Rigid link reversed: node3 -> node2
    let beam_member = make_beam_member(1, &node1, &node2, section_id);
    let rigid_member_reversed = make_rigid_member(2, &node3, &node2);
    add_member_set(&mut model, 1, vec![beam_member, rigid_member_reversed]);

    // Load case: 1 kN downward at node 2
    let load_case_id = add_load_case(&mut model, 1, "End Load");
    let force_newton = 1000.0_f64;
    add_nodal_load(
        &mut model,
        1,
        load_case_id,
        2,
        force_newton,
        (0.0, -1.0, 0.0),
    );

    // ---------------- Solve ----------------
    model
        .solve_for_load_case(load_case_id)
        .expect("Analysis failed");

    let results = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("End Load")
        .unwrap();

    // Displacements, rotations, and reactions
    let dy_2 = results.displacement_nodes.get(&2).unwrap().dy;
    let dy_3 = results.displacement_nodes.get(&3).unwrap().dy;
    let rz_2 = results.displacement_nodes.get(&2).unwrap().rz;
    let rz_3 = results.displacement_nodes.get(&3).unwrap().rz;
    let mz_1 = results.reaction_nodes.get(&1).unwrap().nodal_forces.mz;

    // ---------------- References (analytical) ----------------
    let e_modulus = 210.0e9_f64;
    let i_zz = SECOND_MOMENT_STRONG_AXIS_IN_M4;

    let dy_expected = cantilever_end_point_load_deflection_at_free_end(
        force_newton,
        length_elastic,
        e_modulus,
        i_zz,
    );
    let mz_expected =
        cantilever_end_point_load_fixed_end_moment_magnitude(force_newton, length_elastic);
    let rz_expected = -force_newton * length_elastic.powi(2) / (2.0 * e_modulus * i_zz);

    let dy_end_from_mid = dy_2 + length_rigid * rz_2;

    // ---------------- Assertions ----------------
    assert_close(dy_2, dy_expected, TOL_ABSOLUTE_DISPLACEMENT_IN_METER);
    assert_close(mz_1.abs(), mz_expected, TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER);
    assert!((rz_2 - rz_3).abs() < TOL_ABSOLUTE_ROTATION_IN_RADIAN);
    assert!((rz_2 - rz_expected).abs() < TOL_ABSOLUTE_ROTATION_IN_RADIAN);
    assert_close(dy_3, dy_end_from_mid, TOL_ABSOLUTE_DISPLACEMENT_IN_METER);
}

#[test]
fn test_042_rigid_member_reversed_end_load_rigid_member() {
    test_042_rigid_member_reversed_end_load_impl(RigidStrategy::RigidMember);
}

#[test]
fn test_042_rigid_member_reversed_end_load_mpc_linear() {
    test_042_rigid_member_reversed_end_load_impl(RigidStrategy::LinearMpc);
}

// ===================== 051 =====================

/// Cantilever with a root rotational spring via a MemberHinge at the start of the elastic member,
/// preceded by a rigid link: node1 --[RIGID]--> node2 --[NORMAL + spring at start]--> node3.
fn test_051_member_hinge_root_rotational_spring_impl(strategy: RigidStrategy) {
    // ---------------- Model setup (first order) ----------------
    let mut model = make_fers_with_strategy(strategy);

    let material_id = add_material_s235(&mut model, 1);
    let section_id =
        add_section_ipe180_like(&mut model, 1, material_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    // Fixed support at node 1
    model.nodal_supports.push(make_fixed_support(1));

    // Geometry
    let length_rigid = 2.5_f64; // node1 -> node2 (rigid)
    let length_elastic = 2.5_f64; // node2 -> node3 (elastic)
    let total_length = length_rigid + length_elastic;

    let node1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let node2 = make_node(2, length_rigid, 0.0, 0.0, None);
    let node3 = make_node(3, total_length, 0.0, 0.0, None);

    // Members
    let rigid_member = make_rigid_member(1, &node1, &node2);
    let mut elastic_member = make_beam_member(2, &node2, &node3, section_id);

    // Hinge: rotational spring about local Z at the START of the elastic member
    let force_newton = 1000.0_f64;
    let target_root_rotation_rad = 0.1_f64;
    let k_phi_z = (force_newton * length_elastic) / target_root_rotation_rad;

    let hinge_id = 1_u32;
    let hinge = MemberHinge {
        id: hinge_id,
        hinge_type: "SPRING_Z".to_string(),
        translational_release_vx: None,
        translational_release_vy: None,
        translational_release_vz: None,
        rotational_release_mx: None,
        rotational_release_my: None,
        rotational_release_mz: Some(k_phi_z),
        max_tension_vx: None,
        max_tension_vy: None,
        max_tension_vz: None,
        max_moment_mx: None,
        max_moment_my: None,
        max_moment_mz: None,
    };

    if model.memberhinges.is_none() {
        model.memberhinges = Some(Vec::new());
    }
    model.memberhinges.as_mut().unwrap().push(hinge);
    elastic_member.start_hinge = Some(hinge_id);

    add_member_set(&mut model, 1, vec![rigid_member, elastic_member]);

    // Load case: 1 kN downward at the free end (node 3)
    let load_case_id = add_load_case(&mut model, 1, "End Load");
    add_nodal_load(
        &mut model,
        1,
        load_case_id,
        3,
        force_newton,
        (0.0, -1.0, 0.0),
    );

    // ---------------- Solve (first order) ----------------
    model
        .solve_for_load_case(load_case_id)
        .expect("First-order analysis failed");

    let results = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("End Load")
        .unwrap();

    let dy_3 = results.displacement_nodes.get(&3).unwrap().dy;
    let rz_3 = results.displacement_nodes.get(&3).unwrap().rz;
    let mz_1 = results.reaction_nodes.get(&1).unwrap().nodal_forces.mz;

    // ---------------- References (elastic span + spring) ----------------
    let e_modulus = 210.0e9_f64;
    let i_zz = SECOND_MOMENT_STRONG_AXIS_IN_M4;

    let phi_root_expected = (force_newton * length_elastic) / k_phi_z;
    let phi_tip_expected =
        -((force_newton * length_elastic.powi(2)) / (2.0 * e_modulus * i_zz) + phi_root_expected);
    let deflection_tip_expected = -((force_newton * length_elastic.powi(3))
        / (3.0 * e_modulus * i_zz)
        + phi_root_expected * length_elastic);
    let reaction_mz_expected = force_newton * (length_elastic + length_rigid);
    let fy_1 = results.reaction_nodes.get(&1).unwrap().nodal_forces.fy;

    // ---------------- Assertions (first order) ----------------
    assert_close(
        dy_3,
        deflection_tip_expected,
        TOL_ABSOLUTE_DISPLACEMENT_IN_METER,
    );
    assert_close(fy_1, force_newton, TOL_ABSOLUTE_FORCE_IN_NEWTON);

    assert_close(rz_3, phi_tip_expected, TOL_ABSOLUTE_ROTATION_IN_RADIAN);
    assert_close(
        mz_1.abs(),
        reaction_mz_expected,
        TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER,
    );

    assert_close(rz_3, phi_tip_expected, TOL_ABSOLUTE_ROTATION_IN_RADIAN);
    assert_close(
        dy_3,
        deflection_tip_expected,
        TOL_ABSOLUTE_DISPLACEMENT_IN_METER,
    );

    assert_close(fy_1, force_newton, TOL_ABSOLUTE_FORCE_IN_NEWTON);
    assert_close(
        mz_1.abs(),
        reaction_mz_expected,
        TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER,
    );

    // ---------------- Second-order sanity (no singular tangent) ----------------
    let mut model_so = make_fers_with_strategy(strategy);

    let material_id_so = add_material_s235(&mut model_so, 1);
    let section_id_so = add_section_ipe180_like(
        &mut model_so,
        1,
        material_id_so,
        SECOND_MOMENT_STRONG_AXIS_IN_M4,
    );

    model_so.nodal_supports.push(make_fixed_support(1));

    let node1_so = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let node2_so = make_node(2, length_rigid, 0.0, 0.0, None);
    let node3_so = make_node(3, total_length, 0.0, 0.0, None);

    let rigid_member_so = make_rigid_member(1, &node1_so, &node2_so);
    let mut elastic_member_so = make_beam_member(2, &node2_so, &node3_so, section_id_so);

    let hinge_so = MemberHinge {
        id: hinge_id,
        hinge_type: "SPRING_Z".to_string(),
        translational_release_vx: None,
        translational_release_vy: None,
        translational_release_vz: None,
        rotational_release_mx: None,
        rotational_release_my: None,
        rotational_release_mz: Some(k_phi_z),
        max_tension_vx: None,
        max_tension_vy: None,
        max_tension_vz: None,
        max_moment_mx: None,
        max_moment_my: None,
        max_moment_mz: None,
    };

    model_so.memberhinges = Some(vec![hinge_so]);
    elastic_member_so.start_hinge = Some(hinge_id);

    add_member_set(&mut model_so, 1, vec![rigid_member_so, elastic_member_so]);

    let load_case_id_so = add_load_case(&mut model_so, 1, "End Load SO");
    add_nodal_load(
        &mut model_so,
        1,
        load_case_id_so,
        3,
        force_newton,
        (0.0, -1.0, 0.0),
    );

    model_so
        .solve_for_load_case_second_order(load_case_id_so, 30, 1.0e-10)
        .expect("Second-order analysis failed");

    let results_so = model_so
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("End Load SO")
        .unwrap();

    let dy_3_so = results_so.displacement_nodes.get(&3).unwrap().dy;
    let rz_3_so = results_so.displacement_nodes.get(&3).unwrap().rz;

    assert!(
        (dy_3_so - dy_3).abs() < 10.0 * TOL_ABSOLUTE_DISPLACEMENT_IN_METER,
        "Second-order dy differs more than expected"
    );
    assert!(
        (rz_3_so - rz_3).abs() < 10.0 * TOL_ABSOLUTE_ROTATION_IN_RADIAN,
        "Second-order rz differs more than expected"
    );
}

#[test]
fn test_051_member_hinge_root_rotational_spring_rigid_member() {
    test_051_member_hinge_root_rotational_spring_impl(RigidStrategy::RigidMember);
}

#[test]
fn test_051_member_hinge_root_rotational_spring_mpc_linear() {
    test_051_member_hinge_root_rotational_spring_impl(RigidStrategy::LinearMpc);
}

// ===================== 061 =====================

fn test_061_two_colinear_tension_only_members_with_mid_load_impl(strategy: RigidStrategy) {
    let mut model = make_fers_with_strategy(strategy);

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    // Node 1 fixed, Node 3 fixed, Node 2: X free, Y fixed, Z fixed; rotations all fixed for safety.
    model.nodal_supports.push(make_fixed_support(1));
    model.nodal_supports.push(make_support_custom(
        2,
        SupportConditionType::Free,  // Ux
        SupportConditionType::Fixed, // Uy
        SupportConditionType::Fixed, // Uz
        SupportConditionType::Fixed, // Rx
        SupportConditionType::Fixed, // Ry
        SupportConditionType::Fixed, // Rz
    ));
    model.nodal_supports.push(make_fixed_support(3));

    let member_length = 2.5_f64;
    let n1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let n2 = make_node(2, member_length, 0.0, 0.0, Some(2));
    let n3 = make_node(3, 2.0 * member_length, 0.0, 0.0, Some(3));

    let m_left = make_tension_only_member(1, &n1, &n2, sec_id);
    let m_right = make_tension_only_member(2, &n2, &n3, sec_id);
    add_member_set(&mut model, 1, vec![m_left, m_right]);

    let lc_id = add_load_case(&mut model, 1, "Mid Load");
    add_nodal_load(&mut model, 1, lc_id, 2, 1.0_f64, (1.0, 0.0, 0.0));

    model.solve_for_load_case(lc_id).expect("Analysis failed");

    let res = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("Mid Load")
        .unwrap();

    let dx_2 = res.displacement_nodes.get(&2).unwrap().dx;
    let fx_1 = res.reaction_nodes.get(&1).unwrap().nodal_forces.fx;
    let fx_3 = res.reaction_nodes.get(&3).unwrap().nodal_forces.fx;

    let e = 210.0e9_f64;
    let area = 26.2e-4_f64;
    let expected_dx_2 = 1.0_f64 * member_length / (area * e);

    assert_close(dx_2, expected_dx_2, TOL_ABSOLUTE_DISPLACEMENT_IN_METER);
    assert!((fx_1 - (-1.0_f64)).abs() < TOL_ABSOLUTE_FORCE_IN_NEWTON);
    assert!(fx_3.abs() < TOL_ABSOLUTE_FORCE_IN_NEWTON);
}

#[test]
fn test_061_two_colinear_tension_only_members_with_mid_load_rigid_member() {
    test_061_two_colinear_tension_only_members_with_mid_load_impl(RigidStrategy::RigidMember);
}

#[test]
fn test_061_two_colinear_tension_only_members_with_mid_load_mpc_linear() {
    test_061_two_colinear_tension_only_members_with_mid_load_impl(RigidStrategy::LinearMpc);
}

// ===================== 082 =====================

fn test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium_impl(
    strategy: RigidStrategy,
) {
    // ------------- Model setup -------------
    let mut model = make_fers_with_strategy(strategy);

    let material_id = add_material_s235(&mut model, 1);
    let section_id =
        add_section_ipe180_like(&mut model, 1, material_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    // Support 1: fully fixed
    model.nodal_supports.push(make_fixed_support(1));

    // Support 2: X free, Y free, Z fixed; rotations all free
    model.nodal_supports.push(make_support_custom(
        2,
        SupportConditionType::Free,  // Ux
        SupportConditionType::Free,  // Uy
        SupportConditionType::Fixed, // Uz
        SupportConditionType::Free,  // Rx
        SupportConditionType::Free,  // Ry
        SupportConditionType::Free,  // Rz
    ));

    // Geometry: an "L" — horizontal member (node 1 -> node 2), vertical member (node 2 -> node 3)
    let length_horizontal = 5.0_f64;
    let length_vertical = 5.0_f64;

    let node1 = make_node(1, 0.0, 0.0, 0.0, Some(1)); // fixed translations
    let node2 = make_node(2, length_horizontal, 0.0, 0.0, Some(1)); // fixed translations
    let node3 = make_node(3, length_horizontal, length_vertical, 0.0, Some(2)); // only Uz fixed

    let member_horizontal = make_beam_member(1, &node1, &node2, section_id);
    let member_vertical = make_beam_member(2, &node2, &node3, section_id);
    add_member_set(&mut model, 1, vec![member_horizontal, member_vertical]);

    // Load case: 1 kN to the left at node 3 (global X = -1)
    let load_case_id = add_load_case(&mut model, 1, "Horizontal Tip Load");
    let force_newton = 1000.0_f64;
    add_nodal_load(
        &mut model,
        1,
        load_case_id,
        3,
        force_newton,
        (-1.0, 0.0, 0.0),
    );

    // ------------- Solve -------------
    model
        .solve_for_load_case(load_case_id)
        .expect("Analysis failed");

    let results = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("Horizontal Tip Load")
        .unwrap();

    // ------------- Extract reactions -------------
    let reactions_node1 = results.reaction_nodes.get(&1).unwrap().nodal_forces;
    let reactions_node2 = results.reaction_nodes.get(&2).unwrap().nodal_forces;
    let reactions_node3 = results.reaction_nodes.get(&3).unwrap().nodal_forces;

    let reaction_fx_sum = reactions_node1.fx + reactions_node2.fx + reactions_node3.fx;
    let reaction_fy_sum = reactions_node1.fy + reactions_node2.fy + reactions_node3.fy;
    let reaction_fz_sum = reactions_node1.fz + reactions_node2.fz + reactions_node3.fz;

    // ------------- Assertions -------------
    // Global equilibrium in X: reactions must balance the applied -1000 N in X → sum Rx = +1000 N
    assert_close(reaction_fx_sum, force_newton, TOL_ABSOLUTE_FORCE_IN_NEWTON);

    // Global equilibrium in Y: there is no external Y-load → sum Ry = 0
    assert_close(reaction_fy_sum, 0.0, TOL_ABSOLUTE_FORCE_IN_NEWTON);

    // No parasitic Z reactions expected
    assert_close(reaction_fz_sum, 0.0, TOL_ABSOLUTE_FORCE_IN_NEWTON);

    // Opposite vertical reactions at the two bases (frame action)
    let fy1 = reactions_node1.fy;
    let fy2 = reactions_node2.fy;
    assert!(
        fy1 * fy2 <= 0.0,
        "Expected opposite signs for Fy at nodes 1 and 2, got Fy1={}, Fy2={}",
        fy1,
        fy2
    );
    assert_close(fy1 + fy2, 0.0, TOL_ABSOLUTE_FORCE_IN_NEWTON);

    // Node 3 has only Uz fixed; it should not pick up significant X or Y reaction.
    assert!(reactions_node3.fx.abs() < TOL_ABSOLUTE_FORCE_IN_NEWTON);
    assert!(reactions_node3.fy.abs() < TOL_ABSOLUTE_FORCE_IN_NEWTON);
}

#[test]
fn test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium_rigid_member() {
    test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium_impl(
        RigidStrategy::RigidMember,
    );
}

#[test]
fn test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium_mpc_linear() {
    test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium_impl(
        RigidStrategy::LinearMpc,
    );
}
