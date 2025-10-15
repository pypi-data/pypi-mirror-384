use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

#[pyfunction]
fn verify_bet(py: Python<'_>, receipt_json: &str, transcript_json: &str) -> PyResult<()> {
    py.allow_threads(|| pf_bindings_core::verify_bet(receipt_json, transcript_json))
        .map_err(|err| PyValueError::new_err(err.to_string()))
}

#[pyfunction]
fn register_gdp_package(py: Python<'_>, bytes: &[u8]) -> PyResult<()> {
    py.allow_threads(|| pf_bindings_core::register_gdp_package(bytes))
        .map_err(|err| PyValueError::new_err(err.to_string()))
}

#[pymodule]
fn pf_bindings_python(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(verify_bet, m)?)?;
    m.add_function(wrap_pyfunction!(register_gdp_package, m)?)?;
    Ok(())
}
