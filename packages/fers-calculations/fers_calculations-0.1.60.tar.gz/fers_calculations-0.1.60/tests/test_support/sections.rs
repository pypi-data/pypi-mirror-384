use super::materials::Steel;

#[derive(Clone, Copy)]
pub struct Section {
    pub area: f64,
    pub i_strong: f64,
    pub steel: Steel,
}

/// This matches your IPE180 helper values as used in the Python tests.
/// Adjust if your real section values differ.
pub fn build_ipe180(steel: Steel) -> Section {
    Section {
        area: 26.2e-4, // m^2 (example; adjust to your exact helper)
        i_strong: super::SECOND_MOMENT_STRONG_AXIS_IN_M4,
        steel,
    }
}
