use std::cmp::Ordering;
use std::fmt;

use chrono::{Datelike, Duration, NaiveDate, NaiveDateTime, NaiveTime};
use dicom_core::dictionary::DataDictionaryEntry;
use dicom_core::header::Header;
use dicom_core::{DataDictionary, DataElement, PrimitiveValue, Tag, VR};
use dicom_dictionary_std::StandardDataDictionary;
use dicom_object::mem::{InMemDicomObject, InMemElement};
use once_cell::sync::Lazy;
use rand::Rng;
use regex::Regex;
use serde::{Deserialize, Deserializer};
use serde_yaml::Value;
use sha2::{Digest, Sha256};
use smallvec::SmallVec;
use thiserror::Error;

use crate::dcm::parse::{DicomValue, get_dcm_value};
use crate::dcm::utils;

const PATIENT_BIRTH_DATE: Tag = Tag(0x0010, 0x0030);
const STUDY_DATE: Tag = Tag(0x0008, 0x0020);
const SERIES_DATE: Tag = Tag(0x0008, 0x0021);
const PATIENT_AGE: Tag = Tag(0x0010, 0x1010);
static DICOM_TAG_TUPLE_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"\(\s*([0-9a-fA-F]{4})\s*,\s*([0-9a-fA-F]{4})\s*\)").unwrap());

#[derive(Debug, Error)]
pub enum ProfileParseError {
    #[error("YAML parse error: {0}")]
    YamlError(String),

    #[error("Profile validation failed: {0:?}")]
    ValidationError(Vec<String>),

    #[error("Unsupported profile version: {0}")]
    UnsupportedVersion(u32),
}

#[derive(Debug, Clone)]
pub enum DeidProfile {
    V1(DeidProfileV1),
}

impl DeidProfile {
    pub fn from_yaml(yaml_data: &str) -> Result<DeidProfile, ProfileParseError> {
        let raw: Value = serde_yaml::from_str(yaml_data)
            .map_err(|e| ProfileParseError::YamlError(e.to_string()))?;
        let version = raw.get("version").and_then(|v| v.as_u64()).unwrap_or(1);
        match version {
            1 => {
                let v1: DeidProfileV1 = serde_yaml::from_value(raw)
                    .map_err(|e| ProfileParseError::YamlError(e.to_string()))?;
                Ok(DeidProfile::V1(v1))
            }
            v => Err(ProfileParseError::UnsupportedVersion(v as u32)),
        }
    }

    pub fn deid_dcm(&self, dcm: &[u8]) -> Result<Vec<u8>, String> {
        match self {
            DeidProfile::V1(profile) => profile.deid(dcm),
        }
    }
}

#[derive(Debug, Deserialize, Clone)]
pub struct DeidProfileV1 {
    pub name: Option<String>,
    pub dicom: Option<DicomSectionV1>,
}

