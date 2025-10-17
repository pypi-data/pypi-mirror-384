use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, ToSchema)]
pub enum RigidStrategy {
    /// Serialize as "LINEAR_MPC"; also accept "Linear_MPC" and "linear_mpc"
    #[serde(alias = "Linear_MPC", alias = "linear_mpc")]
    LinearMpc,

    /// Serialize as "RIGID_MEMBER"; also accept "rigid_member"
    #[serde(alias = "rigid_member", alias = "Rigid_Member")]
    RigidMember,
}

/// Python:
/// class AnalysisOrder(Enum):
///     LINEAR = "LINEAR"
///     NONLINEAR = "NONLINEAR"
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, ToSchema)]
#[serde(rename_all = "UPPERCASE")]
pub enum AnalysisOrder {
    /// Serialize as "LINEAR"; also accept "Linear" / "linear"
    #[serde(alias = "Linear", alias = "linear")]
    Linear,

    /// Serialize as "NONLINEAR"; also accept "Nonlinear" / "nonlinear"
    #[serde(alias = "Nonlinear", alias = "nonlinear")]
    Nonlinear,
}

/// Python:
/// class Dimensionality(Enum):
///     TWO_DIMENSIONAL = "2D"
///     THREE_DIMENSIONAL = "3D"
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, ToSchema)]
pub enum Dimensionality {
    /// Serialize as "2D"; also accept several common spellings
    #[serde(rename = "2D", alias = "2d")]
    TwoDimensional,

    /// Serialize as "3D"; also accept several common spellings
    #[serde(rename = "3D", alias = "3d")]
    ThreeDimensional,
}

#[derive(Debug, Serialize, Deserialize, ToSchema)]
pub struct AnalysisOptions {
    pub id: u32,
    pub solve_loadcases: bool,
    pub solver: String,
    pub tolerance: f64,
    pub max_iterations: Option<u32>,
    pub dimensionality: Dimensionality,
    pub order: AnalysisOrder,
    pub rigid_strategy: RigidStrategy,
}
