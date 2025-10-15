use std::collections::HashMap;

use chrono::{DateTime, FixedOffset};
pub use dicom_core::value::PrimitiveValue;
use once_cell::sync::Lazy;
use regex::Regex;

use crate::dcm::DicomValue;
use crate::dcm::utils;

static UID_TIMESTAMP_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"\d+(\.\d+)*\.(?P<timestamp>(19|20)\d{12,})(\.\d+)*").unwrap());

fn safe_extract<T, F>(func: F) -> Option<T>
where
    F: FnOnce() -> Result<T, Box<dyn std::error::Error>>,
{
    match func() {
        Ok(value) => Some(value),
        Err(_e) => None,
    }
}

fn get_timestamp(
    meta_map: &HashMap<String, DicomValue>,
    tag_prefix: &str,
) -> Option<DateTime<FixedOffset>> {
    if !matches!(tag_prefix, "Study" | "Series" | "Acquisition") {
        return None;
    }

    let mut datetime_str = String::new();

    if tag_prefix == "Acquisition" {
        if let Some(dt) = get_dicom_string_value_from_map(meta_map, "AcquisitionDateTime") {
            datetime_str = dt;
        }
    }

    if datetime_str.is_empty() {
        if let Some(date) =
            get_dicom_string_value_from_map(meta_map, &format!("{}Date", tag_prefix))
        {
            let time = get_dicom_string_value_from_map(meta_map, &format!("{}Time", tag_prefix))
                .unwrap_or_default();
            datetime_str = format!("{}{}", date, time);
        }
    }

    if datetime_str.is_empty() && tag_prefix != "Acquisition" {
        if let Some(uid_ts) = get_uid_timestamp_from_map(meta_map, tag_prefix) {
            datetime_str = uid_ts;
        }
    }

    if datetime_str.is_empty() {
        return None;
    }

    if !Regex::new(r"[+-]\d{4}$").unwrap().is_match(&datetime_str) {
        if let Some(offset) = get_dicom_string_value_from_map(meta_map, "TimezoneOffsetFromUTC") {
            let offset = if !offset.starts_with('+') && !offset.starts_with('-') {
                format!("+{}", offset)
            } else {
                offset
            };
            datetime_str = format!("{}{}", datetime_str, offset);
        }
    }

    if let Some(parsed_datetime) = utils::parse_dicom_datetime("DT", &datetime_str) {
        Some(parsed_datetime)
    } else {
        None
    }
}

fn get_uid_timestamp_from_map(
    meta_map: &HashMap<String, DicomValue>,
    tag_prefix: &str,
) -> Option<String> {
    if !matches!(tag_prefix, "Study" | "Series") {
        return None;
    }
    let uid = get_dicom_string_value_from_map(meta_map, &format!("{}InstanceUID", tag_prefix))?;

    UID_TIMESTAMP_RE
        .captures(&uid)
        .and_then(|caps| caps.name("timestamp"))
        .map(|m| m.as_str()[..14.min(m.len())].to_string())
}

fn get_dicom_string_value_from_map(
    meta_map: &HashMap<String, DicomValue>,
    tag_name: &str,
) -> Option<String> {
    match meta_map.get(tag_name) {
        Some(DicomValue::Str(s)) => Some(s.clone()),
        Some(DicomValue::Strings(v)) if !v.is_empty() => Some(v[0].clone()),
        _ => None,
    }
}

fn get_dicom_int_value_from_map(
    meta_map: &HashMap<String, DicomValue>,
    tag_name: &str,
) -> Option<i64> {
    match meta_map.get(tag_name) {
        Some(DicomValue::Int(i)) => Some(*i),
        Some(DicomValue::Ints(v)) if !v.is_empty() => Some(v[0]),
        _ => None,
    }
}

fn get_dicom_float_value_from_map(
    meta_map: &HashMap<String, DicomValue>,
    tag_name: &str,
) -> Option<f64> {
    match meta_map.get(tag_name) {
        Some(DicomValue::Float(f)) => Some(*f),
        Some(DicomValue::Floats(v)) if !v.is_empty() => Some(v[0]),
        _ => None,
    }
}