impl DeidProfileV1 {
    pub fn deid(&self, dcm: &[u8]) -> Result<Vec<u8>, String> {
        match self.dicom {
            Some(ref dicom) => dicom.deid(dcm),
            None => Ok(dcm.to_vec()),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgeUnit {
    Years,
    Months,
    Days,
}

impl<'de> Deserialize<'de> for AgeUnit {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        match s.as_str() {
            "Y" | "y" => Ok(AgeUnit::Years),
            "M" | "m" => Ok(AgeUnit::Months),
            "D" | "d" => Ok(AgeUnit::Days),
            _ => Err(serde::de::Error::custom(format!("invalid age unit: {}", s))),
        }
    }
}

#[derive(Debug, Deserialize, Clone)]
pub struct DicomSectionV1 {
    pub fields: Option<Vec<FieldSpecV1>>,
    // global options
    #[serde(rename = "date-increment")]
    pub date_increment: Option<i64>,
    #[serde(rename = "jitter-type")]
    pub jitter_type: Option<String>,
    #[serde(rename = "jitter-range")]
    pub jitter_range: Option<f64>,
    #[serde(rename = "patient-age-from-birthdate")]
    pub patient_age_from_birthdate: Option<bool>,
    #[serde(rename = "patient-age-units")]
    pub patient_age_units: Option<AgeUnit>,
    #[serde(rename = "recurse-sequence")]
    pub recurse_sequence: Option<bool>,
    #[serde(rename = "remove-private-tags")]
    pub remove_private_tags: Option<bool>,
    #[serde(rename = "remove-undefined")]
    pub remove_undefined: Option<bool>,
}

impl DicomSectionV1 {
    pub fn deid(&self, dcm: &[u8]) -> Result<Vec<u8>, String> {
        // TODO collect errors and return them all at once
        let cursor = std::io::Cursor::new(dcm);
        let mut obj = utils::from_reader_flexible(cursor)?;

        if let Some(_) = self.patient_age_from_birthdate {
            set_patient_age_from_birth_date(&mut obj, self.patient_age_units)
                .map_err(|e| format!("Failed apply patient age from birthdate action: {e}"))?;
        }

        if self.remove_private_tags.unwrap_or(false) {
            let mut defined_private_tags: Vec<PrivateTag> = Vec::new();
            if let Some(ref fields) = self.fields {
                for field in fields {
                    if field.name.is_some() {
                        let fieldpaths = resolve_field_paths(&mut obj, field, false)?;
                        if fieldpaths.is_empty() {
                            continue;
                        }
                        // not nice but currently private tags always have one path with one item
                        if let Some(NestedItem::PrivateTag(tag)) = fieldpaths[0].get(0) {
                            defined_private_tags.push(tag.clone());
                        }
                    }
                }
            }
            remove_private_tags(&mut obj, &defined_private_tags);
        }

        let mut allowed_paths = Vec::new();

        if let Some(ref fields) = self.fields {
            for field in fields {
                let fieldpaths =
                    resolve_field_paths(&mut obj, field, self.recurse_sequence.unwrap_or(false))?;
                if fieldpaths.is_empty() {
                    continue;
                }

                if self.remove_undefined.unwrap_or(false) {
                    allowed_paths.extend(fieldpaths.clone());
                }

                for fieldpath in fieldpaths {
                    apply_to_path(&mut obj, &fieldpath, &|obj, tag| {
                        if field.remove.unwrap_or(false) {
                            apply_remove(obj, tag)
                                .map_err(|e| format!("Failed to apply remove action: {e}"))?;
                        } else if let Some(ref val) = field.replace_with {
                            apply_replace_with(obj, tag, val)
                                .map_err(|e| format!("Failed to apply replace-with action: {e}"))?;
                        } else if field.increment_date.unwrap_or(false) {
                            if let Some(days) = self.date_increment {
                                apply_increment_date(obj, tag, days).map_err(|e| {
                                    format!("Failed to apply increment-date action: {e}")
                                })?;
                            }
                        } else if field.hash.unwrap_or(false) {
                            apply_hash(obj, tag)
                                .map_err(|e| format!("Failed to apply hash action: {e}"))?;
                        } else if field.hash_uid.unwrap_or(false) {
                            apply_hash_uid(obj, tag)
                                .map_err(|e| format!("Failed to apply hashuid action: {e}"))?;
                        } else if field.jitter.unwrap_or(false) {
                            let range = self.jitter_range.or(field.jitter_range).unwrap_or(2.0);
                            let jitter_type = self
                                .jitter_type
                                .as_deref()
                                .or(field.jitter_type.as_deref())
                                .unwrap_or("float");
                            apply_jitter(
                                obj,
                                tag,
                                range,
                                &jitter_type,
                                field.jitter_min,
                                field.jitter_max,
                            )
                            .map_err(|e| format!("Failed to apply jitter action: {e}"))?;
                        }
                        Ok(())
                    })?;
                }
            }
        }

        if self.remove_undefined.unwrap_or(false) {
            remove_undefined_fields(&mut obj, &allowed_paths)?;
        }

        let mut out = Vec::new();
        obj.write_all(&mut out)
            .map_err(|e| format!("Failed to write DICOM: {e}"))?;
        Ok(out)
    }
}

#[derive(Debug, Deserialize, Clone)]
pub struct FieldSpecV1 {
    pub name: Option<String>,
    pub regex: Option<String>,
    pub remove: Option<bool>,
    #[serde(
        rename = "replace-with",
        deserialize_with = "empty_array_to_string",
        default
    )]
    pub replace_with: Option<String>,
    pub hash: Option<bool>,
    #[serde(rename = "hashuid")]
    pub hash_uid: Option<bool>,
    #[serde(rename = "increment-date")]
    pub increment_date: Option<bool>,
    pub jitter: Option<bool>,
    #[serde(rename = "jitter-type")]
    pub jitter_type: Option<String>,
    #[serde(rename = "jitter-range")]
    pub jitter_range: Option<f64>,
    #[serde(rename = "jitter-min")]
    pub jitter_min: Option<f64>,
    #[serde(rename = "jitter-max")]
    pub jitter_max: Option<f64>,
}

