// src/models/members/memberset.rs
use crate::models::members::member::Member;
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Serialize, Deserialize, ToSchema, Debug)]
pub struct MemberSet {
    pub id: u32,
    pub l_y: Option<f64>,
    pub l_z: Option<f64>,
    pub classification: Option<String>,
    pub members: Vec<Member>,
}
