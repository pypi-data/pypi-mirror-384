use crate::models::settings::analysissettings::AnalysisOptions;
use crate::models::settings::generalinfo::GeneralInfo;
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Debug, Serialize, Deserialize, ToSchema)]
pub struct Settings {
    pub id: u32,
    pub analysis_options: AnalysisOptions,
    pub general_info: GeneralInfo,
}