fn resolve_field_paths(
    obj: &mut InMemDicomObject,
    field: &FieldSpecV1,
    recurse_sequence: bool,
) -> Result<Vec<Vec<NestedItem>>, String> {
    if let Some(explicit_regex) = &field.regex {
        if recurse_sequence {
            return Err(
                "Sequence recursion is not supported when an explicit regex is specified."
                    .to_string(),
            );
        }
        return execute_regex_search(obj, explicit_regex);
    }

    if let Some(name) = &field.name {
        if let Some(pattern) = utils::build_repeater_pattern(name, recurse_sequence) {
            return execute_regex_search(obj, &pattern);
        } else {
            let mut fieldpaths = Vec::new();

            let initial_path = if let Some(captures) = DICOM_TAG_TUPLE_RE.captures(name) {
                format!(
                    "{}{}",
                    captures.get(1).unwrap().as_str(),
                    captures.get(2).unwrap().as_str()
                )
            } else {
                name.to_string()
            };

            let parsed_path = parse_nested_field(&initial_path)?;

            if recurse_sequence && parsed_path.len() > 1 {
                return Err("Sequence recursion not supported for pre-nested fields".to_string());
            }
            fieldpaths.push(parsed_path.clone());

            if recurse_sequence {
                if let Some(NestedItem::PrivateTag(tag)) = parsed_path.first() {
                    let private_paths = utils::get_private_tag_in_sequences(
                        obj,
                        tag.group,
                        tag.element,
                        &tag.creator,
                    );
                    for path in private_paths {
                        if path.ends_with(name) {
                            fieldpaths.push(parse_nested_field(&path)?);
                        }
                    }
                }
                let all_paths = utils::get_all_field_paths(obj);
                for path in all_paths {
                    if path.ends_with(name) {
                        fieldpaths.push(parse_nested_field(&path)?);
                    }
                }
            }

            return Ok(fieldpaths);
        }
    }

    Ok(Vec::new())
}

fn execute_regex_search(
    obj: &InMemDicomObject,
    pattern: &str,
) -> Result<Vec<Vec<NestedItem>>, String> {
    let re =
        Regex::new(pattern).map_err(|e| format!("Invalid field regex '{}': {}", pattern, e))?;
    let all_paths = utils::get_all_field_paths(obj);
    all_paths
        .iter()
        .filter(|path| re.is_match(path))
        .map(|path| parse_nested_field(path))
        .collect()
}

fn apply_to_path<F>(obj: &mut InMemDicomObject, path: &[NestedItem], f: &F) -> Result<(), String>
where
    F: Fn(&mut InMemDicomObject, NestedItem) -> Result<(), String>,
{
    if path.is_empty() {
        return Ok(());
    }

    match &path[0] {
        NestedItem::PrivateTag { .. } => {
            if path.len() == 1 {
                return f(obj, path[0].clone());
            }
            Err("Path must start with a tag".to_string())
        }
        NestedItem::Tag(tag) => {
            if path.len() == 1 {
                return f(obj, path[0].clone());
            }

            let elem = obj
                .element(*tag)
                .map_err(|e| format!("Tag {tag:?} not found: {e}"))?;

            if let dicom_core::value::Value::Sequence(seq) = elem.value() {
                let mut new_items = Vec::new();

                match &path[1] {
                    NestedItem::Index(idx) => {
                        for (i, item) in seq.items().iter().enumerate() {
                            let mut cloned = item.clone();
                            if i == *idx {
                                apply_to_path(&mut cloned, &path[2..], f)?;
                            }
                            new_items.push(cloned);
                        }
                    }
                    NestedItem::Wildcard => {
                        for item in seq.items() {
                            let mut cloned = item.clone();
                            apply_to_path(&mut cloned, &path[2..], f)?;
                            new_items.push(cloned);
                        }
                    }
                    NestedItem::Tag(_) => {
                        return Err("Expected sequence index but found tag".to_string());
                    }
                    NestedItem::PrivateTag { .. } => {
                        return Err("Expected sequence index but found private tag".to_string());
                    }
                }

                obj.put(DataElement::new(
                    tag.clone(),
                    VR::SQ,
                    dicom_core::value::DataSetSequence::<InMemDicomObject>::new(
                        new_items,
                        dicom_core::Length::UNDEFINED,
                    ),
                ));

                Ok(())
            } else {
                Ok(())
            }
        }
        _ => Err("Path must start with a tag".to_string()),
    }
}

pub fn apply_remove(
    obj: &mut InMemDicomObject,
    item: NestedItem,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(tag) = resolve_tag(obj, item)? {
        obj.remove_element(tag);
    }
    Ok(())
}

