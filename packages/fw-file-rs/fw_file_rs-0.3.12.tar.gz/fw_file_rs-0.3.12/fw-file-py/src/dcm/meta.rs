use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::collections::HashMap;

use fw_file::dcm;

use crate::dcm::parse::DicomValue;

#[pyfunction]
#[pyo3(signature = (header, _mappings=None))]
pub fn get_fw_meta(
    _py: Python,
    header: HashMap<String, DicomValue>,
    _mappings: Option<Vec<String>>,
) -> PyResult<HashMap<String, String>> {
    let dicom_map: HashMap<String, dcm::DicomValue> =
        header.into_iter().map(|(k, v)| (k, v.into())).collect();
    let result = dcm::get_fw_meta(dicom_map, &[])
        .map_err(|e| PyValueError::new_err(format!("get_fw_meta failed: {}", e)))?;
    Ok(result)
}