fn parse_person_name(name: &str) -> (Option<String>, Option<String>) {
    if name.contains('^') {
        let parts: Vec<&str> = name.split('^').collect();
        let lastname = parts[0].trim().to_string();
        let firstname = if parts.len() > 1 {
            parts[1].trim().to_string()
        } else {
            String::new()
        };
        (
            if firstname.is_empty() {
                None
            } else {
                Some(firstname)
            },
            if lastname.is_empty() {
                None
            } else {
                Some(lastname)
            },
        )
    } else {
        let parts: Vec<&str> = name.rsplitn(2, ' ').collect();
        if parts.len() == 2 {
            (
                Some(parts[1].trim().to_string()),
                Some(parts[0].trim().to_string()),
            )
        } else {
            (None, Some(name.trim().to_string()))
        }
    }
}

fn get_patient_name_from_map(
    meta_map: &HashMap<String, DicomValue>,
) -> (Option<String>, Option<String>) {
    get_dicom_string_value_from_map(meta_map, "PatientName")
        .map(|name| parse_person_name(&name))
        .unwrap_or((None, None))
}

fn get_operators_name_from_map(meta_map: &HashMap<String, DicomValue>) -> Option<String> {
    safe_extract(|| -> Result<String, Box<dyn std::error::Error>> {
        match meta_map.get("OperatorsName") {
            Some(DicomValue::Str(name)) => {
                let (first, last) = parse_person_name(name);
                let full_name = match (first, last) {
                    (Some(f), Some(l)) => format!("{} {}", f, l),
                    (Some(f), None) => f,
                    (None, Some(l)) => l,
                    _ => String::new(),
                };
                Ok(full_name)
            }
            Some(DicomValue::Strings(names)) => {
                let formatted_names: Vec<String> = names
                    .iter()
                    .map(|name| {
                        let (first, last) = parse_person_name(name);
                        match (first, last) {
                            (Some(f), Some(l)) => format!("{} {}", f, l),
                            (Some(f), None) => f,
                            (None, Some(l)) => l,
                            _ => String::new(),
                        }
                    })
                    .filter(|s| !s.is_empty())
                    .collect();
                Ok(formatted_names.join(", "))
            }
            _ => Ok(String::new()),
        }
    })
    .filter(|s| !s.is_empty())
}

fn birthdate_to_age(
    birth_date: DateTime<FixedOffset>,
    reference_date: DateTime<FixedOffset>,
) -> Option<i64> {
    if reference_date < birth_date {
        return None;
    }

    let duration = reference_date.signed_duration_since(birth_date);
    Some(duration.num_seconds())
}

fn get_session_age_from_map(meta_map: &HashMap<String, DicomValue>) -> Option<i64> {
    safe_extract(|| -> Result<i64, Box<dyn std::error::Error>> {
        if let Some(age_str) = get_dicom_string_value_from_map(meta_map, "PatientAge") {
            static AGE_RE: Lazy<Regex> =
                Lazy::new(|| Regex::new(r"(?P<value>[0-9]+)(?P<scale>[dwmyDWMY])?").unwrap());

            if let Some(caps) = AGE_RE.captures(&age_str) {
                let value: i64 = caps.name("value").unwrap().as_str().parse()?;
                let scale = caps
                    .name("scale")
                    .map(|m| m.as_str().to_uppercase())
                    .unwrap_or_else(|| "Y".to_string());

                let conversion = match scale.as_str() {
                    "Y" => 365.25 * 86400.0,
                    "M" => 30.0 * 86400.0,
                    "W" => 7.0 * 86400.0,
                    "D" => 86400.0,
                    _ => 365.25 * 86400.0, // Default to years
                };

                return Ok((value as f64 * conversion) as i64);
            }
        }

        let birth_date_str =
            get_dicom_string_value_from_map(meta_map, "PatientBirthDate").unwrap_or_default();
        let birth_date =
            utils::parse_dicom_datetime("DT", &birth_date_str).ok_or("No valid birth date")?;
        let acq_timestamp =
            get_acquisition_timestamp_from_map(meta_map).ok_or("No acquisition timestamp")?;

        birthdate_to_age(birth_date, acq_timestamp).ok_or("Invalid age calculation".into())
    })
}

fn get_session_label_from_map(meta_map: &HashMap<String, DicomValue>) -> Option<String> {
    safe_extract(|| -> Result<String, Box<dyn std::error::Error>> {
        if let Some(label) = get_dicom_string_value_from_map(meta_map, "StudyDescription") {
            if !label.trim().is_empty() {
                return Ok(label);
            }
        }

        if let Some(ts) = get_session_timestamp_from_map(meta_map) {
            return Ok(ts.format("%Y-%m-%dT%H-%M-%S").to_string());
        }
        get_dicom_string_value_from_map(meta_map, "StudyInstanceUID")
            .ok_or("No session label available".into())
    })
}