pub fn apply_replace_with(
    obj: &mut InMemDicomObject,
    item: NestedItem,
    new_text: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(tag) = resolve_tag(obj, item.clone())? {
        let vr = match obj.element(tag) {
            Ok(el) => el.header().vr(),
            Err(_) => resolve_vr(item.clone()).map_err(|e| format!("{tag}: {e}"))?,
        };
        let new_value = validate_vr_value(vr, new_text).map_err(|e| format!("{tag}: {e}"))?;
        obj.put(DataElement::new(tag, vr, new_value));
    } else if let NestedItem::PrivateTag(tag) = &item {
        let vr = resolve_vr(item.clone()).map_err(|e| format!("{tag}: {e}"))?;
        let new_value = validate_vr_value(vr, new_text).map_err(|e| format!("{tag}: {e}"))?;
        obj.put_private_element(tag.group, &tag.creator, tag.element, vr, new_value)?;
    }
    Ok(())
}

pub fn apply_increment_date(
    obj: &mut InMemDicomObject,
    item: NestedItem,
    increment: i64,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(tag) = resolve_tag(obj, item)? {
        let vr = match obj.element(tag) {
            Ok(el) => el.header().vr(),
            Err(_) => return Ok(()),
        };
        let value = get_dcm_value(&obj, tag).map_err(|e| format!("{tag}: {e}"))?;
        let inc_value = increment_date(vr.to_string(), &value.to_string(), increment);
        let new_value = validate_vr_value(vr, &inc_value).map_err(|e| format!("{tag}: {e}"))?;
        obj.put(DataElement::new(tag, vr, new_value));
    }
    Ok(())
}

pub fn apply_hash(
    obj: &mut InMemDicomObject,
    item: NestedItem,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(tag) = resolve_tag(obj, item)? {
        let vr = match obj.element(tag) {
            Ok(el) => el.header().vr(),
            Err(_) => return Ok(()),
        };
        let value = get_dcm_value(&obj, tag).map_err(|e| format!("{tag}: {e}"))?;
        let hashed_value = hash(&value.to_string(), Some("hex"));
        let new_value =
            validate_vr_value(vr, &hashed_value[..16]).map_err(|e| format!("{tag}: {e}"))?;
        obj.put(DataElement::new(tag, vr, new_value));
    }
    Ok(())
}

pub fn apply_hash_uid(
    obj: &mut InMemDicomObject,
    item: NestedItem,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(tag) = resolve_tag(obj, item)? {
        let vr = match obj.element(tag) {
            Ok(el) => el.header().vr(),
            Err(_) => return Ok(()),
        };
        let value = get_dcm_value(&obj, tag).map_err(|e| format!("{tag}: {e}"))?;
        let value_str = value.to_string();
        let hashed_value = hash_uid(&value_str);
        let new_value = validate_vr_value(vr, &hashed_value).map_err(|e| format!("{tag}: {e}"))?;
        obj.put(DataElement::new(tag, vr, new_value));
    }
    Ok(())
}

pub fn apply_jitter(
    obj: &mut InMemDicomObject,
    item: NestedItem,
    jitter_range: f64,
    jitter_type: &str,
    jitter_min: Option<f64>,
    jitter_max: Option<f64>,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(tag) = resolve_tag(obj, item)? {
        let vr = match obj.element(tag) {
            Ok(el) => el.header().vr(),
            Err(_) => return Ok(()),
        };
        let value = get_dcm_value(&obj, tag).map_err(|e| format!("{tag}: {e}"))?;
        let mut new_value = match value {
            DicomValue::Int(value) => jitter(
                value as f64,
                jitter_range,
                jitter_type,
                jitter_min,
                jitter_max,
            )?,
            DicomValue::Float(value) => {
                jitter(value, jitter_range, jitter_type, jitter_min, jitter_max)?
            }
            _ => return Err("Unsupported value type for jittering".into()),
        };
        match vr {
            VR::IS | VR::UL | VR::US => {
                if jitter_type == "float" {
                    new_value = new_value.floor();
                }
                let (min, max) = match vr {
                    VR::US => (0.0, (2u32.pow(16) - 1) as f64),
                    VR::UL => (0.0, (2u32.pow(32) - 1) as f64),
                    _ => (f64::MIN, f64::MAX),
                };
                new_value = new_value.clamp(min, max);
            }
            _ => {}
        }
        let formatted = match vr {
            VR::US | VR::UL | VR::IS => format!("{}", new_value as u64),
            VR::FL | VR::FD => format!("{}", new_value),
            _ => new_value.to_string(),
        };
        let new_value = validate_vr_value(vr, &formatted).map_err(|e| format!("{tag}: {e}"))?;
        obj.put(DataElement::new(tag, vr, new_value));
    }
    Ok(())
}

