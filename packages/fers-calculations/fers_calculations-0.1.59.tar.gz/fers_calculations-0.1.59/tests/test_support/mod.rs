// tests/test_support/mod.rs
#![allow(dead_code)]

pub mod formulas;
pub mod helpers;
pub mod materials;
pub mod sections;

pub const TOL_ABSOLUTE_DISPLACEMENT_IN_METER: f64 = 1.0e-9;
pub const TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER: f64 = 1.0e-5;
pub const TOL_ABSOLUTE_FORCE_IN_NEWTON: f64 = 1.0e-6;
pub const TOL_ABSOLUTE_ROTATION_IN_RADIAN: f64 = 1.0e-9;

/// Strong-axis inertia used by your analytic helpers (about local z for vertical loading).
pub const SECOND_MOMENT_STRONG_AXIS_IN_M4: f64 = 10.63e-6;

pub fn assert_close(actual: f64, expected: f64, abs_tol: f64) {
    let diff = (actual - expected).abs();
    assert!(
        diff <= abs_tol,
        "Expected {expected}, got {actual}, |diff|={diff} > {abs_tol}"
    );
}
