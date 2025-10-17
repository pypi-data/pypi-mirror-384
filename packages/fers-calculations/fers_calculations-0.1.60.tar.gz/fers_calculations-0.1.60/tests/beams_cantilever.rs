use fers_calculations::models::fers::fers::FERS;
use fers_calculations::models::settings::analysissettings::RigidStrategy;

#[path = "test_support/mod.rs"]
mod test_support;

use test_support::formulas::*;
use test_support::helpers::*;
use test_support::*;

// ===================== 001 =====================

fn test_001_cantilever_with_end_load_impl(strategy: RigidStrategy) {
    let mut model: FERS = make_fers_with_strategy(strategy);

    // Material and Section
    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    // Supports
    let support_fixed_id = 1_u32;
    model
        .nodal_supports
        .push(make_fixed_support(support_fixed_id));

    // Geometry
    let beam_length_meter = 5.0_f64;
    let node1_id = 1_u32;
    let node2_id = 2_u32;

    let node_fixed = make_node(node1_id, 0.0, 0.0, 0.0, Some(support_fixed_id));
    let node_free = make_node(node2_id, beam_length_meter, 0.0, 0.0, None);

    // Members + MemberSet
    let m1 = make_beam_member(1, &node_fixed, &node_free, sec_id);
    let _ms_id = add_member_set(&mut model, 1, vec![m1]);

    // Loads
    let force_newton = 1000.0_f64;
    let lc_id = add_load_case(&mut model, 1, "End Load");
    add_nodal_load(
        &mut model,
        1,
        lc_id,
        node2_id,
        force_newton,
        (0.0, -1.0, 0.0),
    );

    // Solve
    model.solve_for_load_case(lc_id).expect("Analysis failed");

    // Results
    let bundle = model.results.as_ref().expect("results missing");
    let res = bundle.loadcases.get("End Load").expect("case missing");

    let fers_dy_free = res.displacement_nodes.get(&node2_id).unwrap().dy;
    let fers_mz_fixed = res.reaction_nodes.get(&node1_id).unwrap().nodal_forces.mz;

    // Expectations
    let steel_e = 210.0e9_f64;
    let expected_dy_free = cantilever_end_point_load_deflection_at_free_end(
        force_newton,
        beam_length_meter,
        steel_e,
        SECOND_MOMENT_STRONG_AXIS_IN_M4,
    );
    let expected_mz_fixed_magnitude =
        cantilever_end_point_load_fixed_end_moment_magnitude(force_newton, beam_length_meter);

    assert_close(
        fers_dy_free,
        expected_dy_free,
        TOL_ABSOLUTE_DISPLACEMENT_IN_METER,
    );
    assert_close(
        fers_mz_fixed.abs(),
        expected_mz_fixed_magnitude,
        TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER,
    );
}

#[test]
fn test_001_cantilever_with_end_load_rigid_member() {
    test_001_cantilever_with_end_load_impl(RigidStrategy::RigidMember);
}

#[test]
fn test_001_cantilever_with_end_load_mpc_linear() {
    test_001_cantilever_with_end_load_impl(RigidStrategy::LinearMpc);
}
