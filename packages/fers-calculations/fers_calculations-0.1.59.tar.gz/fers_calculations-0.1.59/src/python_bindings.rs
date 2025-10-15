// only compiled when you do `--features python`
use crate::analysis::{
    calculate_from_file_internal, calculate_from_json_internal,
    load_fers_from_file as load_fers_from_file_internal,
};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pyfunction]
pub fn calculate_from_json(json_data: &str) -> PyResult<String> {
    // map internal error -> Python RuntimeError
    calculate_from_json_internal(json_data).map_err(|e| PyRuntimeError::new_err(e.to_string()))
}

#[pyfunction]
pub fn calculate_from_file(path: &str) -> PyResult<String> {
    // map internal error -> Python RuntimeError
    calculate_from_file_internal(path).map_err(|e| PyRuntimeError::new_err(e.to_string()))
}

#[pyfunction]
pub fn load_fers_from_file(path: &str) -> PyResult<String> {
    let fers =
        load_fers_from_file_internal(path).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

    serde_json::to_string(&fers).map_err(|e| PyRuntimeError::new_err(e.to_string()))
}

#[pymodule]
fn fers_calculations(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_from_json, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_from_file, m)?)?;
    m.add_function(wrap_pyfunction!(load_fers_from_file, m)?)?;
    Ok(())
}