fn resolve_tag(
    obj: &InMemDicomObject,
    item: NestedItem,
) -> Result<Option<Tag>, Box<dyn std::error::Error>> {
    match item {
        NestedItem::Tag(tag) => Ok(Some(tag)),
        NestedItem::PrivateTag(tag) => {
            if let Ok(private_el) = obj.private_element(tag.group, &tag.creator, tag.element) {
                Ok(Some(private_el.tag()))
            } else {
                Ok(None)
            }
        }
        _ => Err("Nested item must be a tag".into()),
    }
}

fn resolve_vr(item: NestedItem) -> Result<VR, String> {
    match item {
        NestedItem::Tag(tag) => {
            if let Some(entry) = StandardDataDictionary.by_tag(tag) {
                let vvr = entry.vr();
                Ok(vvr.exact().unwrap_or_else(|| vvr.relaxed()))
            } else {
                Ok(VR::UN)
            }
        }
        NestedItem::PrivateTag(tag) => {
            match utils::get_private_tag_vr(tag.group, tag.element, &tag.creator) {
                Some(vr) => Ok(vr),
                _ => Err(format!("Could not resolve VR for private tag")),
            }
        }
        _ => Err("Item must be a tag".into()),
    }
}

fn validate_vr_value(vr: VR, value: &str) -> Result<PrimitiveValue, String> {
    if value.is_empty() {
        return Ok(PrimitiveValue::Empty);
    }

    match vr {
        VR::DA => {
            NaiveDate::parse_from_str(value, "%Y%m%d")
                .map_err(|_| format!("{value} cannot be parsed as DA"))?;
            Ok(PrimitiveValue::from(value.to_string()))
        }

        VR::TM => {
            let fmts = ["%H", "%H%M", "%H%M%S", "%H%M%S%.f"];
            if !fmts
                .iter()
                .any(|f| NaiveTime::parse_from_str(value, f).is_ok())
            {
                return Err(format!("{value} cannot be parsed as TM"));
            }
            Ok(PrimitiveValue::from(value.to_string()))
        }

        VR::DT => {
            let fmts = [
                "%Y%m%d%H%M%S",
                "%Y%m%d%H%M%S%.f",
                "%Y%m%d%H%M",
                "%Y%m%d%H",
                "%Y%m%d",
            ];
            if !fmts
                .iter()
                .any(|f| NaiveDateTime::parse_from_str(value, f).is_ok())
            {
                return Err(format!("{value} cannot be parsed as DT"));
            }
            Ok(PrimitiveValue::from(value.to_string()))
        }

        VR::DS => {
            let vals: Result<Vec<f64>, _> =
                value.split('\\').map(|v| v.trim().parse::<f64>()).collect();
            match vals {
                Ok(nums) => Ok(PrimitiveValue::F64(SmallVec::from_vec(nums))),
                Err(_) => Err(format!("{value} cannot be parsed as {vr:?}")),
            }
        }

        VR::FL => {
            let vals: Result<Vec<f32>, _> =
                value.split('\\').map(|v| v.trim().parse::<f32>()).collect();
            match vals {
                Ok(nums) => Ok(PrimitiveValue::F32(SmallVec::from_vec(nums))),
                Err(_) => Err(format!("{value} cannot be parsed as {vr:?}")),
            }
        }

        VR::FD => {
            let vals: Result<Vec<f64>, _> =
                value.split('\\').map(|v| v.trim().parse::<f64>()).collect();
            match vals {
                Ok(nums) => Ok(PrimitiveValue::F64(SmallVec::from_vec(nums))),
                Err(_) => Err(format!("{value} cannot be parsed as {vr:?}")),
            }
        }

        VR::IS => {
            let vals: Result<Vec<i64>, _> =
                value.split('\\').map(|v| v.trim().parse::<i64>()).collect();
            match vals {
                Ok(nums) => Ok(PrimitiveValue::I64(SmallVec::from_vec(nums))),
                Err(_) => Err(format!("{value} cannot be parsed as {vr:?}")),
            }
        }

        VR::UL => {
            let vals: Result<Vec<u32>, _> =
                value.split('\\').map(|v| v.trim().parse::<u32>()).collect();
            match vals {
                Ok(nums) => Ok(PrimitiveValue::U32(SmallVec::from_vec(nums))),
                Err(_) => Err(format!("{value} cannot be parsed as {vr:?}")),
            }
        }
        VR::SL => {
            let vals: Result<Vec<i32>, _> =
                value.split('\\').map(|v| v.trim().parse::<i32>()).collect();
            match vals {
                Ok(nums) => Ok(PrimitiveValue::I32(SmallVec::from_vec(nums))),
                Err(_) => Err(format!("{value} cannot be parsed as {vr:?}")),
            }
        }
        VR::SS => {
            let vals: Result<Vec<i16>, _> =
                value.split('\\').map(|v| v.trim().parse::<i16>()).collect();
            match vals {
                Ok(nums) => Ok(PrimitiveValue::I16(SmallVec::from_vec(nums))),
                Err(_) => Err(format!("{value} cannot be parsed as {vr:?}")),
            }
        }
        VR::US => {
            let vals: Result<Vec<u16>, _> =
                value.split('\\').map(|v| v.trim().parse::<u16>()).collect();
            match vals {
                Ok(nums) => Ok(PrimitiveValue::U16(SmallVec::from_vec(nums))),
                Err(_) => Err(format!("{value} cannot be parsed as {vr:?}")),
            }
        }

        _ => Ok(PrimitiveValue::from(value.to_string())),
    }
}