fn get_session_timestamp_from_map(
    meta_map: &HashMap<String, DicomValue>,
) -> Option<DateTime<FixedOffset>> {
    get_timestamp(meta_map, "Study")
        .or_else(|| get_timestamp(meta_map, "Series"))
        .or_else(|| get_timestamp(meta_map, "Acquisition"))
}

fn get_acquisition_uid_from_map(meta_map: &HashMap<String, DicomValue>) -> Option<String> {
    safe_extract(|| -> Result<String, Box<dyn std::error::Error>> {
        get_dicom_string_value_from_map(meta_map, "SeriesInstanceUID")
            .ok_or("No SeriesInstanceUID".into())
    })
}

fn get_acquisition_label_from_map(meta_map: &HashMap<String, DicomValue>) -> Option<String> {
    safe_extract(|| -> Result<String, Box<dyn std::error::Error>> {
        let mut label = get_dicom_string_value_from_map(meta_map, "SeriesDescription")
            .or_else(|| get_dicom_string_value_from_map(meta_map, "ProtocolName"));

        if label.is_none() {
            if let Some(ts) = get_acquisition_timestamp_from_map(meta_map) {
                label = Some(ts.format("%Y-%m-%dT%H-%M-%S").to_string());
            }
        }

        let label = label
            .or_else(|| get_dicom_string_value_from_map(meta_map, "SeriesInstanceUID"))
            .ok_or("No acquisition label available")?;

        // Prepend series number if available
        if let Some(series_number) = get_dicom_int_value_from_map(meta_map, "SeriesNumber") {
            Ok(format!("{} - {}", series_number, label))
        } else {
            Ok(label)
        }
    })
}

fn get_acquisition_timestamp_from_map(
    meta_map: &HashMap<String, DicomValue>,
) -> Option<DateTime<FixedOffset>> {
    get_timestamp(meta_map, "Acquisition")
        .or_else(|| get_timestamp(meta_map, "Series"))
        .or_else(|| get_timestamp(meta_map, "Study"))
}

pub fn get_fw_meta(
    header: HashMap<String, DicomValue>,
    _: &[&str], // mappings will be passed here
) -> Result<HashMap<String, String>, String> {
    let (firstname, lastname) = get_patient_name_from_map(&header);

    let mut meta = HashMap::new();

    if let Some(subject_label) = get_dicom_string_value_from_map(&header, "PatientID") {
        meta.insert("subject.label".to_string(), subject_label);
    }
    if let Some(firstname) = firstname {
        meta.insert("subject.firstname".to_string(), firstname);
    }
    if let Some(lastname) = lastname {
        meta.insert("subject.lastname".to_string(), lastname);
    }
    if let Some(sex) = get_dicom_string_value_from_map(&header, "PatientSex") {
        meta.insert("subject.sex".to_string(), sex);
    }

    if let Some(session_uid) = get_dicom_string_value_from_map(&header, "StudyInstanceUID") {
        meta.insert("session.uid".to_string(), session_uid);
    }
    if let Some(session_label) = get_session_label_from_map(&header) {
        meta.insert("session.label".to_string(), session_label);
    }
    if let Some(session_age) = get_session_age_from_map(&header) {
        meta.insert("session.age".to_string(), session_age.to_string());
    }
    if let Some(session_weight) = get_dicom_float_value_from_map(&header, "PatientWeight") {
        meta.insert("session.weight".to_string(), session_weight.to_string());
    }
    if let Some(session_operator) = get_operators_name_from_map(&header) {
        meta.insert("session.operator".to_string(), session_operator);
    }
    if let Some(session_timestamp) = get_session_timestamp_from_map(&header) {
        meta.insert(
            "session.timestamp".to_string(),
            session_timestamp.to_rfc3339(),
        );
    }

    if let Some(acquisition_uid) = get_acquisition_uid_from_map(&header) {
        meta.insert("acquisition.uid".to_string(), acquisition_uid);
    }
    if let Some(acquisition_label) = get_acquisition_label_from_map(&header) {
        meta.insert("acquisition.label".to_string(), acquisition_label);
    }
    if let Some(acquisition_timestamp) = get_acquisition_timestamp_from_map(&header) {
        meta.insert(
            "acquisition.timestamp".to_string(),
            acquisition_timestamp.to_rfc3339(),
        );
    }

    Ok(meta)
}
