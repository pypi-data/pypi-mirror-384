/// All formulas mirror your Python analytic helpers.

pub fn cantilever_end_point_load_deflection_at_free_end(
    force_newton: f64,
    length_meter: f64,
    elastic_modulus: f64,
    second_moment_m4: f64,
) -> f64 {
    -(force_newton * length_meter.powi(3)) / (3.0 * elastic_modulus * second_moment_m4)
}

pub fn cantilever_end_point_load_fixed_end_moment_magnitude(
    force_newton: f64,
    length_meter: f64,
) -> f64 {
    force_newton * length_meter
}

pub fn cantilever_point_load_deflection_at_position_a(
    force_newton: f64,
    position_a_meter: f64,
    elastic_modulus: f64,
    second_moment_m4: f64,
) -> f64 {
    -(force_newton * position_a_meter.powi(3)) / (3.0 * elastic_modulus * second_moment_m4)
}

pub fn cantilever_point_load_deflection_at_free_end_from_a(
    force_newton: f64,
    length_meter: f64,
    position_a_meter: f64,
    elastic_modulus: f64,
    second_moment_m4: f64,
) -> f64 {
    let a = position_a_meter;
    let l = length_meter;
    -((force_newton * a.powi(2) * (3.0 * l - a)) / (6.0 * elastic_modulus * second_moment_m4))
}

pub fn cantilever_uniform_load_deflection_at_free_end(
    intensity_newton_per_meter: f64,
    length_meter: f64,
    elastic_modulus: f64,
    second_moment_m4: f64,
) -> f64 {
    -(intensity_newton_per_meter * length_meter.powi(4))
        / (8.0 * elastic_modulus * second_moment_m4)
}

pub fn cantilever_uniform_load_fixed_end_moment(
    intensity_newton_per_meter: f64,
    length_meter: f64,
) -> f64 {
    0.5 * intensity_newton_per_meter * length_meter.powi(2)
}

pub fn simply_supported_center_point_load_deflection_at_midspan(
    force_newton: f64,
    length_meter: f64,
    elastic_modulus: f64,
    second_moment_m4: f64,
) -> f64 {
    -force_newton * length_meter.powi(3) / (48.0 * elastic_modulus * second_moment_m4)
}

pub fn simply_supported_center_point_load_max_moment(force_newton: f64, length_meter: f64) -> f64 {
    force_newton * length_meter / 4.0
}

pub fn simply_supported_reactions_for_point_load_at_x(
    force_newton: f64,
    length_meter: f64,
    position_from_left_meter: f64,
) -> (f64, f64) {
    let r_right = force_newton * position_from_left_meter / length_meter;
    let r_left = force_newton - r_right;
    (r_left, r_right)
}

pub fn cantilever_full_triangular_deflection_at_free_end(
    peak_intensity_newton_per_meter: f64,
    length_meter: f64,
    elastic_modulus: f64,
    second_moment_m4: f64,
) -> f64 {
    -(peak_intensity_newton_per_meter * length_meter.powi(4))
        / (30.0 * elastic_modulus * second_moment_m4)
}

pub fn cantilever_full_triangular_fixed_end_moment(
    peak_intensity_newton_per_meter: f64,
    length_meter: f64,
) -> f64 {
    peak_intensity_newton_per_meter * length_meter.powi(2) / 6.0
}

pub fn cantilever_full_inverse_triangular_fixed_end_moment(
    peak_intensity_newton_per_meter: f64,
    length_meter: f64,
) -> f64 {
    peak_intensity_newton_per_meter * length_meter.powi(2) / 3.0
}

pub fn cantilever_partial_uniform_resultant_and_fixed_moment(
    intensity_newton_per_meter: f64,
    length_meter: f64,
    start_frac: f64,
    end_frac: f64,
) -> (f64, f64) {
    let a = start_frac * length_meter;
    let b = end_frac * length_meter;
    let w = intensity_newton_per_meter;
    let resultant = w * (b - a);
    let centroid_from_fixed = a + (b - a) / 2.0;
    let fixed_end_moment = resultant * centroid_from_fixed;
    (resultant, fixed_end_moment)
}

pub fn cantilever_partial_triangular_resultant_and_fixed_moment(
    peak_intensity_newton_per_meter: f64,
    length_meter: f64,
    start_frac: f64,
    end_frac: f64,
    inverse: bool,
) -> (f64, f64) {
    let a = start_frac * length_meter;
    let b = end_frac * length_meter;
    let l = length_meter;
    let w0 = peak_intensity_newton_per_meter;

    // Linear load: w(x) = w0 * (x / l) for TRIANGULAR increasing from fixed end,
    // or w(x) = w0 * (1 - x / l) for INVERSE TRIANGULAR.
    let _load_at = |x: f64| {
        if inverse {
            w0 * (1.0 - x / l).max(0.0)
        } else {
            w0 * (x / l).max(0.0)
        }
    };

    // Resultant = integral_a^b w(x) dx
    let integral = |x: f64| {
        if inverse {
            w0 * (x - x.powi(2) / (2.0 * l))
        } else {
            w0 * (x.powi(2) / (2.0 * l))
        }
    };

    // First moment about the fixed end = integral_a^b w(x) * x dx
    let first_moment_integral = |x: f64| {
        if inverse {
            // integral x * w0 * (1 - x/l) dx = w0 * (x^2/2 - x^3/(3l))
            w0 * (x.powi(2) / 2.0 - x.powi(3) / (3.0 * l))
        } else {
            // integral x * w0 * (x/l) dx = w0/l * integral x^2 dx = w0 * x^3 / (3l)
            w0 * x.powi(3) / (3.0 * l)
        }
    };

    let resultant = integral(b) - integral(a);
    let first_moment = first_moment_integral(b) - first_moment_integral(a);
    let fixed_end_moment = first_moment; // about x=0

    (resultant, fixed_end_moment)
}
