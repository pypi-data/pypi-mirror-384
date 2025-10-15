use std::collections::HashMap;
use std::fs::File;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use fw_file::dcm;

use crate::dcm::group::DCMGroup;
use crate::dcm::parse::DicomValue;

#[pyclass]
#[derive(Debug, Clone)]
pub struct Context {
    inner: dcm::Context,
}

#[pymethods]
impl Context {
    #[new]
    pub fn new() -> Self {
        Self {
            inner: dcm::Context::new(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Self {
            inner: dcm::Context::default(),
        }
    }

    pub fn stop_at_tags(mut slf: PyRefMut<Self>, tags: Vec<(u16, u16)>) -> PyRefMut<Self> {
        slf.inner = slf.inner.clone().stop_at_tags(tags);
        slf
    }

    pub fn max_size(mut slf: PyRefMut<Self>, size: usize) -> PyRefMut<Self> {
        slf.inner = slf.inner.clone().max_size(size);
        slf
    }

    pub fn include_tags(mut slf: PyRefMut<Self>, tags: Vec<String>) -> PyRefMut<Self> {
        slf.inner = slf.inner.clone().include_tags(tags);
        slf
    }

    pub fn group_by_tags(mut slf: PyRefMut<Self>, tags: Vec<String>) -> PyRefMut<Self> {
        slf.inner = slf.inner.clone().group_by_tags(tags);
        slf
    }

    pub fn split_localizer(mut slf: PyRefMut<Self>, flag: bool) -> PyRefMut<Self> {
        slf.inner = slf.inner.clone().split_localizer(flag);
        slf
    }

    pub fn mappings(mut slf: PyRefMut<Self>, mappings: Vec<String>) -> PyRefMut<Self> {
        slf.inner = slf.inner.clone().mappings(mappings);
        slf
    }

    pub fn deid_profile<'a>(
        mut slf: PyRefMut<'a, Self>,
        yaml: &'a str,
    ) -> PyResult<PyRefMut<'a, Self>> {
        slf.inner = slf
            .inner
            .clone()
            .deid_profile(yaml)
            .map_err(|e| PyValueError::new_err(e))?;
        Ok(slf)
    }

    pub fn read_until_pixels<'py>(&self, py: Python<'py>, path: &str) -> PyResult<Py<PyBytes>> {
        let mut file = File::open(path)
            .map_err(|e| PyValueError::new_err(format!("Could not open file: {}", e)))?;

        let result = self
            .inner
            .read_until_pixels(&mut file)
            .map_err(|e| PyValueError::new_err(format!("read_until_pixels failed: {}", e)))?;

        Ok(PyBytes::new(py, &result).into())
    }

    pub fn parse_header<'py>(
        &self,
        _py: Python<'py>,
        bytes: &[u8],
    ) -> PyResult<HashMap<String, DicomValue>> {
        let result = self
            .inner
            .parse_header(bytes)
            .map_err(|e| PyValueError::new_err(format!("parse_header failed: {}", e)))?;

        let py_map: HashMap<String, DicomValue> = result
            .into_iter()
            .map(|(k, v)| (k, DicomValue::from(v)))
            .collect();

        Ok(py_map)
    }

    pub fn group_series<'py>(
        &self,
        py: Python<'py>,
        path_header_pairs: Vec<(String, HashMap<String, DicomValue>)>,
    ) -> PyResult<Vec<Py<DCMGroup>>> {
        let rust_pairs: Vec<(String, HashMap<String, dcm::DicomValue>)> = path_header_pairs
            .into_iter()
            .map(|(path, meta)| {
                let rust_meta = meta
                    .into_iter()
                    .map(|(k, v)| (k, dcm::DicomValue::from(v)))
                    .collect();
                (path, rust_meta)
            })
            .collect();

        let groups = self.inner.group_series(&rust_pairs);

        Ok(groups
            .into_iter()
            .map(|g| Py::new(py, DCMGroup::from(g)).unwrap())
            .collect())
    }

    pub fn get_fw_meta(
        &self,
        header: HashMap<String, DicomValue>,
    ) -> PyResult<HashMap<String, String>> {
        let rust_header: HashMap<String, dcm::DicomValue> = header
            .into_iter()
            .map(|(k, v)| (k, dcm::DicomValue::from(v)))
            .collect();

        let result = self
            .inner
            .get_fw_meta(rust_header)
            .map_err(|e| PyValueError::new_err(format!("get_fw_meta failed: {}", e)))?;

        Ok(result)
    }

    pub fn deid_header<'py>(&self, py: Python<'py>, bytes: &[u8]) -> PyResult<Py<PyBytes>> {
        let result = self
            .inner
            .deid_header(bytes)
            .map_err(|e| PyValueError::new_err(format!("deid_header failed: {}", e)))?;

        Ok(PyBytes::new(py, &result).into())
    }
}
