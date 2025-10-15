// src/models/results/reaction.rs
use crate::models::results::forces::NodeForces;
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[allow(non_snake_case)]
#[derive(Serialize, Deserialize, ToSchema, Debug, Clone)]
pub struct NodeLocation {
    pub X: f64,
    pub Y: f64,
    pub Z: f64,
}

#[derive(Serialize, Deserialize, ToSchema, Debug, Clone)]
pub struct ReactionNodeResult {
    pub nodal_forces: NodeForces,
    pub location: NodeLocation,
    pub support_id: u32,
}
