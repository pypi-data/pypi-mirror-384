use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

use crate::models::imperfections::rotationimperfection::RotationImperfection;
use crate::models::imperfections::translationimperfection::TranslationImperfection;
use crate::models::loads::loadcombination::LoadCombination;

#[derive(Debug, Serialize, Deserialize, ToSchema)]
pub struct ImperfectionCase {
    pub imperfection_case_id: u32,
    pub load_combinations: Vec<LoadCombination>,
    pub rotation_imperfections: Vec<RotationImperfection>,
    pub translation_imperfections: Vec<TranslationImperfection>,
}
