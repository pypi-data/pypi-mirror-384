use pyo3::prelude::*;
use std::collections::HashMap;

use fw_file::dcm;
use fw_file::dcm::group;

use crate::dcm::parse::DicomValue;

#[pyclass]
#[derive(Debug, Clone)]
pub struct DCMGroup {
    #[pyo3(get)]
    paths: Vec<String>,
    #[pyo3(get)]
    is_localizer: bool,
}

impl From<dcm::DCMGroup> for DCMGroup {
    fn from(group: dcm::DCMGroup) -> Self {
        DCMGroup {
            paths: group.paths,
            is_localizer: group.is_localizer,
        }
    }
}

#[pyfunction]
pub fn group_series(
    py: Python<'_>,
    path_meta_pairs: Vec<(String, HashMap<String, DicomValue>)>,
    group_by_tags: Vec<String>,
    split_localizer: bool,
) -> PyResult<Vec<Py<DCMGroup>>> {
    let path_meta_pairs: Vec<(String, HashMap<String, dcm::DicomValue>)> = path_meta_pairs
        .iter()
        .map(|(path, meta)| {
            (
                path.clone(),
                meta.iter()
                    .map(|(k, v)| {
                        let value = match v {
                            DicomValue::Int(i) => dcm::DicomValue::Int(*i),
                            DicomValue::Float(f) => dcm::DicomValue::Float(*f),
                            DicomValue::Str(s) => dcm::DicomValue::Str(s.clone()),
                            DicomValue::Strings(v) => dcm::DicomValue::Strings(v.clone()),
                            DicomValue::Ints(v) => dcm::DicomValue::Ints(v.clone()),
                            DicomValue::Floats(v) => dcm::DicomValue::Floats(v.clone()),
                            _ => dcm::DicomValue::Unsupported("".to_string()),
                        };
                        (k.to_string(), value)
                    })
                    .collect(),
            )
        })
        .collect();
    let group_by_tags_ref: Vec<&str> = group_by_tags.iter().map(|s| s.as_str()).collect();
    let groups = group::group_series(&path_meta_pairs, Some(&group_by_tags_ref), split_localizer);
    Ok(groups
        .into_iter()
        .map(|g| Py::new(py, DCMGroup::from(g)).unwrap())
        .collect())
}
