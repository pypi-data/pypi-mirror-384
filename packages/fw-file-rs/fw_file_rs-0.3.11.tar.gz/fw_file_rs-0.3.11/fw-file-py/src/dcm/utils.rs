use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::collections::HashMap;

use fw_file::dcm::utils;

use crate::dcm::parse::DicomValue;

use std::fs::File;

#[pyfunction]
#[pyo3(signature = (path, stop_tags=None))]
pub fn read_until_pixels<'py>(
    py: Python<'py>,
    path: &str,
    stop_tags: Option<Vec<(u16, u16)>>,
) -> PyResult<Py<PyBytes>> {
    let mut file = File::open(path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Could not open file: {}", e)))?;

    let mut combined_tags = Vec::new();
    combined_tags.extend(stop_tags.unwrap_or_default());
    combined_tags.extend(utils::STOP_TAGS);
    let data = utils::read_until_pixels(&mut file, &combined_tags, None)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))?;

    Ok(PyBytes::new(py, &data).into())
}

#[pyfunction]
pub fn create_dcm_as_bytes(tags: HashMap<String, DicomValue>) -> PyResult<Py<PyBytes>> {
    let tags_ref: HashMap<&str, utils::CreateDicomValue> = tags
        .iter()
        .map(|(k, v)| -> PyResult<(&str, utils::CreateDicomValue)> {
            let value = match v {
                DicomValue::Int(i) => utils::CreateDicomValue::from(*i),
                DicomValue::Float(f) => utils::CreateDicomValue::from(*f),
                DicomValue::Str(s) => utils::CreateDicomValue::from(s.clone()),
                DicomValue::Strings(v) => utils::CreateDicomValue::from(v.clone()),
                DicomValue::Ints(v) => utils::CreateDicomValue::from(v.clone()),
                DicomValue::Floats(v) => utils::CreateDicomValue::from(v.clone()),
                DicomValue::Empty => utils::CreateDicomValue::from("".to_string()),
                DicomValue::Unsupported(_) => {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "Unsupported value type",
                    ));
                }
            };
            Ok((k.as_str(), value))
        })
        .collect::<PyResult<HashMap<_, _>>>()?;

    let cursor = utils::create_dcm_as_bytes(tags_ref).map_err(|e| {
        pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create DCM: {:?}", e))
    })?;

    let py = unsafe { Python::assume_gil_acquired() }; // acquire Python GIL
    Ok(PyBytes::new(py, &cursor.into_inner()).into())
}
