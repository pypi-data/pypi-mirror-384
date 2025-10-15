use std::collections::HashMap;
use std::fmt;

pub use dicom_core::value::PrimitiveValue;
use dicom_core::{DataDictionary, Tag};
use dicom_dictionary_std::StandardDataDictionary;
use dicom_object::InMemDicomObject;
use serde::ser::{Serialize, Serializer};

use crate::dcm::utils::from_reader_flexible;

pub static DEFAULT_TAGS: &[&str] = &[
    "AcquisitionDate",
    "AcquisitionDateTime",
    "AcquisitionTime",
    "Columns",
    "ImageOrientationPatient",
    "ImagePositionPatient",
    "InstanceNumber",
    "OperatorsName",
    "PatientAge",
    "PatientBirthDate",
    "PatientID",
    "PatientName",
    "PatientSex",
    "PatientWeight",
    "ProtocolName",
    "Rows",
    "SeriesDate",
    "SeriesDescription",
    "SeriesInstanceUID",
    "SeriesNumber",
    "SeriesTime",
    "StudyDate",
    "StudyDescription",
    "StudyInstanceUID",
    "StudyTime",
    "TimezoneOffsetFromUTC",
];

#[derive(Clone, Debug, PartialEq)]
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

impl Serialize for DicomValue {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match self {
            DicomValue::Int(i) => serializer.serialize_i64(*i),
            DicomValue::Float(f) => serializer.serialize_f64(*f),
            DicomValue::Str(s) => serializer.serialize_str(s),
            DicomValue::Strings(v) => v.serialize(serializer),
            DicomValue::Ints(v) => v.serialize(serializer),
            DicomValue::Floats(v) => v.serialize(serializer),
            DicomValue::Empty => serializer.serialize_none(),
            DicomValue::Unsupported(msg) => {
                serializer.serialize_str(&format!("[unsupported: {msg}]"))
            }
        }
    }
}

impl fmt::Display for DicomValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        use DicomValue::*;
        match self {
            Int(v) => write!(f, "{}", v),
            Float(v) => write!(f, "{}", v),
            Str(s) => write!(f, "{}", s),
            Strings(vec) => write!(f, "[{}]", vec.join(", ")),
            Ints(vec) => write!(
                f,
                "[{}]",
                vec.iter()
                    .map(|v| v.to_string())
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Floats(vec) => write!(
                f,
                "[{}]",
                vec.iter()
                    .map(|v| v.to_string())
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Empty => write!(f, ""),
            Unsupported(s) => write!(f, "Unsupported({})", s),
        }
    }
}

pub fn parse_header(
    bytes: &[u8],
    include_tags: &[&str],
) -> Result<HashMap<String, DicomValue>, String> {
    let cursor = std::io::Cursor::new(bytes);
    let obj = from_reader_flexible(cursor)?;

    let mut map = HashMap::new();
    let mut tags = Vec::new();
    tags.extend_from_slice(include_tags);
    tags.extend_from_slice(DEFAULT_TAGS);
    for tag in tags {
        if let Ok((key, value)) = extract_dcm_values(&obj, tag) {
            map.insert(key, value);
        }
    }

    Ok(map)
}

pub fn extract_dcm_values(
    obj: &InMemDicomObject,
    tag_name: &str,
) -> Result<(String, DicomValue), String> {
    // TODO custom error type
    // TODO lower-case tag name support
    // TODO flexible numeric tag support (parens, brackets, space, comma, comma+space, etc.)
    // TODO advanced private tag support (creator + XX)
    let tag = StandardDataDictionary
        .parse_tag(tag_name)
        .ok_or_else(|| format!("Invalid tag name: {tag_name}"))?;
    let value = get_dcm_value(&obj, tag)?;
    let tag_name_str = match StandardDataDictionary.by_tag(tag) {
        Some(dict_entry) => dict_entry.alias.to_string(),
        None => tag_name.to_string(),
    };
    Ok((tag_name_str, value))
}

pub fn get_dcm_value(obj: &InMemDicomObject, tag: Tag) -> Result<DicomValue, String> {
    let elem = obj
        .element(tag)
        .map_err(|e| format!("Missing element: {e}"))?;

    // Check if the element has an empty value first
    if matches!(
        elem.value(),
        dicom_core::value::Value::Primitive(PrimitiveValue::Empty)
    ) {
        return Ok(DicomValue::Empty);
    }

    let value = match elem.vr().to_string() {
        "IS" | "SL" | "SS" | "UL" | "US" => match elem.to_multi_int::<i64>() {
            Ok(vs) => {
                if vs.is_empty() {
                    DicomValue::Empty
                } else if vs.len() == 1 {
                    DicomValue::Int(vs[0])
                } else {
                    DicomValue::Ints(vs)
                }
            }
            Err(_) => DicomValue::Unsupported("Invalid int value".to_string()),
        },
        "FL" | "FD" | "DS" => match elem.to_multi_float64() {
            Ok(vs) => {
                if vs.is_empty() {
                    DicomValue::Empty
                } else if vs.len() == 1 {
                    DicomValue::Float(vs[0])
                } else {
                    DicomValue::Floats(vs)
                }
            }
            Err(_) => DicomValue::Unsupported("Invalid float value".to_string()),
        },
        "SQ" => DicomValue::Unsupported("Sequence not supported".to_string()),
        _ => match elem.to_multi_str() {
            Ok(vs) => {
                let strings: Vec<String> = vs.iter().map(|s| s.to_string()).collect();
                if strings.is_empty() {
                    DicomValue::Empty
                } else if strings.len() == 1 {
                    DicomValue::Str(strings[0].clone())
                } else {
                    DicomValue::Strings(strings)
                }
            }
            Err(_) => DicomValue::Unsupported("Invalid string value".to_string()),
        },
    };
    Ok(value)
}