pub fn hash(message: &str, format: Option<&str>) -> String {
    let mut hasher = Sha256::new();
    hasher.update(message.as_bytes());
    let result = hasher.finalize();
    match format.unwrap_or("hex") {
        "dec" => result.iter().map(|b| b.to_string()).collect(),
        _ => hex::encode(result),
    }
}

const UID_PREFIX_FIELDS: usize = 4;
const UID_SUFFIX_FIELDS: usize = 1;
const UID_HASH_FIELDS: [usize; 6] = [6, 6, 6, 6, 6, 6];
const UID_MAX_SUFFIX_DIGITS: usize = 6;
const UID_MAX_LENGTH: usize = 64;

pub fn hash_uid(value: &str) -> String {
    let original_parts: Vec<&str> = value.split('.').collect();
    let decimal_digest = hash(value, Some("dec"));

    let mut result_parts: Vec<String> = original_parts
        .iter()
        .take(UID_PREFIX_FIELDS)
        .map(|s| s.to_string())
        .collect();

    let mut index = 0;
    for &segment_len in UID_HASH_FIELDS.iter() {
        let end = usize::min(index + segment_len, decimal_digest.len());
        result_parts.push(decimal_digest[index..end].to_string());
        index += segment_len;
    }

    if UID_SUFFIX_FIELDS > 0 {
        for part in original_parts.iter().rev().take(UID_SUFFIX_FIELDS).rev() {
            let part_len = usize::min(part.len(), UID_MAX_SUFFIX_DIGITS);
            result_parts.push(part[part.len() - part_len..].to_string());
        }
    }

    let mut new_value = result_parts.join(".");
    if new_value.len() > UID_MAX_LENGTH {
        let parts: Vec<String> = new_value.split('.').map(|s| s.to_string()).collect();
        let mut rest = parts[..parts.len() - 1].to_vec();
        let suffix = parts[parts.len() - 1].clone();

        while rest
            .iter()
            .chain(std::iter::once(&suffix))
            .map(|s| s.len() + 1)
            .sum::<usize>()
            - 1
            > UID_MAX_LENGTH
        {
            if let Some(last) = rest.last_mut() {
                if last.len() > 1 {
                    last.truncate(last.len() - 1);
                } else {
                    rest.pop();
                }
            } else {
                break;
            }
        }

        rest.push(suffix);
        new_value = rest.join(".");
    }

    new_value
}

fn increment_date(vr: &str, value: &str, increment: i64) -> String {
    if value.is_empty() {
        return value.to_string();
    }

    let Some(dt) = utils::parse_dicom_datetime(vr, value) else {
        return value.to_string();
    };
    let adjusted = dt + Duration::days(increment);
    let fmt = match vr {
        "DA" => "%Y%m%d",
        "TM" => {
            if value.len() <= 2 {
                "%H"
            } else if value.len() <= 4 {
                "%H%M"
            } else if value.len() <= 6 {
                "%H%M%S"
            } else {
                "%H%M%S%.f"
            }
        }
        "DT" => {
            if value.len() <= 8 {
                "%Y%m%d"
            } else if value.len() <= 10 {
                "%Y%m%d%H"
            } else if value.len() <= 12 {
                "%Y%m%d%H%M"
            } else if value.contains('.') {
                "%Y%m%d%H%M%S%.f"
            } else {
                "%Y%m%d%H%M%S"
            }
        }
        _ => "%Y%m%d",
    };

    if vr == "DT" {
        format!("{}{}", adjusted.format(fmt), adjusted.format("%z"))
    } else {
        adjusted.format(fmt).to_string()
    }
}

