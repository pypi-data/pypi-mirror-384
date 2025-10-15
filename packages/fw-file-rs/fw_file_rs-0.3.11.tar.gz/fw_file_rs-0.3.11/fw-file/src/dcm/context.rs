use std::collections::HashMap;
use std::fs::File;

use crate::dcm::{
    DCMGroup, DeidProfile, DicomValue, get_fw_meta, group_series, parse_header, read_until_pixels,
};

/// Context struct for configuring DICOM operations with a builder pattern
#[derive(Debug, Clone)]
pub struct Context {
    stop_tags: Vec<(u16, u16)>,
    max_size: Option<usize>,
    include_tags: Vec<String>,
    group_by_tags: Vec<String>,
    split_localizer_flag: bool,
    mappings: Vec<String>,
    deid_profile: Option<DeidProfile>,
}

impl Context {
    /// Create a new Context with default values
    pub fn new() -> Self {
        Self {
            stop_tags: Vec::new(),
            max_size: None,
            include_tags: Vec::new(),
            group_by_tags: Vec::new(),
            split_localizer_flag: true,
            mappings: Vec::new(),
            deid_profile: None,
        }
    }

    /// Set stop tags for read_until_pixels operation
    pub fn stop_at_tags<T: Into<Vec<(u16, u16)>>>(mut self, tags: T) -> Self {
        self.stop_tags = tags.into();
        self
    }

    pub fn get_stop_tags(&self) -> &Vec<(u16, u16)> {
        &self.stop_tags
    }

    /// Set maximum file size for read_until_pixels operation
    pub fn max_size(mut self, size: usize) -> Self {
        self.max_size = Some(size);
        self
    }

    pub fn get_max_size(&self) -> Option<usize> {
        self.max_size
    }

    /// Set tags to include in parse_header operation
    pub fn include_tags<T: IntoIterator<Item = S>, S: Into<String>>(mut self, tags: T) -> Self {
        self.include_tags = tags.into_iter().map(|s| s.into()).collect();
        self
    }

    /// Set tags to group by in group_series operation
    pub fn group_by_tags<T: IntoIterator<Item = S>, S: Into<String>>(mut self, tags: T) -> Self {
        self.group_by_tags = tags.into_iter().map(|s| s.into()).collect();
        self
    }

    /// Set split localizer flag for group_series operation
    pub fn split_localizer(mut self, flag: bool) -> Self {
        self.split_localizer_flag = flag;
        self
    }

    /// Set mappings for get_fw_meta operation
    pub fn mappings<T: IntoIterator<Item = S>, S: Into<String>>(mut self, mappings: T) -> Self {
        self.mappings = mappings.into_iter().map(|s| s.into()).collect();
        self
    }

    /// Set de-identification profile from YAML string
    pub fn deid_profile(mut self, yaml: &str) -> Result<Self, String> {
        use crate::dcm::ProfileParseError;

        let profile = DeidProfile::from_yaml(yaml).map_err(|e| match e {
            ProfileParseError::YamlError(msg) => format!("YAML parse error: {}", msg),
            ProfileParseError::ValidationError(errs) => format!("Validation errors: {:?}", errs),
            ProfileParseError::UnsupportedVersion(v) => {
                format!("Unsupported profile version: {}", v)
            }
        })?;

        self.deid_profile = Some(profile);
        Ok(self)
    }

    /// Read file until pixel data using configured stop tags
    pub fn read_until_pixels(&self, file: &mut File) -> Result<Vec<u8>, String> {
        read_until_pixels(file, &self.stop_tags, self.max_size)
    }

    /// Parse DICOM header using configured include tags
    pub fn parse_header(&self, bytes: &[u8]) -> Result<HashMap<String, DicomValue>, String> {
        let include_refs: Vec<&str> = self.include_tags.iter().map(|s| s.as_str()).collect();
        parse_header(bytes, &include_refs)
    }

    /// Group series using configured group-by tags and split localizer flag
    pub fn group_series(
        &self,
        path_header_pairs: &[(String, HashMap<String, DicomValue>)],
    ) -> Vec<DCMGroup> {
        let group_by_tags: Vec<&str> = self.group_by_tags.iter().map(|s| s.as_str()).collect();
        group_series(
            path_header_pairs,
            Some(&group_by_tags),
            self.split_localizer_flag,
        )
    }

    /// Get Flywheel metadata using configured mappings
    pub fn get_fw_meta(
        &self,
        header: HashMap<String, DicomValue>,
    ) -> Result<HashMap<String, String>, String> {
        let mapping_refs: Vec<&str> = self.mappings.iter().map(|s| s.as_str()).collect();
        get_fw_meta(header, &mapping_refs)
    }

    /// De-identify DICOM header using configured de-identification profile
    pub fn deid_header(&self, bytes: &[u8]) -> Result<Vec<u8>, String> {
        match &self.deid_profile {
            Some(profile) => profile.deid_dcm(bytes),
            None => Err("No de-identification profile configured".to_string()),
        }
    }
}

impl Default for Context {
    fn default() -> Self {
        Self::new()
    }
}
