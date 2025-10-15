pub mod dcm;

use pyo3::prelude::*;

#[pymodule]
fn fw_file_rs(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    dcm::register(py, m)?;
    Ok(())
}
