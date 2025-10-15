use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::collections::HashMap;

use fw_file::dcm;
use fw_file::dcm::parse;

#[derive(Debug, Clone)]
pub enum DicomValue {
    Int(i64),
    Float(f64),
    Str(String),
    Strings(Vec<String>),
    Ints(Vec<i64>),
    Floats(Vec<f64>),
    Empty,
    Unsupported(String),
}

impl<'py> IntoPyObject<'py> for DicomValue {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            DicomValue::Int(i) => Ok(i.into_pyobject(py).map_err(PyErr::from)?.into_any()),
            DicomValue::Float(f) => Ok(f.into_pyobject(py).map_err(PyErr::from)?.into_any()),
            DicomValue::Str(s) => Ok(s.into_pyobject(py).map_err(PyErr::from)?.into_any()),
            DicomValue::Strings(v) => Ok(v.into_pyobject(py).map_err(PyErr::from)?.into_any()),
            DicomValue::Ints(v) => Ok(v.into_pyobject(py).map_err(PyErr::from)?.into_any()),
            DicomValue::Floats(v) => Ok(v.into_pyobject(py).map_err(PyErr::from)?.into_any()),
            DicomValue::Empty => Ok(py.None().into_bound(py)),
            DicomValue::Unsupported(s) => Ok(s.into_pyobject(py).map_err(PyErr::from)?.into_any()),
        }
    }
}

impl<'py> FromPyObject<'py> for DicomValue {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        if ob.is_none() {
            return Ok(DicomValue::Empty);
        }
        if let Ok(i) = ob.extract::<i64>() {
            return Ok(DicomValue::Int(i));
        }
        if let Ok(f) = ob.extract::<f64>() {
            return Ok(DicomValue::Float(f));
        }
        if let Ok(s) = ob.extract::<String>() {
            return Ok(DicomValue::Str(s));
        }
        if let Ok(v) = ob.extract::<Vec<String>>() {
            return Ok(DicomValue::Strings(v));
        }
        if let Ok(v) = ob.extract::<Vec<i64>>() {
            return Ok(DicomValue::Ints(v));
        }
        if let Ok(v) = ob.extract::<Vec<f64>>() {
            return Ok(DicomValue::Floats(v));
        }
        Ok(DicomValue::Unsupported(format!(
            "Unsupported type: {:?}",
            ob
        )))
    }
}

impl From<dcm::DicomValue> for DicomValue {
    fn from(v: dcm::DicomValue) -> Self {
        match v {
            dcm::DicomValue::Int(i) => Self::Int(i),
            dcm::DicomValue::Float(f) => Self::Float(f),
            dcm::DicomValue::Str(s) => Self::Str(s),
            dcm::DicomValue::Strings(v) => Self::Strings(v),
            dcm::DicomValue::Ints(v) => Self::Ints(v),
            dcm::DicomValue::Floats(v) => Self::Floats(v),
            dcm::DicomValue::Empty => Self::Empty,
            dcm::DicomValue::Unsupported(s) => Self::Unsupported(s),
        }
    }
}

impl From<DicomValue> for dcm::DicomValue {
    fn from(v: DicomValue) -> Self {
        match v {
            DicomValue::Int(i) => dcm::DicomValue::Int(i),
            DicomValue::Float(f) => dcm::DicomValue::Float(f),
            DicomValue::Str(s) => dcm::DicomValue::Str(s),
            DicomValue::Strings(v) => dcm::DicomValue::Strings(v),
            DicomValue::Ints(v) => dcm::DicomValue::Ints(v),
            DicomValue::Floats(v) => dcm::DicomValue::Floats(v),
            DicomValue::Empty => dcm::DicomValue::Empty,
            DicomValue::Unsupported(s) => dcm::DicomValue::Unsupported(s),
        }
    }
}

#[pyfunction]
#[pyo3(signature = (bytes, include_tags=None))]
pub fn parse_header(
    _py: Python,
    bytes: &[u8],
    include_tags: Option<Vec<String>>,
) -> PyResult<HashMap<String, DicomValue>> {
    let tag_refs: Vec<&str> = include_tags
        .as_ref()
        .map(|v| v.iter().map(String::as_str).collect())
        .unwrap_or_default();
    let result = parse::parse_header(bytes, &tag_refs)
        .map_err(|e| PyValueError::new_err(format!("get_dcm_meta failed: {}", e)))?;
    let py_map: HashMap<String, DicomValue> = result
        .into_iter()
        .map(|(k, v)| (k, DicomValue::from(v)))
        .collect();

    Ok(py_map)
}