fn jitter(
    value: f64,
    jitter_range: f64,
    jitter_type: &str,
    jitter_min: Option<f64>,
    jitter_max: Option<f64>,
) -> Result<f64, String> {
    if jitter_range == 0.0 {
        return Err("jitter_range cannot be 0".to_string());
    }

    let mut rng = rand::rng();
    let rand_val: f64 = loop {
        let rv = if jitter_type == "int" {
            rng.random_range(-(jitter_range as i64)..=(jitter_range as i64)) as f64
        } else {
            rng.random_range(-1.0..=1.0) * jitter_range
        };
        if rv != 0.0 {
            break rv;
        }
    };

    let mut new_value = value + rand_val;

    if let Some(min) = jitter_min {
        if new_value < min {
            new_value = min;
        }
    }
    if let Some(max) = jitter_max {
        if new_value > max {
            new_value = max;
        }
    }

    Ok(new_value)
}

fn parse_da(value: &str) -> Option<NaiveDate> {
    NaiveDate::parse_from_str(value.trim(), "%Y%m%d").ok()
}

fn get_patient_age(
    birth_date: NaiveDate,
    experiment_date: NaiveDate,
    preferred_unit: Option<AgeUnit>,
) -> String {
    let days = (experiment_date - birth_date).num_days();

    if days < 1000
        && preferred_unit != Some(AgeUnit::Years)
        && preferred_unit != Some(AgeUnit::Months)
    {
        return format!("{:0>3}D", days);
    }

    // months: approximate by year*12 + month difference
    let months = (experiment_date.year() - birth_date.year()) * 12
        + (experiment_date.month() as i32 - birth_date.month() as i32);

    if months < 1000 && preferred_unit != Some(AgeUnit::Years) {
        return format!("{:0>3}M", months);
    }

    let years = experiment_date.year()
        - birth_date.year()
        - match (experiment_date.month(), experiment_date.day())
            .cmp(&(birth_date.month(), birth_date.day()))
        {
            Ordering::Less => 1,
            _ => 0,
        };

    format!("{:0>3}Y", years)
}

fn set_patient_age_from_birth_date(
    obj: &mut InMemDicomObject,
    unit: Option<AgeUnit>,
) -> Result<(), Box<dyn std::error::Error>> {
    let birth_date = obj
        .element(PATIENT_BIRTH_DATE)
        .ok()
        .and_then(|el| el.to_str().ok())
        .as_deref()
        .and_then(parse_da);
    let birth_date = match birth_date {
        Some(d) => d,
        None => return Ok(()),
    };
    let experiment_date = obj
        .element(STUDY_DATE)
        .ok()
        .and_then(|el| el.to_str().ok())
        .or_else(|| {
            obj.element(SERIES_DATE)
                .ok()
                .and_then(|el| el.to_str().ok())
        })
        .as_deref()
        .and_then(parse_da);
    let experiment_date = match experiment_date {
        Some(d) => d,
        None => return Ok(()),
    };
    let age_str = get_patient_age(birth_date, experiment_date, unit);
    obj.put_str(PATIENT_AGE, VR::AS, &age_str);
    Ok(())
}

#[derive(Debug, Clone)]
pub struct PrivateTag {
    group: u16,
    element: u8,
    creator: String,
}

impl PrivateTag {
    fn new(group: u16, element: u8, creator: String) -> Self {
        Self {
            group,
            element,
            creator,
        }
    }
}

impl fmt::Display for PrivateTag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "({:04X},xx{:02X}) \"{}\"",
            self.group, self.element, self.creator
        )
    }
}

#[derive(Debug, Clone)]
pub enum NestedItem {
    Tag(Tag),
    PrivateTag(PrivateTag),
    Index(usize),
    Wildcard,
}

fn parse_nested_field(name: &str) -> Result<Vec<NestedItem>, String> {
    let mut path = Vec::new();
    if let Some(captures) = utils::PRIVATE_TAG_RE.captures(name) {
        let group = u16::from_str_radix(captures.get(1).unwrap().as_str(), 16)
            .map_err(|e| format!("Invalid private tag group in {name}: {e}"))?;
        let creator = captures.get(2).unwrap().as_str().to_string();
        let element = u8::from_str_radix(captures.get(3).unwrap().as_str(), 16)
            .map_err(|e| format!("Invalid private tag element in {name}: {e}"))?;
        path.push(NestedItem::PrivateTag(PrivateTag::new(
            group, element, creator,
        )));
        return Ok(path);
    }

    for part in name.split('.') {
        if part == "*" {
            path.push(NestedItem::Wildcard);
        } else if part.starts_with("0x")
            || (part.len() == 8 && part.chars().all(|c| c.is_ascii_hexdigit()))
        {
            let raw = u32::from_str_radix(part.trim_start_matches("0x"), 16)
                .map_err(|e| format!("Invalid hex tag {part}: {e}"))?;
            let group = ((raw >> 16) & 0xFFFF) as u16;
            let element = (raw & 0xFFFF) as u16;
            path.push(NestedItem::Tag(Tag(group, element)));
        } else if let Ok(idx) = part.parse::<usize>() {
            path.push(NestedItem::Index(idx));
        } else {
            let tag = StandardDataDictionary
                .parse_tag(part)
                .ok_or_else(|| format!("Invalid tag name: {part}"))?;
            path.push(NestedItem::Tag(tag));
        }
    }

    Ok(path)
}

fn remove_undefined_fields(
    obj: &mut InMemDicomObject,
    allowed_paths: &[Vec<NestedItem>],
) -> Result<(), String> {
    let mut allowed_tags = std::collections::HashSet::new();
    for path in allowed_paths {
        if let Some(NestedItem::Tag(tag)) = path.first() {
            allowed_tags.insert(*tag);
        }
    }

    let tags_to_remove: Vec<Tag> = obj
        .clone()
        .into_iter()
        .map(|el| el.header().tag)
        .filter(|tag| !allowed_tags.contains(tag))
        .collect();

    for tag in tags_to_remove {
        obj.remove_element(tag);
    }

    Ok(())
}

pub fn remove_private_tags(obj: &mut InMemDicomObject, defined_private_tags: &[PrivateTag]) {
    let mut tags_to_remove = Vec::new();
    let mut updated_elements: Vec<InMemElement> = Vec::new();

    for elem in obj.iter() {
        let tag = elem.tag();

        if let dicom_core::DicomValue::Sequence(seq) = elem.value() {
            let mut new_items = Vec::new();

            for item in seq.items().iter() {
                let mut cloned = item.clone();
                remove_private_tags(&mut cloned, defined_private_tags);
                new_items.push(cloned);
            }

            updated_elements.push(DataElement::new(
                tag.clone(),
                VR::SQ,
                dicom_core::value::DataSetSequence::<InMemDicomObject>::new(
                    new_items,
                    dicom_core::Length::UNDEFINED,
                ),
            ));
        }

        if tag.0 % 2 == 1 {
            if (0x0010..=0x00FF).contains(&tag.1) {
                let creator = match elem.value().to_str() {
                    Ok(s) => s.to_string(),
                    Err(_) => String::new(),
                };
                let is_used = defined_private_tags
                    .iter()
                    .any(|pt| pt.group == tag.0 && pt.creator == creator);
                if !is_used {
                    tags_to_remove.push(tag);
                }
            } else {
                let is_defined = defined_private_tags.iter().any(|pt| {
                    if let Ok(element) = obj.private_element(pt.group, &pt.creator, pt.element) {
                        element.tag() == tag
                    } else {
                        false
                    }
                });
                if !is_defined {
                    tags_to_remove.push(tag);
                }
            }
        }
    }

    for updated in updated_elements {
        obj.put(updated);
    }
    for tag in tags_to_remove {
        obj.remove_element(tag);
    }
}

fn empty_array_to_string<'de, D>(deserializer: D) -> Result<Option<String>, D::Error>
where
    D: Deserializer<'de>,
{
    #[derive(Deserialize)]
    #[serde(untagged)]
    #[allow(dead_code)]
    enum StringOrArray {
        Str(String),
        Int(i64),
        Float(f64),
        Array(Vec<serde_yaml::Value>),
    }

    match StringOrArray::deserialize(deserializer)? {
        StringOrArray::Str(s) => Ok(Some(s)),
        StringOrArray::Int(i) => Ok(Some(i.to_string())),
        StringOrArray::Float(f) => Ok(Some(f.to_string())),
        StringOrArray::Array(_) => Ok(Some("".to_string())),
    }
}
