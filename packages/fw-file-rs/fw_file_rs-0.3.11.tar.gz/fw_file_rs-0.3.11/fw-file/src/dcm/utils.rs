use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::io::{self, Read, Seek, SeekFrom};
use std::io::{Cursor, Error, ErrorKind, Result as IOResult, Write};

use chrono::{DateTime, FixedOffset, NaiveDate, NaiveDateTime, NaiveTime, TimeZone};
use dicom_core::header::SequenceItemHeader;
use dicom_core::header::{DataElement, Header};
use dicom_core::value::PrimitiveValue;
use dicom_core::{DataDictionary, Tag, VR};
use dicom_dictionary_std::StandardDataDictionary;
use dicom_encoding::transfer_syntax::TransferSyntaxIndex;
use dicom_object::FileMetaTableBuilder;
use dicom_object::InMemDicomObject;
use dicom_parser::{DynStatefulDecoder, StatefulDecode};
use dicom_transfer_syntax_registry::TransferSyntaxRegistry;
use dicom_transfer_syntax_registry::entries::{
    EXPLICIT_VR_LITTLE_ENDIAN, IMPLICIT_VR_LITTLE_ENDIAN,
};
use once_cell::sync::Lazy;
use regex::Regex;
use smallvec::SmallVec;

pub static REPEATER_TUPLE_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"\(\s*([56]0[Xx]{2})\s*,\s*([0-9A-Fa-f]{4})\s*\)").unwrap());
pub static REPEATER_HEX_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^(?:0x)?([56]0[Xx]{2}[0-9A-Fa-f]{4})$").unwrap());
pub static PRIVATE_TAG_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r#"^\(\s*([0-9A-Fa-f]{4})\s*,\s*"?([^\\\"()]{1,64})"?\s*,\s*([0-9A-Fa-f]{2})\s*\)$"#)
        .unwrap()
});

pub static STOP_TAGS: &[(u16, u16)] = &[
    (0x7FE0, 0x0008),
    (0x7FE0, 0x0009),
    (0x7FE0, 0x0010),
    (0x0067, 0x1018),
];

pub fn read_until_pixels(
    file: &mut File,
    stop_tags: &[(u16, u16)],
    max_size: Option<usize>,
) -> Result<Vec<u8>, String> {
    let file_size = file
        .metadata()
        .map_err(|e| format!("Failed to get file metadata: {}", e))?
        .len();

    let absolute_max = max_size.unwrap_or(50_000_000);
    let initial_chunk_size = 5_000_000.min(file_size as usize).min(absolute_max);
    let mut current_chunk_size = initial_chunk_size;

    let mut stop_tag_set = HashSet::new();
    for &(group, element) in stop_tags {
        stop_tag_set.insert(Tag(group, element));
    }
    for &(group, element) in STOP_TAGS {
        stop_tag_set.insert(Tag(group, element));
    }

    loop {
        file.seek(SeekFrom::Start(0))
            .map_err(|e| format!("Failed to seek to start: {e}"))?;

        let mut chunk_data = vec![0u8; current_chunk_size];
        let bytes_read = file
            .read(&mut chunk_data)
            .map_err(|e| format!("Failed to read file: {e}"))?;
        chunk_data.truncate(bytes_read);

        match parse_dicom_until_stop_tags(&chunk_data, file_size, &stop_tag_set) {
            Ok(end_pos) => {
                let result = &chunk_data[..end_pos as usize];
                return Ok(result.to_vec());
            }
            Err(e) if e.contains("Need more data") => {
                if current_chunk_size >= absolute_max {
                    return Err(format!(
                        "Could not find stop tags within max_size limit of {absolute_max} bytes. \
                        Consider increasing max_size or checking if this is a valid DICOM file."
                    ));
                }

                if current_chunk_size >= file_size as usize {
                    return Ok(chunk_data);
                }

                current_chunk_size = (current_chunk_size * 2)
                    .min(file_size as usize)
                    .min(absolute_max);
                continue;
            }
            Err(e) => {
                return Err(e);
            }
        }
    }
}

/// Validates that data at the start looks like raw DICOM format
fn validate_raw_dicom_start(data: &[u8]) -> bool {
    if data.len() < 8 {
        return false;
    }

    // Try to read first tag - should be a group/element pair
    let group = u16::from_le_bytes([data[0], data[1]]);
    let _element = u16::from_le_bytes([data[2], data[3]]);

    // Valid DICOM groups: 0002, 0008, 0010, 0018, 0020, 0028, etc.
    // Group 0000 is command group (not in files), groups > 0xFFEF are invalid
    if group == 0 || group > 0xFFEF {
        return false;
    }

    // Most DICOM files start with group 0008 (Identifying Information)
    // or group 0002 (File Meta Information)
    let is_common_start_group =
        matches!(group, 0x0002 | 0x0008 | 0x0010 | 0x0018 | 0x0020 | 0x0028);

    // Try detecting format: Explicit VR or Implicit VR
    // In Explicit VR: Tag (4 bytes) + VR (2 bytes) + Length (2 or 6 bytes)
    // In Implicit VR: Tag (4 bytes) + Length (4 bytes)

    if data.len() >= 6 {
        let vr_bytes = [data[4], data[5]];

        // Check if bytes 4-5 are a valid standard DICOM VR (Explicit VR format)
        if VR::from_binary(vr_bytes).is_some() {
            // Valid VR found - likely Explicit VR format
            return true;
        }

        // If not Explicit VR, check if it could be Implicit VR
        // In Implicit VR, bytes 4-7 are the length (32-bit little endian)
        if data.len() >= 8 {
            let length = u32::from_le_bytes([data[4], data[5], data[6], data[7]]);

            // Sanity check: length should be reasonable (not too large)
            // and if it's a common starting group, more likely to be valid
            if length < 10000 && is_common_start_group {
                return true;
            }

            // For other groups, be more conservative
            if length < 1000 {
                return true;
            }
        }
    }

    false
}

pub fn parse_dicom_until_stop_tags(
    data: &[u8],
    _file_size: u64,
    stop_tag_set: &std::collections::HashSet<Tag>,
) -> Result<u64, String> {
    let mut buffer = Cursor::new(data);

    buffer
        .seek(SeekFrom::Start(0))
        .map_err(|e| format!("Failed to seek to start: {e}"))?;

    // Check if file has DICOM Part 10 preamble and DICM prefix
    let has_dicm_prefix = if data.len() >= 132 {
        &data[128..132] == b"DICM"
    } else {
        false
    };

    let (ts, dataset_start_pos) = if has_dicm_prefix {
        // DICOM Part 10 format: read preamble, DICM prefix, and file meta information
        let mut preamble = vec![0u8; 128];
        buffer
            .read_exact(&mut preamble)
            .map_err(|e| format!("Failed to read preamble: {e}"))?;

        let mut prefix = [0u8; 4];
        buffer
            .read_exact(&mut prefix)
            .map_err(|e| format!("Failed to read DICM prefix: {e}"))?;

        // Parse file meta information to get transfer syntax and end position
        let (ts_uid, meta_end_pos) = parse_file_meta_and_get_ts_with_position(&mut buffer)
            .map_err(|e| format!("Failed to parse file meta information: {e}"))?;

        let ts = TransferSyntaxRegistry
            .get(&ts_uid)
            .ok_or_else(|| format!("Unsupported transfer syntax: {ts_uid}"))?;

        (ts, meta_end_pos)
    } else {
        if !validate_raw_dicom_start(data) {
            return Err("File does not appear to be valid DICOM format (missing DICM prefix and invalid tag structure)".to_string());
        }

        // Detect if it's Explicit or Implicit VR by checking if bytes 4-5 are a valid DICOM VR
        let vr_bytes = [data[4], data[5]];
        let looks_like_explicit_vr = VR::from_binary(vr_bytes).is_some();

        if looks_like_explicit_vr {
            (&EXPLICIT_VR_LITTLE_ENDIAN.erased(), 0u64)
        } else {
            (&IMPLICIT_VR_LITTLE_ENDIAN.erased(), 0u64)
        }
    };

    // Position to start of dataset and find stop position
    buffer
        .seek(SeekFrom::Start(dataset_start_pos))
        .map_err(|e| format!("Failed to seek to dataset start: {e}"))?;

    // Create StatefulDecoder to track position
    let mut decoder = DynStatefulDecoder::new_with_ts(&mut buffer, ts, dataset_start_pos)
        .map_err(|e| format!("Failed to create decoder: {e}"))?;

    let mut sequence_depth = 0u32;
    let mut in_undefined_item = false;

    // Parse until we hit a stop tag or run out of data
    loop {
        // If we're in a sequence, check for item/delimiter headers
        if sequence_depth > 0 && !in_undefined_item {
            match decoder.decode_item_header() {
                Ok(header) => {
                    match header {
                        SequenceItemHeader::Item { len } => {
                            if len.0 != 0xFFFFFFFF {
                                // Defined length item - skip it
                                decoder
                                    .skip_bytes(len.0)
                                    .map_err(|e| format!("Failed to skip item: {e}"))?;
                            } else {
                                in_undefined_item = true;
                            }
                            continue;
                        }
                        SequenceItemHeader::ItemDelimiter => {
                            continue;
                        }
                        SequenceItemHeader::SequenceDelimiter => {
                            sequence_depth = sequence_depth.saturating_sub(1);
                            continue;
                        }
                    }
                }
                Err(_) => {} // Not an item header, try as element header
            }
        }

        // Capture position before decoding the header
        let pos_before_header = decoder.position();

        // Decode the next element header
        match decoder.decode_header() {
            Ok(header) => {
                // Check for item delimiter or sequence delimiter
                if header.tag.0 == 0xFFFE {
                    if header.tag.1 == 0xE00D {
                        // ItemDelimiter
                        in_undefined_item = false;
                        continue;
                    } else if header.tag.1 == 0xE0DD {
                        // SequenceDelimiter
                        in_undefined_item = false;
                        sequence_depth = sequence_depth.saturating_sub(1);
                        continue;
                    }
                }

                // Check if this is a stop tag
                if stop_tag_set.contains(&header.tag) {
                    // Return position before this tag's header
                    return Ok(pos_before_header);
                }

                if header.vr == VR::SQ {
                    if header.len.0 == 0xFFFFFFFF {
                        sequence_depth += 1;
                        in_undefined_item = false;
                    } else {
                        // Skip defined length sequence
                        decoder
                            .skip_bytes(header.len.0)
                            .map_err(|e| format!("Failed to skip sequence: {e}"))?;
                    }
                } else if header.len.0 != 0xFFFFFFFF {
                    // Skip value data
                    decoder
                        .skip_bytes(header.len.0)
                        .map_err(|e| format!("Failed to skip value: {e}"))?;
                }
            }
            Err(e) => {
                // Check if we ran out of data
                if e.to_string().contains("UnexpectedEndOfElement")
                    || e.to_string().contains("EOF")
                    || decoder.position() >= data.len() as u64
                {
                    return Err("Need more data".to_string());
                }
                return Err(format!("Failed to decode header: {e}"));
            }
        }
    }
}

pub fn parse_file_meta_and_get_ts_with_position<R: Read + Seek>(
    reader: &mut R,
) -> io::Result<(String, u64)> {
    // Seek past preamble and DICM
    reader.seek(SeekFrom::Start(132))?;

    // Use the consolidated function to parse file meta
    let meta =
        parse_file_meta_group(reader).map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;

    // Get the transfer syntax UID
    let ts_uid = meta.transfer_syntax().to_string();

    // Get the current position (should be right after file meta)
    let end_pos = reader.stream_position()?;

    Ok((ts_uid, end_pos))
}

pub fn detect_transfer_syntax(meta: &[u8]) -> io::Result<String> {
    let ts_tag = [0x02, 0x00, 0x10, 0x00];
    if let Some(pos) = meta.windows(4).position(|w| w == ts_tag) {
        let len_pos = pos + 6;
        let len = u16::from_le_bytes([meta[len_pos], meta[len_pos + 1]]) as usize;
        let value_pos = len_pos + 2;
        if value_pos + len <= meta.len() {
            let raw_uid = &meta[value_pos..value_pos + len];
            return Ok(String::from_utf8_lossy(raw_uid)
                .trim_end_matches('\0')
                .to_string());
        }
    }
    Err(io::Error::new(
        io::ErrorKind::Other,
        "Could not detect Transfer Syntax UID",
    ))
}

/// Custom from_reader implementation that handles both DICOM Part 10 (with preamble)
/// and raw DICOM (without preamble) formats
pub fn from_reader_flexible<R: Read + Seek>(
    mut reader: R,
) -> Result<dicom_object::DefaultDicomObject, String> {
    use dicom_object::{FileDicomObject, from_reader};

    // Check if file has DICOM Part 10 preamble and DICM prefix
    let mut preamble_check = [0u8; 132];
    reader
        .read_exact(&mut preamble_check)
        .map_err(|e| format!("Failed to read file header: {e}"))?;

    let has_dicm_prefix = &preamble_check[128..132] == b"DICM";

    // Seek back to start
    reader
        .seek(SeekFrom::Start(0))
        .map_err(|e| format!("Failed to seek to start: {e}"))?;

    if has_dicm_prefix {
        // Standard DICOM Part 10 format - use standard parser
        match from_reader(&mut reader) {
            Ok(obj) => Ok(obj),
            Err(_e) => {
                // Standard parsing failed, try to parse file meta and dataset separately
                reader
                    .seek(SeekFrom::Start(132))
                    .map_err(|e| format!("Failed to seek past DICM preamble: {e}"))?;

                let meta = match parse_file_meta_group(&mut reader) {
                    Ok(meta) => meta,
                    Err(_meta_err) => {
                        // Reset and create minimal meta
                        reader
                            .seek(SeekFrom::Start(132))
                            .map_err(|e| format!("Failed to seek past DICM preamble: {e}"))?;
                        FileMetaTableBuilder::new()
                            .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
                            .build()
                            .map_err(|e| format!("Failed to build meta: {e}"))?
                    }
                };

                // Determine transfer syntax from meta or try to detect it
                let ts_uid = meta.transfer_syntax();
                let ts = TransferSyntaxRegistry
                    .get(ts_uid)
                    .ok_or_else(|| format!("Unknown transfer syntax: {ts_uid}"))?;

                // Parse the dataset with the detected transfer syntax
                let (dataset, element_count) = try_parse_raw_dicom(&mut reader, &ts)
                    .map_err(|parse_err| format!("Failed to parse dataset: {parse_err}"))?;

                if element_count == 0 {
                    return Err("No elements found in dataset".to_string());
                }

                let mut file_obj =
                    FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
                *file_obj = dataset;
                Ok(file_obj)
            }
        }
    } else {
        if !validate_raw_dicom_start(&preamble_check[..std::cmp::min(preamble_check.len(), 132)]) {
            return Err("File does not appear to be valid DICOM format (missing DICM prefix and invalid tag structure)".to_string());
        }

        // Try implicit VR first, then fall back to explicit VR if that fails
        let implicit_ts = IMPLICIT_VR_LITTLE_ENDIAN.erased();
        match try_parse_raw_dicom(&mut reader, &implicit_ts) {
            Ok((dataset, element_count)) if element_count > 0 => {
                // Create minimal file meta for raw DICOM
                let meta = FileMetaTableBuilder::new()
                    .transfer_syntax(IMPLICIT_VR_LITTLE_ENDIAN.uid())
                    .build()
                    .map_err(|e| format!("Failed to build meta: {e}"))?;

                let mut file_obj =
                    FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
                *file_obj = dataset;
                Ok(file_obj)
            }
            _ => {
                // Reset reader to start and try explicit VR
                reader
                    .seek(SeekFrom::Start(0))
                    .map_err(|e| format!("Failed to seek to start: {e}"))?;

                let explicit_ts = EXPLICIT_VR_LITTLE_ENDIAN.erased();
                let (dataset, _) = try_parse_raw_dicom(&mut reader, &explicit_ts).map_err(|e| {
                    format!("Failed to parse with both Implicit and Explicit VR: {e}")
                })?;

                // Create minimal file meta for raw DICOM
                let meta = FileMetaTableBuilder::new()
                    .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
                    .build()
                    .map_err(|e| format!("Failed to build meta: {e}"))?;

                let mut file_obj =
                    FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
                *file_obj = dataset;
                Ok(file_obj)
            }
        }
    }
}

fn parse_file_meta_group<R: Read + Seek>(
    reader: &mut R,
) -> Result<dicom_object::FileMetaTable, String> {
    // File meta is always Explicit VR Little Endian
    let ts = EXPLICIT_VR_LITTLE_ENDIAN.erased();
    let start_pos = reader
        .stream_position()
        .map_err(|e| format!("Failed to get position: {e}"))?;

    let mut decoder = DynStatefulDecoder::new_with_ts(&mut *reader, &ts, start_pos)
        .map_err(|e| format!("Failed to create decoder: {e}"))?;

    let mut builder = FileMetaTableBuilder::new();
    let mut has_transfer_syntax = false;
    let mut dataset_start_pos = None;

    loop {
        // Save position before reading header
        let pos_before_header = decoder.position();

        match decoder.decode_header() {
            Ok(header) => {
                // Stop when we leave group 0002
                if header.tag.0 != 0x0002 {
                    // Save the position where dataset starts (before this non-0x0002 tag)
                    dataset_start_pos = Some(pos_before_header);
                    break;
                }

                // Read the value for this header
                match decoder.read_value(&header) {
                    Ok(value) => {
                        let value_bytes = value.to_bytes();

                        match header.tag.1 {
                            0x0002 => {
                                // Media Storage SOP Class UID
                                if let Ok(uid) = std::str::from_utf8(&value_bytes) {
                                    builder = builder.media_storage_sop_class_uid(
                                        uid.trim_end_matches('\0').trim(),
                                    );
                                }
                            }
                            0x0003 => {
                                // Media Storage SOP Instance UID
                                if let Ok(uid) = std::str::from_utf8(&value_bytes) {
                                    builder = builder.media_storage_sop_instance_uid(
                                        uid.trim_end_matches('\0').trim(),
                                    );
                                }
                            }
                            0x0010 => {
                                // Transfer Syntax UID
                                if let Ok(uid) = std::str::from_utf8(&value_bytes) {
                                    builder =
                                        builder.transfer_syntax(uid.trim_end_matches('\0').trim());
                                    has_transfer_syntax = true;
                                }
                            }
                            0x0012 => {
                                // Implementation Class UID
                                if let Ok(uid) = std::str::from_utf8(&value_bytes) {
                                    builder = builder.implementation_class_uid(
                                        uid.trim_end_matches('\0').trim(),
                                    );
                                }
                            }
                            0x0013 => {
                                // Implementation Version Name
                                if let Ok(name) = std::str::from_utf8(&value_bytes) {
                                    builder = builder.implementation_version_name(
                                        name.trim_end_matches('\0').trim(),
                                    );
                                }
                            }
                            _ => {
                                // Skip other meta elements
                            }
                        }
                    }
                    Err(_) => {
                        // If we can't read the value, try to skip it and continue
                        if header.len.0 != 0xFFFFFFFF {
                            decoder.skip_bytes(header.len.0).ok();
                        }
                    }
                }
            }
            Err(_) => {
                break;
            }
        }
    }

    // Drop the decoder to release the reader
    drop(decoder);

    // Seek to the dataset start position if we have it
    if let Some(pos) = dataset_start_pos {
        reader
            .seek(SeekFrom::Start(pos))
            .map_err(|e| format!("Failed to seek to dataset start: {e}"))?;
    }

    // Ensure we have at least a transfer syntax
    if !has_transfer_syntax {
        builder = builder.transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid());
    }

    builder
        .build()
        .map_err(|e| format!("Failed to build FileMetaTable: {e}"))
}

fn try_parse_raw_dicom<R: Read + Seek>(
    reader: &mut R,
    ts: &dicom_encoding::transfer_syntax::TransferSyntax,
) -> Result<(InMemDicomObject, usize), String> {
    let start_pos = reader
        .stream_position()
        .map_err(|e| format!("Failed to get position: {e}"))?;
    let mut decoder = DynStatefulDecoder::new_with_ts(reader, ts, start_pos)
        .map_err(|e| format!("Failed to create decoder: {e}"))?;

    let mut dataset = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    let mut element_count = 0;

    loop {
        match decoder.decode_header() {
            Ok(header) => {
                // Skip sequences and handle special VRs
                if header.vr == VR::SQ {
                    // For sequences with defined length, skip the bytes
                    if header.len.0 != 0xFFFFFFFF {
                        decoder
                            .skip_bytes(header.len.0)
                            .map_err(|e| format!("Failed to skip sequence: {e}"))?;
                    }
                    // Skip undefined length sequences - they'll be handled by item delimiters
                    continue;
                }

                // Read the value for this header
                match decoder.read_value(&header) {
                    Ok(value) => {
                        let element = DataElement::new(header.tag, header.vr, value);
                        dataset.put(element);
                        element_count += 1;
                    }
                    Err(_) => {
                        // If we can't read the value, try to skip it and continue
                        if header.len.0 != 0xFFFFFFFF {
                            decoder.skip_bytes(header.len.0).ok();
                        }
                        // Continue parsing instead of failing
                    }
                }
            }
            Err(_) => {
                // End of data
                break;
            }
        }
    }

    Ok((dataset, element_count))
}

pub enum CreateDicomValue {
    Primitive(PrimitiveValue),
    PrimitiveAndVR(PrimitiveValue, VR),
    Sequence(Vec<HashMap<&'static str, CreateDicomValue>>),
}

macro_rules! impl_from_primitive {
    ($($t:ty),*) => {
        $(
            impl From<$t> for CreateDicomValue {
                fn from(value: $t) -> Self {
                    CreateDicomValue::Primitive(PrimitiveValue::from(value))
                }
            }
        )*
    };
}

impl_from_primitive!(&str, String, i64, f64);

impl From<Vec<i64>> for CreateDicomValue {
    fn from(v: Vec<i64>) -> Self {
        CreateDicomValue::Primitive(PrimitiveValue::I64(SmallVec::from_slice(&v)))
    }
}

impl From<Vec<f64>> for CreateDicomValue {
    fn from(v: Vec<f64>) -> Self {
        CreateDicomValue::Primitive(PrimitiveValue::F64(SmallVec::from_slice(&v)))
    }
}

impl From<Vec<String>> for CreateDicomValue {
    fn from(v: Vec<String>) -> Self {
        CreateDicomValue::Primitive(PrimitiveValue::Strs(SmallVec::from_vec(v)))
    }
}

impl From<Vec<HashMap<&'static str, CreateDicomValue>>> for CreateDicomValue {
    fn from(items: Vec<HashMap<&'static str, CreateDicomValue>>) -> Self {
        CreateDicomValue::Sequence(items)
    }
}

pub fn create_dcm_as_bytes(tags: HashMap<&str, CreateDicomValue>) -> IOResult<Cursor<Vec<u8>>> {
    let mut obj = InMemDicomObject::new_empty();
    insert_tags(&mut obj, tags)?;

    let ts = EXPLICIT_VR_LITTLE_ENDIAN.erased();
    let file_meta = FileMetaTableBuilder::new()
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.2")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8.9")
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .implementation_class_uid("1.2.3.4.5.6.7.8.9.10")
        .build()
        .map_err(|e| Error::new(ErrorKind::Other, e.to_string()))?;

    let mut buffer = Cursor::new(Vec::new());
    buffer.write_all(&[0u8; 128])?;
    buffer.write_all(b"DICM")?;
    file_meta
        .write(&mut buffer)
        .map_err(|e| Error::new(ErrorKind::Other, e.to_string()))?;

    obj.write_dataset_with_ts(&mut buffer, &ts)
        .map_err(|e| Error::new(ErrorKind::Other, format!("Write error: {e}")))?;

    buffer.set_position(0);
    Ok(buffer)
}

fn insert_tags(obj: &mut InMemDicomObject, tags: HashMap<&str, CreateDicomValue>) -> IOResult<()> {
    for (tag_name, value) in tags {
        let tag = StandardDataDictionary
            .parse_tag(tag_name)
            .ok_or_else(|| Error::new(ErrorKind::Other, format!("Invalid tag: {}", tag_name)))?;

        match value {
            CreateDicomValue::Primitive(pv) => {
                let vr = StandardDataDictionary
                    .by_tag(tag)
                    .map(|entry| entry.vr)
                    .unwrap_or(dicom_core::dictionary::VirtualVr::Exact(VR::UN));
                let vr = match vr {
                    dicom_core::dictionary::VirtualVr::Exact(vr) => vr,
                    _ => VR::UN,
                };
                obj.put(DataElement::new(tag, vr, dicom_core::DicomValue::from(pv)));
            }
            CreateDicomValue::PrimitiveAndVR(pv, vr) => {
                obj.put(DataElement::new(tag, vr, dicom_core::DicomValue::from(pv)));
            }
            CreateDicomValue::Sequence(items) => {
                let mut seq_items = Vec::new();
                for item_map in items {
                    let mut item_obj = InMemDicomObject::new_empty();
                    insert_tags(&mut item_obj, item_map)?;
                    seq_items.push(item_obj);
                }
                obj.put(DataElement::new(
                    tag,
                    VR::SQ,
                    dicom_core::value::DataSetSequence::<InMemDicomObject>::new(
                        seq_items,
                        dicom_core::Length::UNDEFINED,
                    ),
                ));
            }
        }
    }
    Ok(())
}

pub fn make_tag_patterns(tag: (u16, u16)) -> ([u8; 4], [u8; 4]) {
    let (group, element) = tag;
    let g_le = group.to_le_bytes();
    let e_le = element.to_le_bytes();
    let le = [g_le[0], g_le[1], e_le[0], e_le[1]];
    let g_be = group.to_be_bytes();
    let e_be = element.to_be_bytes();
    let be = [g_be[0], g_be[1], e_be[0], e_be[1]];
    (le, be)
}

pub fn find_any_tag_in_buffer(buf: &[u8], patterns: &[[u8; 4]]) -> Option<usize> {
    for pattern in patterns {
        if let Some(pos) = buf.windows(4).position(|w| w == pattern) {
            return Some(pos);
        }
    }
    None
}

fn candidate_formats(vr: &str) -> &'static [&'static str] {
    match vr {
        "DA" => &["%Y%m%d"],

        "TM" => &["%H", "%H%M", "%H%M%S", "%H%M%S%.f"],

        "DT" => &[
            "%Y%m%d%H%M%S",
            "%Y%m%d%H%M%S%.f",
            "%Y%m%d%H%M",
            "%Y%m%d%H",
            "%Y%m%d",
        ],

        _ => &["%Y%m%d"],
    }
}

pub fn parse_dicom_datetime(vr: &str, value: &str) -> Option<DateTime<FixedOffset>> {
    let (core_val, tz) = {
        let mut core_val = value;
        if value.len() > 5 {
            let suffix = &value[value.len() - 5..];
            if suffix.starts_with('+') || suffix.starts_with('-') {
                core_val = &value[..value.len() - 5];
            }
        }
        (core_val, get_offset(value))
    };

    let naive = candidate_formats(vr).iter().find_map(|fmt| {
        if let Ok(dt) = NaiveDateTime::parse_from_str(core_val, fmt) {
            return Some(dt);
        }

        if *fmt == "%Y%m%d" {
            if let Ok(d) = NaiveDate::parse_from_str(core_val, fmt) {
                return d.and_hms_opt(0, 0, 0);
            }
        }

        if vr == "TM" {
            if let Ok(t) = NaiveTime::parse_from_str(core_val, fmt) {
                if let Some(d) = NaiveDate::from_ymd_opt(1970, 1, 1) {
                    return Some(NaiveDateTime::new(d, t));
                }
            }
        }

        None
    });

    let naive = match naive {
        Some(naive) => naive,
        None => return None,
    };

    match tz.from_local_datetime(&naive).single() {
        Some(dt) => Some(dt),
        None => match tz
            .timestamp_opt(
                naive.and_utc().timestamp(),
                naive.and_utc().timestamp_subsec_nanos(),
            )
            .single()
        {
            Some(dt) => Some(dt),
            None => None,
        },
    }
}

pub fn get_offset(val: &str) -> FixedOffset {
    let utc = FixedOffset::west_opt(0).unwrap();
    if val.len() >= 5 {
        let suffix = &val[val.len() - 5..];
        if let Some(sign) = suffix.chars().next() {
            if sign == '+' || sign == '-' {
                if let Ok(hours) = suffix[1..3].parse::<i32>() {
                    if let Ok(minutes) = suffix[3..5].parse::<i32>() {
                        let offset_secs = hours * 3600 + minutes * 60;
                        return if sign == '-' {
                            FixedOffset::west_opt(offset_secs).unwrap_or(utc)
                        } else {
                            FixedOffset::east_opt(offset_secs).unwrap_or(utc)
                        };
                    }
                }
            }
        }
    }
    utc
}

pub fn get_dicom_data_elements_keyword_path(dcm: &InMemDicomObject) -> Vec<String> {
    let mut dotty_attrs: Vec<String> = Vec::new();
    let dict = StandardDataDictionary;

    let mut elements_with_keywords: Vec<(&str, &DataElement<InMemDicomObject>)> = dcm
        .iter()
        .filter_map(|elem| dict.by_tag(elem.tag()).map(|entry| (entry.alias, elem)))
        .collect();

    elements_with_keywords.sort_by_key(|(kw, _)| *kw);

    for (keyword, data_element) in elements_with_keywords {
        if data_element.vr() == VR::SQ {
            if let dicom_core::DicomValue::Sequence(sequence) = data_element.value() {
                dotty_attrs.push(keyword.to_string());

                for (i, dataset) in sequence.items().iter().enumerate() {
                    let nested_attrs = get_dicom_data_elements_keyword_path(dataset);
                    let extended_attrs = nested_attrs
                        .into_iter()
                        .map(|attr| format!("{}.{}.{}", keyword, i, attr));
                    dotty_attrs.extend(extended_attrs);
                }
            }
        } else {
            dotty_attrs.push(keyword.to_string());
        }
    }

    dotty_attrs
}

pub fn get_dicom_data_elements_hex_path(dcm: &InMemDicomObject) -> Vec<String> {
    let mut dotty_attrs = Vec::new();

    for elem in dcm.iter() {
        let tag = elem.header().tag;
        // Format tag as 8-digit hex (no 0x prefix)
        let tag_index = format!(
            "{:08x}",
            (u32::from(tag.group()) << 16) | u32::from(tag.element())
        );

        if let dicom_core::DicomValue::Sequence(seq) = elem.value() {
            let mut seq_attrs = vec![tag_index.clone()];

            for (i, item) in seq.items().iter().enumerate() {
                let attrs = get_dicom_data_elements_hex_path(item);
                for attr in attrs {
                    seq_attrs.push(format!("{tag_index}.{i}.{attr}"));
                }
            }

            dotty_attrs.extend(seq_attrs);
        } else {
            dotty_attrs.push(tag_index);
        }
    }

    dotty_attrs
}

pub fn get_all_field_paths(obj: &InMemDicomObject) -> Vec<String> {
    let mut paths = get_dicom_data_elements_keyword_path(obj);
    paths.extend(get_dicom_data_elements_hex_path(obj));
    paths
}

pub fn build_repeater_pattern(name: &str, recurse_sequence: bool) -> Option<String> {
    let pattern_core = if REPEATER_HEX_RE.is_match(name) {
        Some(name.replace("x", "X").replace("XX", "[0-9A-Fa-f]{2}"))
    } else if let Some(captures) = REPEATER_TUPLE_RE.captures(name) {
        let group = captures.get(1).unwrap().as_str();
        let element = captures.get(2).unwrap().as_str();
        Some(
            format!("{group}{element}")
                .replace("x", "X")
                .replace("XX", "[0-9A-Fa-f]{2}"),
        )
    } else {
        None
    };

    pattern_core.map(|p| {
        if recurse_sequence {
            format!(".*{p}$")
        } else {
            format!("^{p}$")
        }
    })
}

pub fn get_private_tag_in_sequences(
    obj: &InMemDicomObject,
    group: u16,
    element: u8,
    private_creator: &str,
) -> Vec<String> {
    let mut paths = Vec::new();

    for de in obj.iter() {
        if let dicom_core::DicomValue::Sequence(seq_items) = de.value() {
            let seq_tag_hex = format!("{:08X}", de.tag().0 as u32 * 0x10000 + de.tag().1 as u32);

            for (i, item) in seq_items.items().iter().enumerate() {
                if let Ok(el) = item.private_element(group, private_creator, element) {
                    let el_tag_hex =
                        format!("{:08X}", el.tag().0 as u32 * 0x10000 + el.tag().1 as u32);
                    paths.push(format!("{}.{}.{}", seq_tag_hex, i, el_tag_hex));
                }
                let nested_paths =
                    get_private_tag_in_sequences(item, group, element, private_creator);
                for nested_path in nested_paths {
                    paths.push(format!("{}.{}.{}", seq_tag_hex, i, nested_path));
                }
            }
        }
    }

    paths
}

pub struct PrivateTagEntry<'a> {
    pub tag: u32,
    pub vr: VR,
    pub alias: &'a str,
}

type E = PrivateTagEntry<'static>;

pub struct PrivateCreatorEntry {
    pub creator: &'static str,
    pub entries: &'static [E],
}

type P = PrivateCreatorEntry;

type PrivateDictionary = HashMap<&'static str, HashMap<u32, &'static E>>;

fn init_private_dictionary() -> PrivateDictionary {
    let mut dict = HashMap::new();
    for entry in PRIVATE_ENTRIES {
        let mut creator_dict = HashMap::new();
        for private_entry in entry.entries {
            creator_dict.insert(private_entry.tag, private_entry);
        }
        dict.insert(entry.creator, creator_dict);
    }
    dict
}

static PRIVATE_DICT: Lazy<PrivateDictionary> = Lazy::new(init_private_dictionary);

pub fn get_private_tag_vr(group: u16, element: u8, creator: &str) -> Option<VR> {
    let tag = ((group as u32) << 16) | ((0x1000 | (element as u16 & 0xFF)) as u32);
    PRIVATE_DICT.get(creator)?.get(&tag).map(|entry| entry.vr)
}

#[rustfmt::skip]
pub(crate) const PRIVATE_ENTRIES: &[P] = &[
    P {
        creator: "AGFA PACS Archive Mirroring 1.0",
        entries: &[
            E { tag: 0x00311000, alias: "StudyStatus", vr: VR::CS },
            E { tag: 0x00311001, alias: "DateTimeVerified", vr: VR::UL },
        ],
    },
    P {
        creator: "CARDIO-D.R. 1.0",
        entries: &[
            E { tag: 0x00191030, alias: "MaximumImageFrameSize", vr: VR::UL },
        ],
    },
    P {
        creator: "CMR42 CIRCLECVI",
        entries: &[
            E { tag: 0x00251010, alias: "WorkspaceID", vr: VR::LO },
            E { tag: 0x00251020, alias: "WorkspaceTimeString", vr: VR::LO },
            E { tag: 0x00251030, alias: "WorkspaceStream", vr: VR::OB },
        ],
    },
    P {
        creator: "DCMTK_ANONYMIZER",
        entries: &[
            E { tag: 0x00091000, alias: "AnonymizerUIDMap", vr: VR::SQ },
            E { tag: 0x00091010, alias: "AnonymizerUIDKey", vr: VR::UI },
            E { tag: 0x00091020, alias: "AnonymizerUIDValue", vr: VR::UI },
            E { tag: 0x00091030, alias: "AnonymizerPatientIDMap", vr: VR::SQ },
            E { tag: 0x00091040, alias: "AnonymizerPatientIDKey", vr: VR::LO },
            E { tag: 0x00091050, alias: "AnonymizerPatientIDValue", vr: VR::LO },
        ],
    },
    P {
        creator: "DLX_EXAMS_01",
        entries: &[
            E { tag: 0x00151001, alias: "StenosisCalibrationRatio", vr: VR::DS },
            E { tag: 0x00151002, alias: "StenosisMagnification", vr: VR::DS },
            E { tag: 0x00151003, alias: "CardiacCalibrationRatio", vr: VR::DS },
        ],
    },
    P {
        creator: "FDMS 1.0",
        entries: &[
            E { tag: 0x00191060, alias: "RadiographersCode", vr: VR::SH },
            E { tag: 0x00291034, alias: "MagnificationReductionRatio", vr: VR::US },
        ],
    },
    P {
        creator: "Flywheel",
        entries: &[
            E { tag: 0x00211000, alias: "DICOM Send", vr: VR::LO },
        ],
    },
    P {
        creator: "GEMS_ACQU_01",
        entries: &[
            E { tag: 0x00191002, alias: "NumberOfCellsInDetector", vr: VR::SL },
            E { tag: 0x0019100f, alias: "HorizontalFrameOfReference", vr: VR::DS },
            E { tag: 0x0019101b, alias: "LastScanLocation", vr: VR::DS },
            E { tag: 0x00191023, alias: "TableSpeed", vr: VR::DS },
            E { tag: 0x00191024, alias: "MidScanTime", vr: VR::DS },
            E { tag: 0x00191026, alias: "DegreesOfAzimuth", vr: VR::SL },
            E { tag: 0x00191027, alias: "GantryPeriod", vr: VR::DS },
            E { tag: 0x00191039, alias: "ScanFOVType", vr: VR::SS },
            E { tag: 0x00191043, alias: "TotalSegmentsRequested", vr: VR::SS },
            E { tag: 0x0019104a, alias: "TotalNumberOfRefChannels", vr: VR::SS },
            E { tag: 0x00191052, alias: "ReconPostProcessingFlag", vr: VR::SS },
            E { tag: 0x0019105e, alias: "NumberOfChannels1To512", vr: VR::SL },
            E { tag: 0x0019106a, alias: "DependantOnNumberOfViewsProcessed", vr: VR::SS },
            E { tag: 0x00191072, alias: "ZChannelAvgOverViews", vr: VR::DS },
            E { tag: 0x00191073, alias: "AvgOfLeftRefChannelsOverViews", vr: VR::DS },
            E { tag: 0x00191074, alias: "MaxLeftChannelOverViews", vr: VR::DS },
            E { tag: 0x00191075, alias: "AvgOfRightRefChannelsOverViews", vr: VR::DS },
            E { tag: 0x00191076, alias: "MaxRightChannelOverViews", vr: VR::DS },
            E { tag: 0x0019107e, alias: "NumberOfEchos", vr: VR::SS },
            E { tag: 0x0019108f, alias: "SwapPhaseFrequency", vr: VR::SS },
            E { tag: 0x00191091, alias: "PulseTime", vr: VR::DS },
            E { tag: 0x00191092, alias: "SliceOffsetOnFrequencyAxis", vr: VR::SL },
            E { tag: 0x00191093, alias: "CenterFrequency", vr: VR::DS },
            E { tag: 0x00191094, alias: "TransmitGain", vr: VR::SS },
            E { tag: 0x00191095, alias: "AnalogReceiverGain", vr: VR::SS },
            E { tag: 0x00191096, alias: "DigitalReceiverGain", vr: VR::SS },
            E { tag: 0x00191098, alias: "CenterFrequencyMethod", vr: VR::SS },
            E { tag: 0x0019109f, alias: "TransmittingCoil", vr: VR::SS },
            E { tag: 0x001910c1, alias: "SurfaceCoilIntensityCorrectionFlag", vr: VR::SS },
            E { tag: 0x001910cb, alias: "PrescribedFlowAxis", vr: VR::SS },
            E { tag: 0x001910d3, alias: "ProjectionAlgorithm", vr: VR::SH },
            E { tag: 0x001910d7, alias: "CardiacPhases", vr: VR::SS },
            E { tag: 0x001910d9, alias: "ConcatenatedSAT", vr: VR::DS },
            E { tag: 0x001910df, alias: "UserData23", vr: VR::DS },
            E { tag: 0x001910e0, alias: "UserData24", vr: VR::DS },
        ],
    },
    P {
        creator: "GEMS_PARM_01",
        entries: &[
            E { tag: 0x00431008, alias: "RespiratoryRateInBPM", vr: VR::SS },
            E { tag: 0x0043100b, alias: "PeakRateOfChangeOfGradientField", vr: VR::DS },
            E { tag: 0x0043100c, alias: "LimitsInUnitsOfPercent", vr: VR::DS },
            E { tag: 0x00431013, alias: "ReconKernelParameters", vr: VR::SS },
            E { tag: 0x0043101e, alias: "DeltaStartTime", vr: VR::DS },
            E { tag: 0x00431026, alias: "NoViewsRefChannelsBlocked", vr: VR::US },
            E { tag: 0x00431028, alias: "UniqueImageIdentifier", vr: VR::OB },
            E { tag: 0x0043102d, alias: "StringSlopField1", vr: VR::SH },
            E { tag: 0x0043102f, alias: "RawDataType", vr: VR::SS },
            E { tag: 0x00431030, alias: "RawDataType", vr: VR::SS },
            E { tag: 0x00431031, alias: "RACoordOfTargetReconCentre", vr: VR::DS },
            E { tag: 0x00431032, alias: "RawDataType", vr: VR::SS },
            E { tag: 0x00431038, alias: "User25ToUser48", vr: VR::FL },
            E { tag: 0x00431039, alias: "SlopInteger6ToSlopInteger9", vr: VR::IS },
            E { tag: 0x00431060, alias: "SlopInteger10ToSlopInteger17", vr: VR::IS },
            E { tag: 0x0043106f, alias: "ScannerTableEntry", vr: VR::DS },
            E { tag: 0x00431074, alias: "NumberOfRestVolumes", vr: VR::US },
            E { tag: 0x00431075, alias: "NumberOfActiveVolumes", vr: VR::US },
            E { tag: 0x00431076, alias: "NumberOfDummyScans", vr: VR::US },
            E { tag: 0x0043107f, alias: "EDWIScaleFactor", vr: VR::DS },
            E { tag: 0x00431087, alias: "ScannerSoftwareVersionLongForm", vr: VR::UT },
        ],
    },
    P {
        creator: "GEMS_RELA_01",
        entries: &[
            E { tag: 0x00211056, alias: "IntegerSlop", vr: VR::SL },
            E { tag: 0x00211057, alias: "IntegerSlop", vr: VR::SL },
            E { tag: 0x00211058, alias: "IntegerSlop", vr: VR::SL },
            E { tag: 0x00211059, alias: "IntegerSlop", vr: VR::SL },
            E { tag: 0x0021105a, alias: "IntegerSlop", vr: VR::SL },
            E { tag: 0x0021105b, alias: "FloatSlop", vr: VR::DS },
            E { tag: 0x0021105c, alias: "FloatSlop", vr: VR::DS },
            E { tag: 0x0021105d, alias: "FloatSlop", vr: VR::DS },
            E { tag: 0x0021105e, alias: "FloatSlop", vr: VR::DS },
            E { tag: 0x0021105f, alias: "FloatSlop", vr: VR::DS },
        ],
    },
    P {
        creator: "GEMS_SENO_02",
        entries: &[
            E { tag: 0x00451006, alias: "Angulation", vr: VR::DS },
            E { tag: 0x0045100d, alias: "ROIOriginXY", vr: VR::DS },
            E { tag: 0x00451011, alias: "ReceptorSizeCmXY", vr: VR::DS },
            E { tag: 0x00451012, alias: "ReceptorSizePixelsXY", vr: VR::IS },
            E { tag: 0x00451016, alias: "BinningFactorXY", vr: VR::IS },
            E { tag: 0x00451020, alias: "MeanOfRegionGrayLevels", vr: VR::DS },
            E { tag: 0x00451028, alias: "WindowingType", vr: VR::CS },
            E { tag: 0x0045102a, alias: "CrosshairCursorXCoordinates", vr: VR::IS },
            E { tag: 0x0045102b, alias: "CrosshairCursorYCoordinates", vr: VR::IS },
        ],
    },
    P {
        creator: "GEMS_SERS_01",
        entries: &[
            E { tag: 0x00251014, alias: "IndicatesNumberOfUpdatesToHeader", vr: VR::SL },
        ],
    },
    P {
        creator: "GEMS_STDY_01",
        entries: &[
            E { tag: 0x00231074, alias: "NumberOfUpdatesToHeader", vr: VR::SL },
            E { tag: 0x0023107d, alias: "IndicatesIfStudyHasCompleteInfo", vr: VR::SS },
        ],
    },
    P {
        creator: "GE_GENESIS_REV3.0",
        entries: &[
            E { tag: 0x0019108f, alias: "SwapPhaseFrequency", vr: VR::SS },
            E { tag: 0x001910a4, alias: "SATFatWaterBone", vr: VR::SS },
            E { tag: 0x001910c1, alias: "SurfaceCoilIntensityCorrectionFlag", vr: VR::SS },
            E { tag: 0x00431027, alias: "ScanPitchRatio", vr: VR::SH },
        ],
    },
    P {
        creator: "INTELERAD MEDICAL SYSTEMS",
        entries: &[
            E { tag: 0x00291001, alias: "ImageCompressionFraction", vr: VR::FD },
            E { tag: 0x00291002, alias: "ImageQuality", vr: VR::FD },
            E { tag: 0x00291003, alias: "ImageBytesTransferred", vr: VR::FD },
            E { tag: 0x00291010, alias: "J2cParameterType", vr: VR::SH },
            E { tag: 0x00291011, alias: "J2cPixelRepresentation", vr: VR::US },
            E { tag: 0x00291012, alias: "J2cBitsAllocated", vr: VR::US },
            E { tag: 0x00291013, alias: "J2cPixelShiftValue", vr: VR::US },
            E { tag: 0x00291014, alias: "J2cPlanarConfiguration", vr: VR::US },
            E { tag: 0x00291015, alias: "J2cRescaleIntercept", vr: VR::DS },
            E { tag: 0x00291020, alias: "PixelDataMD5SumPerFrame", vr: VR::LO },
            E { tag: 0x00291021, alias: "HistogramPercentileLabels", vr: VR::US },
            E { tag: 0x00291022, alias: "HistogramPercentileValues", vr: VR::FD },
            E { tag: 0x3f011006, alias: "OrderGroupNumber", vr: VR::LO },
            E { tag: 0x3f011007, alias: "StrippedPixelData", vr: VR::SH },
            E { tag: 0x3f011008, alias: "PendingMoveRequest", vr: VR::SH },
        ],
    },
    P {
        creator: "OCULUS Optikgeraete GmbH",
        entries: &[
            E { tag: 0x00291010, alias: "OriginalMeasuringData", vr: VR::OB },
            E { tag: 0x00291012, alias: "OriginalMeasuringDataLength", vr: VR::UL },
            E { tag: 0x00291020, alias: "OriginalMeasuringRawData", vr: VR::OB },
            E { tag: 0x00291022, alias: "OriginalMeasuringRawDataLength", vr: VR::UL },
        ],
    },
    P {
        creator: "Philips EV Imaging DD022",
        entries: &[
            E { tag: 0x20071012, alias: "VolumeSequenceCapture", vr: VR::LO },
        ],
    },
    P {
        creator: "Philips Imaging DD 001",
        entries: &[
            E { tag: 0x20011005, alias: "GraphicAnnotationParentID", vr: VR::SS },
            E { tag: 0x20011009, alias: "ImagePrepulseDelay", vr: VR::FL },
            E { tag: 0x2001100c, alias: "ArrhythmiaRejection", vr: VR::CS },
            E { tag: 0x2001100e, alias: "CardiacCycled", vr: VR::CS },
            E { tag: 0x2001100f, alias: "CardiacGateWidth", vr: VR::SS },
            E { tag: 0x2001101e, alias: "MRSeriesReformatAccuracy", vr: VR::CS },
            E { tag: 0x2001103d, alias: "ContourFillColor", vr: VR::UL },
            E { tag: 0x2001103f, alias: "ZoomMode", vr: VR::CS },
            E { tag: 0x20011043, alias: "EllipsDisplShutMajorAxFrstEndPnt", vr: VR::IS },
            E { tag: 0x20011044, alias: "EllipsDisplShutMajorAxScndEndPnt", vr: VR::IS },
            E { tag: 0x20011045, alias: "EllipsDisplShutOtherAxFrstEndPnt", vr: VR::IS },
            E { tag: 0x20011050, alias: "GraphicMarkerType", vr: VR::LO },
            E { tag: 0x20011051, alias: "OverlayPlaneID", vr: VR::IS },
            E { tag: 0x20011052, alias: "ImagePresentationStateUID", vr: VR::UI },
            E { tag: 0x20011054, alias: "ContourFillTransparency", vr: VR::FL },
            E { tag: 0x20011058, alias: "ContrastTransferTaste", vr: VR::UL },
            E { tag: 0x20011061, alias: "SeriesTransmitted", vr: VR::CS },
            E { tag: 0x20011062, alias: "SeriesCommitted", vr: VR::CS },
            E { tag: 0x20011065, alias: "ROIOverlayPlane", vr: VR::SQ },
            E { tag: 0x20011067, alias: "LinearPresentationGLTrafoShapeSub", vr: VR::CS },
            E { tag: 0x20011068, alias: "LinearModalityGLTrafo", vr: VR::SQ },
            E { tag: 0x2001106a, alias: "SpatialTransformation", vr: VR::SQ },
            E { tag: 0x20011071, alias: "GraphicConstraint", vr: VR::CS },
            E { tag: 0x20011072, alias: "EllipsDisplShutOtherAxScndEndPnt", vr: VR::IS },
            E { tag: 0x20011076, alias: "MRNumberOfFrames", vr: VR::UI },
            E { tag: 0x2001107a, alias: "WindowRoundingFactor", vr: VR::FL },
            E { tag: 0x2001107c, alias: "FrameNumber", vr: VR::US },
            E { tag: 0x20011086, alias: "MRSeriesNrOfPhaseEncodingSteps", vr: VR::IS },
            E { tag: 0x2001108b, alias: "MRSeriesTransmittingCoil", vr: VR::SH },
            E { tag: 0x20011090, alias: "TextForegroundColor", vr: VR::LO },
            E { tag: 0x20011091, alias: "TextBackgroundColor", vr: VR::LO },
            E { tag: 0x20011092, alias: "TextShadowColor", vr: VR::LO },
            E { tag: 0x2001109c, alias: "GraphicAnnotationLabel", vr: VR::LO },
        ],
    },
    P {
        creator: "Philips MR Imaging DD 001",
        entries: &[
            E { tag: 0x20051000, alias: "MRImageAngulationAP", vr: VR::FL },
            E { tag: 0x20051001, alias: "MRImageAngulationFH", vr: VR::FL },
            E { tag: 0x20051002, alias: "MRImageAngulationRL", vr: VR::FL },
            E { tag: 0x20051003, alias: "ImageAnnotationCount", vr: VR::IS },
            E { tag: 0x20051004, alias: "MRImageDisplayOrientation", vr: VR::CS },
            E { tag: 0x20051007, alias: "ImageLineCount", vr: VR::IS },
            E { tag: 0x20051008, alias: "MRImageOffCentreAP", vr: VR::FL },
            E { tag: 0x20051009, alias: "MRImageOffCentreFH", vr: VR::FL },
            E { tag: 0x2005100a, alias: "MRImageOffCentreRL", vr: VR::FL },
            E { tag: 0x2005100b, alias: "MRMaxFP", vr: VR::FL },
            E { tag: 0x2005100c, alias: "MRMinFP", vr: VR::FL },
            E { tag: 0x2005100d, alias: "MRScaleIntercept", vr: VR::FL },
            E { tag: 0x2005100e, alias: "MRScaleSlope", vr: VR::FL },
            E { tag: 0x20051011, alias: "MRImageTypeMR", vr: VR::CS },
            E { tag: 0x20051012, alias: "MRCardiacGating", vr: VR::CS },
            E { tag: 0x20051013, alias: "MRSeriesDevelopmentMode", vr: VR::CS },
            E { tag: 0x20051014, alias: "MRSeriesDiffusion", vr: VR::CS },
            E { tag: 0x20051015, alias: "MRFatSaturation", vr: VR::CS },
            E { tag: 0x20051016, alias: "MRFlowCompensation", vr: VR::CS },
            E { tag: 0x20051017, alias: "MRFourierInterpolation", vr: VR::CS },
            E { tag: 0x20051018, alias: "MRHardcopyProtocol", vr: VR::LO },
            E { tag: 0x20051019, alias: "MRInverseReconstructed", vr: VR::CS },
            E { tag: 0x2005101a, alias: "MRLabelSyntax", vr: VR::SS },
            E { tag: 0x2005101b, alias: "MRMagnetiPrepared", vr: VR::CS },
            E { tag: 0x2005101c, alias: "MRMagnetTransferConst", vr: VR::CS },
            E { tag: 0x2005101d, alias: "MRMeasurementScanResolution", vr: VR::SS },
            E { tag: 0x2005101e, alias: "MIPProtocol", vr: VR::SH },
            E { tag: 0x2005101f, alias: "MPRProtocol", vr: VR::SH },
            E { tag: 0x20051021, alias: "MRNumberOfMixes", vr: VR::SS },
            E { tag: 0x20051022, alias: "MRNumberOfReferences", vr: VR::IS },
            E { tag: 0x20051023, alias: "MRNumberOfSlabs", vr: VR::SS },
            E { tag: 0x20051025, alias: "MRNumberOfVolumes", vr: VR::SS },
            E { tag: 0x20051026, alias: "MROverSampleingPhase", vr: VR::CS },
            E { tag: 0x20051027, alias: "MRPackageMode", vr: VR::CS },
            E { tag: 0x20051028, alias: "MRPartialFourierFrequency", vr: VR::CS },
            E { tag: 0x20051029, alias: "MRPartialFourierPhase", vr: VR::CS },
            E { tag: 0x2005102a, alias: "MRPatientReferenceID", vr: VR::IS },
            E { tag: 0x2005102b, alias: "MRPercentScanComplete", vr: VR::SS },
            E { tag: 0x2005102c, alias: "MRPhaseEncodedRecording", vr: VR::CS },
            E { tag: 0x2005102d, alias: "NumberOfStackSlices", vr: VR::SS },
            E { tag: 0x2005102e, alias: "MRPPGPPUGating", vr: VR::CS },
            E { tag: 0x2005102f, alias: "MRSpatialPresaturation", vr: VR::CS },
            E { tag: 0x20051031, alias: "MRRespiratoryGating", vr: VR::CS },
            E { tag: 0x20051032, alias: "SampleRepresentation", vr: VR::CS },
            E { tag: 0x20051034, alias: "MRSegmentedKSpace", vr: VR::CS },
            E { tag: 0x20051035, alias: "MRSeriesDataType", vr: VR::CS },
            E { tag: 0x20051036, alias: "MRSeriesIsCardiac", vr: VR::CS },
            E { tag: 0x20051037, alias: "MRSeriesIsSpectro", vr: VR::CS },
            E { tag: 0x20051038, alias: "MRSpoiled", vr: VR::CS },
            E { tag: 0x20051039, alias: "MRSteadyState", vr: VR::CS },
            E { tag: 0x2005103a, alias: "MRSubAnatomy", vr: VR::SH },
            E { tag: 0x2005103b, alias: "MRTimeReversedSteadyState", vr: VR::CS },
            E { tag: 0x2005103c, alias: "MRSeriesTone", vr: VR::CS },
            E { tag: 0x2005103d, alias: "MRNumberOfRRIntervalRanges", vr: VR::SS },
            E { tag: 0x2005103e, alias: "MRRRIntervalsDistribution", vr: VR::SL },
            E { tag: 0x2005103f, alias: "MRPlanScanAcquisitionNo", vr: VR::SL },
            E { tag: 0x20051040, alias: "MRChemicalShiftNo", vr: VR::SL },
            E { tag: 0x20051041, alias: "MRPlanScanDynamicScanNo", vr: VR::SL },
            E { tag: 0x20051042, alias: "MRPlanScanSurveyEchoNo", vr: VR::SL },
            E { tag: 0x20051043, alias: "MRPlanScanImageType", vr: VR::CS },
            E { tag: 0x20051044, alias: "MRPlanScanPhaseNo", vr: VR::SL },
            E { tag: 0x20051045, alias: "MRPlanScanReconstructionNo", vr: VR::SL },
            E { tag: 0x20051046, alias: "MRPlanScanScanningSequence", vr: VR::CS },
            E { tag: 0x20051047, alias: "MRPlanScanSliceNo", vr: VR::SL },
            E { tag: 0x20051048, alias: "MRReferenceAcquisitionNo", vr: VR::IS },
            E { tag: 0x20051049, alias: "MRReferenceChemicalShiftNo", vr: VR::IS },
            E { tag: 0x2005104a, alias: "MRReferenceDynamicScanNo", vr: VR::IS },
            E { tag: 0x2005104b, alias: "MRReferenceEchoNo", vr: VR::IS },
            E { tag: 0x2005104c, alias: "MRReferenceEntity", vr: VR::CS },
            E { tag: 0x2005104d, alias: "MRReferenceImageType", vr: VR::CS },
            E { tag: 0x2005104e, alias: "MRSlabFovRL", vr: VR::FL },
            E { tag: 0x2005104f, alias: "MRSlabOffcentreAP", vr: VR::FL },
            E { tag: 0x20051050, alias: "MRSlabOffcentreFH", vr: VR::FL },
            E { tag: 0x20051051, alias: "MRSlabOffcentreRL", vr: VR::FL },
            E { tag: 0x20051052, alias: "MRSlabType", vr: VR::CS },
            E { tag: 0x20051053, alias: "MRSlabViewAxis", vr: VR::CS },
            E { tag: 0x20051054, alias: "MRVolumeAngulationAP", vr: VR::FL },
            E { tag: 0x20051055, alias: "MRVolumeAngulationFH", vr: VR::FL },
            E { tag: 0x20051056, alias: "MRVolumeAngulationRL", vr: VR::FL },
            E { tag: 0x20051057, alias: "MRVolumeFovAP", vr: VR::FL },
            E { tag: 0x20051058, alias: "MRVolumeFovFH", vr: VR::FL },
            E { tag: 0x20051059, alias: "MRVolumeFovRL", vr: VR::FL },
            E { tag: 0x2005105a, alias: "MRVolumeOffcentreAP", vr: VR::FL },
            E { tag: 0x2005105b, alias: "MRVolumeOffcentreFH", vr: VR::FL },
            E { tag: 0x2005105c, alias: "MRVolumeOffcentreRL", vr: VR::FL },
            E { tag: 0x2005105d, alias: "MRVolumeType", vr: VR::CS },
            E { tag: 0x2005105e, alias: "MRVolumeViewAxis", vr: VR::CS },
            E { tag: 0x2005105f, alias: "MRStudyOrigin", vr: VR::CS },
            E { tag: 0x20051060, alias: "MRStudySequenceNumber", vr: VR::IS },
            E { tag: 0x20051061, alias: "MRImagePrepulseType", vr: VR::CS },
            E { tag: 0x20051063, alias: "MRfMRIStatusIndication", vr: VR::SS },
            E { tag: 0x20051064, alias: "MRReferencePhaseNo", vr: VR::IS },
            E { tag: 0x20051065, alias: "MRReferenceReconstructionNo", vr: VR::IS },
            E { tag: 0x20051066, alias: "MRReferenceScanningSequence", vr: VR::CS },
            E { tag: 0x20051067, alias: "MRReferenceSliceNo", vr: VR::IS },
            E { tag: 0x20051068, alias: "MRReferenceType", vr: VR::CS },
            E { tag: 0x20051069, alias: "MRSlabAngulationAP", vr: VR::FL },
            E { tag: 0x2005106a, alias: "MRSlabAngulationFH", vr: VR::FL },
            E { tag: 0x2005106b, alias: "MRSlabAngulationRL", vr: VR::FL },
            E { tag: 0x2005106c, alias: "MRSlabFovAP", vr: VR::FL },
            E { tag: 0x2005106d, alias: "MRSlabFovFH", vr: VR::FL },
            E { tag: 0x2005106e, alias: "MRImageScanningSequencePrivate", vr: VR::CS },
            E { tag: 0x2005106f, alias: "MRSeriesAcquisitionTypePrivate", vr: VR::CS },
            E { tag: 0x20051070, alias: "MRSeriesHardcopyProtocolEV", vr: VR::LO },
            E { tag: 0x20051071, alias: "MRStackAngulationAP", vr: VR::FL },
            E { tag: 0x20051072, alias: "MRStackAngulationFH", vr: VR::FL },
            E { tag: 0x20051073, alias: "MRStackAngulationRL", vr: VR::FL },
            E { tag: 0x20051074, alias: "MRStackFovAP", vr: VR::FL },
            E { tag: 0x20051075, alias: "MRStackFovFH", vr: VR::FL },
            E { tag: 0x20051076, alias: "MRStackFovRL", vr: VR::FL },
            E { tag: 0x20051078, alias: "MRStackOffcentreAP", vr: VR::FL },
            E { tag: 0x20051079, alias: "MRStackOffcentreFH", vr: VR::FL },
            E { tag: 0x2005107a, alias: "MRStackOffcentreRL", vr: VR::FL },
            E { tag: 0x2005107b, alias: "MRStackPreparationDirection", vr: VR::CS },
            E { tag: 0x2005107e, alias: "MRStackSliceDistance", vr: VR::FL },
            E { tag: 0x20051080, alias: "SeriesPlanScan", vr: VR::SQ },
            E { tag: 0x20051081, alias: "MRStackViewAxis", vr: VR::CS },
            E { tag: 0x20051084, alias: "SeriesReference", vr: VR::SQ },
            E { tag: 0x20051085, alias: "SeriesVolume", vr: VR::SQ },
            E { tag: 0x20051086, alias: "MRNumberOfGeometry", vr: VR::SS },
            E { tag: 0x20051087, alias: "MRNumberOfGeometrySlices", vr: VR::SL },
            E { tag: 0x20051088, alias: "MRGeomAngulationAP", vr: VR::FL },
            E { tag: 0x20051089, alias: "MRGeomAngulationFH", vr: VR::FL },
            E { tag: 0x2005108a, alias: "MRGeomAngulationRL", vr: VR::FL },
            E { tag: 0x2005108b, alias: "MRGeomFOVAP", vr: VR::FL },
            E { tag: 0x2005108c, alias: "MRGeomFOVFH", vr: VR::FL },
            E { tag: 0x2005108d, alias: "MRGeomFOVRL", vr: VR::FL },
            E { tag: 0x2005108e, alias: "MRGeomOffCentreAP", vr: VR::FL },
            E { tag: 0x2005108f, alias: "MRGeomOffCentreFH", vr: VR::FL },
            E { tag: 0x20051090, alias: "MRGeomOffCentreRL", vr: VR::FL },
            E { tag: 0x20051091, alias: "MRGeomPreparationDirect", vr: VR::CS },
            E { tag: 0x20051092, alias: "MRGeomRadialAngle", vr: VR::FL },
            E { tag: 0x20051093, alias: "MRGeomRadialAxis", vr: VR::CS },
            E { tag: 0x20051094, alias: "MRGeomSliceDistance", vr: VR::FL },
            E { tag: 0x20051095, alias: "MRGeomSliceNumber", vr: VR::SL },
            E { tag: 0x20051096, alias: "MRGeomType", vr: VR::CS },
            E { tag: 0x20051097, alias: "MRGeomViewAxis", vr: VR::CS },
            E { tag: 0x20051098, alias: "MRGeomColour", vr: VR::CS },
            E { tag: 0x20051099, alias: "MRGeomApplicationType", vr: VR::CS },
            E { tag: 0x2005109a, alias: "MRGeomId", vr: VR::SL },
            E { tag: 0x2005109b, alias: "MRGeomApplicationName", vr: VR::SH },
            E { tag: 0x2005109c, alias: "MRGeomLableName", vr: VR::SH },
            E { tag: 0x2005109d, alias: "MRGeomLineStyle", vr: VR::CS },
            E { tag: 0x2005109e, alias: "SeriesGeom", vr: VR::SQ },
            E { tag: 0x2005109f, alias: "MRSeriesSpectralSelectiveExcitationPulse", vr: VR::CS },
        ],
    },
    P {
        creator: "Philips MR Imaging DD 002",
        entries: &[
            E { tag: 0x20051015, alias: "MRUserName", vr: VR::LO },
            E { tag: 0x20051016, alias: "MRPassWord", vr: VR::LO },
            E { tag: 0x20051017, alias: "MRServerName", vr: VR::LO },
            E { tag: 0x20051018, alias: "MRDataBaseName", vr: VR::LO },
            E { tag: 0x20051019, alias: "MRRootName", vr: VR::LO },
            E { tag: 0x20051020, alias: "DMIApplicationName", vr: VR::LO },
            E { tag: 0x2005102d, alias: "MRRootId", vr: VR::LO },
            E { tag: 0x20051032, alias: "MRBlobDataObjectArray", vr: VR::SQ },
            E { tag: 0x20051034, alias: "SeriesTransactionUID", vr: VR::LT },
            E { tag: 0x20051035, alias: "ParentID", vr: VR::IS },
            E { tag: 0x20051036, alias: "ParentType", vr: VR::PN },
            E { tag: 0x20051037, alias: "MRBlobName", vr: VR::PN },
            E { tag: 0x20051038, alias: "MRApplicationName", vr: VR::PN },
            E { tag: 0x20051039, alias: "MRTypeName", vr: VR::PN },
            E { tag: 0x20051040, alias: "MRVersionStr", vr: VR::PN },
            E { tag: 0x20051041, alias: "MRCommentStr", vr: VR::PN },
            E { tag: 0x20051042, alias: "BlobInFile", vr: VR::CS },
            E { tag: 0x20051043, alias: "MRActualBlobSize", vr: VR::SL },
            E { tag: 0x20051044, alias: "MRBlobData", vr: VR::OW },
            E { tag: 0x20051045, alias: "BlobFilename", vr: VR::PN },
            E { tag: 0x20051046, alias: "BlobOffset", vr: VR::SL },
            E { tag: 0x20051047, alias: "MRBlobFlag", vr: VR::CS },
            E { tag: 0x20051099, alias: "MRNumberOfRequestExcerpts", vr: VR::UL },
        ],
    },
    P {
        creator: "Philips MR Imaging DD 003",
        entries: &[
            E { tag: 0x20051000, alias: "MRNumberOfSOPCommon", vr: VR::UL },
            E { tag: 0x20051001, alias: "MRNoOfFilmConsumption", vr: VR::UL },
            E { tag: 0x20051013, alias: "MRNumberOfCodes", vr: VR::UL },
            E { tag: 0x20051034, alias: "MRNumberOfImagePerSeriesRef", vr: VR::SL },
            E { tag: 0x20051043, alias: "MRNoDateOfLastCalibration", vr: VR::SS },
            E { tag: 0x20051044, alias: "MRNoTimeOfLastCalibration", vr: VR::SS },
            E { tag: 0x20051045, alias: "MRNrOfSoftwareVersion", vr: VR::SS },
            E { tag: 0x20051047, alias: "MRNrOfPatientOtherNames", vr: VR::SS },
            E { tag: 0x20051048, alias: "MRNrOfReqRecipeOfResults", vr: VR::SS },
            E { tag: 0x20051049, alias: "MRNrOfSeriesOperatorsName", vr: VR::SS },
            E { tag: 0x20051050, alias: "MRNrOfSeriesPerfPhysiName", vr: VR::SS },
            E { tag: 0x20051051, alias: "MRNrOfStudyAdmittingDiagnosticDescr", vr: VR::SS },
            E { tag: 0x20051052, alias: "MRNrOfStudyPatientContrastAllergies", vr: VR::SS },
            E { tag: 0x20051053, alias: "MRNrOfStudyPatientMedicalAlerts", vr: VR::SS },
            E { tag: 0x20051054, alias: "MRNrOfStudyPhysiciansOfRecord", vr: VR::SS },
            E { tag: 0x20051055, alias: "MRNrOfStudyPhysiReadingStudy", vr: VR::SS },
            E { tag: 0x20051056, alias: "MRNrSCSoftwareVersions", vr: VR::SS },
            E { tag: 0x20051057, alias: "MRNrRunningAttributes", vr: VR::SS },
            E { tag: 0x20051070, alias: "SpectrumPixelData", vr: VR::OW },
            E { tag: 0x20051081, alias: "DefaultImageUID", vr: VR::UI },
            E { tag: 0x20051082, alias: "RunningAttributes", vr: VR::CS },
        ],
    },
    P {
        creator: "Philips MR Imaging DD 004",
        entries: &[
            E { tag: 0x20051000, alias: "MRSpectrumExtraNumber", vr: VR::SS },
            E { tag: 0x20051001, alias: "MRSpectrumKxCoordinate", vr: VR::SS },
            E { tag: 0x20051002, alias: "MRSpectrumKyCoordinate", vr: VR::SS },
            E { tag: 0x20051003, alias: "MRSpectrumLocationNumber", vr: VR::SS },
            E { tag: 0x20051004, alias: "MRSpectrumMixNumber", vr: VR::SS },
            E { tag: 0x20051005, alias: "MRSpectrumXCoordinate", vr: VR::SS },
            E { tag: 0x20051006, alias: "MRSpectrumYCoordinate", vr: VR::SS },
            E { tag: 0x20051007, alias: "MRSpectrumDCLevel", vr: VR::FL },
            E { tag: 0x20051008, alias: "MRSpectrumNoiseLevel", vr: VR::FL },
            E { tag: 0x20051009, alias: "MRSpectrumBeginTime", vr: VR::FL },
            E { tag: 0x20051010, alias: "MRSpectrumEchoTime", vr: VR::FL },
            E { tag: 0x20051012, alias: "SpectrumNumber", vr: VR::FL },
            E { tag: 0x20051013, alias: "MRSpectrumNumber", vr: VR::SS },
            E { tag: 0x20051014, alias: "MRSpectrumNumberOfAverages", vr: VR::SS },
            E { tag: 0x20051015, alias: "MRSpectrumNumberOfSamples", vr: VR::SS },
            E { tag: 0x20051016, alias: "MRSpectrumScanSequenceNumber", vr: VR::SS },
            E { tag: 0x20051017, alias: "MRSpectrumNumberOfPeaks", vr: VR::SS },
            E { tag: 0x20051018, alias: "MRSpectrumPeak", vr: VR::SQ },
            E { tag: 0x20051019, alias: "MRSpectrumPeakIntensity", vr: VR::FL },
            E { tag: 0x20051020, alias: "MRSpectrumPeakLabel", vr: VR::LO },
            E { tag: 0x20051021, alias: "MRSpectrumPeakPhase", vr: VR::FL },
            E { tag: 0x20051022, alias: "MRSpectrumPeakPosition", vr: VR::FL },
            E { tag: 0x20051023, alias: "MRSpectrumPeakType", vr: VR::CS },
            E { tag: 0x20051024, alias: "MRSpectrumPeakWidth", vr: VR::FL },
            E { tag: 0x20051025, alias: "MRSpectroSIB0Correction", vr: VR::CS },
            E { tag: 0x20051026, alias: "MRSpectroB0EchoTopPosition", vr: VR::FL },
            E { tag: 0x20051027, alias: "MRSpectroComplexComponent", vr: VR::CS },
            E { tag: 0x20051028, alias: "MRSpectroDataOrigin", vr: VR::CS },
            E { tag: 0x20051029, alias: "MRSpectroEchoTopPosition", vr: VR::FL },
            E { tag: 0x20051030, alias: "MRInPlaneTransforms", vr: VR::CS },
            E { tag: 0x20051031, alias: "MRNumberOfSpectraAcquired", vr: VR::SS },
            E { tag: 0x20051033, alias: "MRPhaseEncodingEchoTopPositions", vr: VR::FL },
            E { tag: 0x20051034, alias: "MRPhysicalQuantityForChemicalShift", vr: VR::CS },
            E { tag: 0x20051035, alias: "MRPhysicalQuantitySpatial", vr: VR::CS },
            E { tag: 0x20051036, alias: "MRReferenceFrequency", vr: VR::FL },
            E { tag: 0x20051037, alias: "MRSampleOffset", vr: VR::FL },
            E { tag: 0x20051038, alias: "MRSamplePitch", vr: VR::FL },
            E { tag: 0x20051039, alias: "MRSearchIntervalForPeaks", vr: VR::SS },
            E { tag: 0x20051040, alias: "MRSignalDomainForChemicalShift", vr: VR::CS },
            E { tag: 0x20051041, alias: "MRSignalDomainSpatial", vr: VR::CS },
            E { tag: 0x20051042, alias: "MRSignalType", vr: VR::CS },
            E { tag: 0x20051043, alias: "MRSpectroAdditionalRotations", vr: VR::CS },
            E { tag: 0x20051044, alias: "MRSpectroDisplayRanges", vr: VR::SS },
            E { tag: 0x20051045, alias: "MRSpectroEchoAcquisition", vr: VR::CS },
            E { tag: 0x20051046, alias: "MRSpectroFrequencyUnit", vr: VR::CS },
            E { tag: 0x20051047, alias: "MRSpectroGamma", vr: VR::FL },
            E { tag: 0x20051048, alias: "MRSpectroHiddenLineRemoval", vr: VR::CS },
            E { tag: 0x20051049, alias: "MRSpectroHorizontalShift", vr: VR::FL },
            E { tag: 0x20051050, alias: "MRSpectroHorizontalWindow", vr: VR::FL },
            E { tag: 0x20051051, alias: "MRSpectroNumberOfDisplayRanges", vr: VR::SS },
            E { tag: 0x20051052, alias: "MRSpectroNumberOfEchoPulses", vr: VR::SS },
            E { tag: 0x20051053, alias: "MRSpectroProcessingHistory", vr: VR::LO },
            E { tag: 0x20051054, alias: "MRSpectroScanType", vr: VR::CS },
            E { tag: 0x20051055, alias: "MRSpectroSICSIntervals", vr: VR::FL },
            E { tag: 0x20051056, alias: "MRSpectroSIMode", vr: VR::CS },
            E { tag: 0x20051057, alias: "MRSpectroSpectralBW", vr: VR::SS },
            E { tag: 0x20051058, alias: "MRSpectroTitleLine", vr: VR::LO },
            E { tag: 0x20051059, alias: "MRSpectroTurboEchoSpacing", vr: VR::FL },
            E { tag: 0x20051060, alias: "MRSpectroVerticalShift", vr: VR::FL },
            E { tag: 0x20051061, alias: "MRSpectroVerticalWindow", vr: VR::FL },
            E { tag: 0x20051062, alias: "MRSpectroOffset", vr: VR::FL },
            E { tag: 0x20051063, alias: "MRSpectrumPitch", vr: VR::FL },
            E { tag: 0x20051064, alias: "MRVolumeSelection", vr: VR::CS },
            E { tag: 0x20051070, alias: "MRNoMixesSpectro", vr: VR::SS },
            E { tag: 0x20051071, alias: "MRSeriesSPMix", vr: VR::SQ },
            E { tag: 0x20051072, alias: "SPMixTResolution", vr: VR::SS },
            E { tag: 0x20051073, alias: "SPMixKXResolution", vr: VR::SS },
            E { tag: 0x20051074, alias: "SPMixKYResolution", vr: VR::SS },
            E { tag: 0x20051075, alias: "SPMixFResolution", vr: VR::SS },
            E { tag: 0x20051076, alias: "SPMixXResolution", vr: VR::SS },
            E { tag: 0x20051077, alias: "SPMixYResolution", vr: VR::SS },
            E { tag: 0x20051078, alias: "SPMixNoSpectraIntended", vr: VR::SS },
            E { tag: 0x20051079, alias: "SPMixNoAverages", vr: VR::SS },
            E { tag: 0x20051080, alias: "MRSeriesNrOfMFImageObjects", vr: VR::SL },
            E { tag: 0x20051081, alias: "MRScanoGramSurveyNumberOfImages", vr: VR::IS },
            E { tag: 0x20051082, alias: "MRNumberOfProcedureCodes", vr: VR::UL },
            E { tag: 0x20051083, alias: "SortAttributes", vr: VR::CS },
            E { tag: 0x20051084, alias: "MRNrSortAttributes", vr: VR::SS },
            E { tag: 0x20051085, alias: "ImageDisplayDirection", vr: VR::CS },
            E { tag: 0x20051086, alias: "InsetScanogram", vr: VR::CS },
            E { tag: 0x20051087, alias: "MRDisplayLayoutNrColumns", vr: VR::SS },
            E { tag: 0x20051088, alias: "MRDisplayLayoutNrRows", vr: VR::SS },
            E { tag: 0x20051089, alias: "ViewingProtocol", vr: VR::SQ },
            E { tag: 0x20051090, alias: "MRStackCoilFunction", vr: VR::CS },
            E { tag: 0x20051091, alias: "PatientNameJobInParams", vr: VR::PN },
            E { tag: 0x20051092, alias: "MRGeolinkID", vr: VR::IS },
            E { tag: 0x20051093, alias: "MRStationNo", vr: VR::IS },
            E { tag: 0x20051094, alias: "ProcessingHistory", vr: VR::CS },
            E { tag: 0x20051095, alias: "ViewProcedureString", vr: VR::UI },
            E { tag: 0x20051096, alias: "MRFlowImagesPresent", vr: VR::CS },
            E { tag: 0x20051097, alias: "AnatomicRegCodeValue", vr: VR::LO },
            E { tag: 0x20051098, alias: "MRMobiviewEnabled", vr: VR::CS },
            E { tag: 0x20051099, alias: "MRIViewBoldEnabled", vr: VR::CS },
        ],
    },
    P {
        creator: "Philips MR Imaging DD 005",
        entries: &[
            E { tag: 0x20051000, alias: "MRVolumeViewEnabled", vr: VR::CS },
            E { tag: 0x20051001, alias: "MRNumberOfStudyReference", vr: VR::UL },
            E { tag: 0x20051003, alias: "MRNumberOfSPSCodes", vr: VR::UL },
            E { tag: 0x20051007, alias: "MRNrOfSpecificCharacterSet", vr: VR::SS },
            E { tag: 0x20051009, alias: "RescaleInterceptOriginal", vr: VR::DS },
            E { tag: 0x2005100a, alias: "RescaleSlopeOriginal", vr: VR::DS },
            E { tag: 0x2005100b, alias: "RescaleTypeOriginal", vr: VR::LO },
            E { tag: 0x2005100e, alias: "PrivateSharedSq", vr: VR::SQ },
            E { tag: 0x2005100f, alias: "PrivatePerFrameSq", vr: VR::SQ },
            E { tag: 0x20051010, alias: "MFConvTreatSpectorMixNo", vr: VR::IS },
            E { tag: 0x20051011, alias: "MFPrivateReferencedSOPInstanceUID", vr: VR::UI },
            E { tag: 0x20051012, alias: "MRImageDiffBValueNumber", vr: VR::IS },
            E { tag: 0x20051013, alias: "MRImageGradientOrientationNumber", vr: VR::IS },
            E { tag: 0x20051014, alias: "MRSeriesNrOfDiffBValues", vr: VR::SL },
            E { tag: 0x20051015, alias: "MRSeriesNrOfDiffGradOrients", vr: VR::SL },
            E { tag: 0x20051016, alias: "MRSeriesPlanMode", vr: VR::CS },
            E { tag: 0x20051017, alias: "DiffusionBMatrix", vr: VR::FD },
            E { tag: 0x20051018, alias: "PrivOperatingModeType", vr: VR::CS },
            E { tag: 0x20051019, alias: "PrivOperatingMode", vr: VR::CS },
            E { tag: 0x2005101a, alias: "MRFatSaturationTechnique", vr: VR::CS },
            E { tag: 0x2005101b, alias: "MRVersionNumberDeletedImages", vr: VR::IS },
            E { tag: 0x2005101c, alias: "MRVersionNumberDeletedSpectra", vr: VR::IS },
            E { tag: 0x2005101d, alias: "MRVersionNumberDeletedBlobsets", vr: VR::IS },
            E { tag: 0x2005101e, alias: "LUT1Offset", vr: VR::UL },
            E { tag: 0x2005101f, alias: "LUT1Range", vr: VR::UL },
            E { tag: 0x20051020, alias: "LUT1BeginColor", vr: VR::UL },
            E { tag: 0x20051021, alias: "LUT1EndColor", vr: VR::UL },
            E { tag: 0x20051022, alias: "LUT2Offset", vr: VR::UL },
            E { tag: 0x20051023, alias: "LUT2Range", vr: VR::UL },
            E { tag: 0x20051024, alias: "LUT2BeginColor", vr: VR::UL },
            E { tag: 0x20051025, alias: "LUT2EndColor", vr: VR::UL },
            E { tag: 0x20051026, alias: "ViewingHardcopyOnly", vr: VR::CS },
            E { tag: 0x20051027, alias: "PrivateEMR", vr: VR::SQ },
            E { tag: 0x20051028, alias: "MRSeriesNrOfLabelTypes", vr: VR::SL },
            E { tag: 0x20051029, alias: "MRImageLabelType", vr: VR::CS },
            E { tag: 0x2005102a, alias: "ExamPrintStatus", vr: VR::CS },
            E { tag: 0x2005102b, alias: "ExamExportStatus", vr: VR::CS },
            E { tag: 0x2005102c, alias: "ExamStorageCommitStatus", vr: VR::CS },
            E { tag: 0x2005102d, alias: "ExamMediaWriteStatus", vr: VR::CS },
            E { tag: 0x2005102e, alias: "MRSeriesDBdt", vr: VR::FL },
            E { tag: 0x2005102f, alias: "MRSeriesProtonSAR", vr: VR::FL },
            E { tag: 0x20051030, alias: "MRSeriesNonProtonSAR", vr: VR::FL },
            E { tag: 0x20051031, alias: "MRSeriesLocalSAR", vr: VR::FL },
            E { tag: 0x20051032, alias: "MRSeriesSafetyOverrideMode", vr: VR::CS },
            E { tag: 0x20051033, alias: "EVDVDJobInParamsDatetime", vr: VR::DT },
            E { tag: 0x20051034, alias: "DVDJobInParamsVolumeLabel", vr: VR::DT },
            E { tag: 0x20051035, alias: "SpectroExamcard", vr: VR::CS },
            E { tag: 0x20051036, alias: "MRRefSeriesInstanceUID", vr: VR::UI },
            E { tag: 0x20051037, alias: "ColorLUTType", vr: VR::CS },
            E { tag: 0x2005103b, alias: "MRIsCoilSurvey", vr: VR::CS },
            E { tag: 0x2005103c, alias: "MRStackTablePosLong", vr: VR::FL },
            E { tag: 0x2005103d, alias: "MRStackTablePosLat", vr: VR::FL },
            E { tag: 0x2005103e, alias: "MRStackPosteriorCoilPos", vr: VR::FL },
            E { tag: 0x2005103f, alias: "AIMDLimitsApplied", vr: VR::CS },
            E { tag: 0x20051040, alias: "AIMDHeadSARLimit", vr: VR::FL },
            E { tag: 0x20051041, alias: "AIMDWholeBodySARLimit", vr: VR::FL },
            E { tag: 0x20051042, alias: "AIMDB1RMSLimit", vr: VR::FL },
            E { tag: 0x20051043, alias: "AIMDdbDtLimit", vr: VR::FL },
            E { tag: 0x20051044, alias: "TFEFactor", vr: VR::IS },
            E { tag: 0x20051045, alias: "AttenuationCorrection", vr: VR::CS },
            E { tag: 0x20051046, alias: "FWHMShim", vr: VR::FL },
            E { tag: 0x20051047, alias: "PowerOptimization", vr: VR::FL },
            E { tag: 0x20051048, alias: "CoilQ", vr: VR::FL },
            E { tag: 0x20051049, alias: "ReceiverGain", vr: VR::FL },
            E { tag: 0x2005104a, alias: "DataWindowDuration", vr: VR::FL },
            E { tag: 0x2005104b, alias: "MixingTime", vr: VR::FL },
            E { tag: 0x2005104c, alias: "FirstEchoTime", vr: VR::FL },
            E { tag: 0x2005104d, alias: "IsB0Series", vr: VR::CS },
            E { tag: 0x2005104e, alias: "IsB1Series", vr: VR::CS },
            E { tag: 0x2005104f, alias: "VolumeSelect", vr: VR::CS },
            E { tag: 0x20051050, alias: "MRNrOfPatientOtherIDs", vr: VR::SS },
            E { tag: 0x20051051, alias: "PrivateSeriesNumber", vr: VR::IS },
            E { tag: 0x20051052, alias: "PrivateSeriesInstanceUID", vr: VR::UI },
            E { tag: 0x20051053, alias: "SplitSeriesJobParams", vr: VR::CS },
            E { tag: 0x20051054, alias: "PreferredDimensionForSplitting", vr: VR::SS },
            E { tag: 0x20051055, alias: "ImageVelocityEncodingDirection", vr: VR::FD },
            E { tag: 0x20051056, alias: "ContrastBolusNoInjections", vr: VR::SS },
            E { tag: 0x20051057, alias: "ContrastBolusAgentCode", vr: VR::LT },
            E { tag: 0x20051058, alias: "ContrastBolusAdminRouteCode", vr: VR::LT },
            E { tag: 0x20051059, alias: "ContrastBolusVolume", vr: VR::DS },
            E { tag: 0x2005105a, alias: "ContrastBolusIngredientConcentration", vr: VR::DS },
            E { tag: 0x2005105b, alias: "ContrastBolusDynamicNumber", vr: VR::IS },
            E { tag: 0x2005105c, alias: "SeriesBolusContrast", vr: VR::SQ },
            E { tag: 0x2005105d, alias: "ContrastBolusID", vr: VR::IS },
            E { tag: 0x20051060, alias: "LUTtoRGBJobParams", vr: VR::CS },
            E { tag: 0x20051092, alias: "SpecificEnergyDose", vr: VR::FL },
        ],
    },
    P {
        creator: "Philips MR Imaging DD 006",
        entries: &[
            E { tag: 0x20051053, alias: "MREFrequency", vr: VR::FL },
            E { tag: 0x20051054, alias: "MREAmplitude", vr: VR::FL },
            E { tag: 0x20051055, alias: "MREMEGFrequency", vr: VR::FL },
            E { tag: 0x20051056, alias: "MREMEGPairs", vr: VR::FL },
            E { tag: 0x20051057, alias: "MREMEGDirection", vr: VR::CS },
            E { tag: 0x20051058, alias: "MREMEGAmplitude", vr: VR::FL },
            E { tag: 0x20051059, alias: "MRENumberofPhaseDelays", vr: VR::FL },
            E { tag: 0x20051060, alias: "MRENumberofMotionCycles", vr: VR::IS },
            E { tag: 0x20051061, alias: "MREMotionMegPhaseDelay", vr: VR::FL },
            E { tag: 0x20051062, alias: "MREInversionAlgorithmVersion", vr: VR::LT },
            E { tag: 0x20051063, alias: "SagittalSliceOrder", vr: VR::CS },
            E { tag: 0x20051064, alias: "CoronalSliceOrder", vr: VR::CS },
            E { tag: 0x20051065, alias: "TransversalSliceOrder", vr: VR::CS },
            E { tag: 0x20051066, alias: "SeriesOrientation", vr: VR::CS },
            E { tag: 0x20051067, alias: "MRStackReverse", vr: VR::IS },
            E { tag: 0x20051068, alias: "MREPhaseDelayNumber", vr: VR::IS },
            E { tag: 0x20051071, alias: "NumberOfInversionDelays", vr: VR::IS },
            E { tag: 0x20051072, alias: "InversionDelayTime", vr: VR::FL },
            E { tag: 0x20051073, alias: "InversionDelayNumber", vr: VR::IS },
            E { tag: 0x20051074, alias: "MaxDbDt", vr: VR::DS },
            E { tag: 0x20051075, alias: "MaxSAR", vr: VR::DS },
            E { tag: 0x20051076, alias: "SARType", vr: VR::LT },
            E { tag: 0x20051078, alias: "MetalImplantStatus", vr: VR::CS },
            E { tag: 0x20051079, alias: "OrientationMirrorFlip", vr: VR::CS },
            E { tag: 0x20051081, alias: "SAROperationMode", vr: VR::CS },
            E { tag: 0x20051082, alias: "SpatialGradient", vr: VR::IS },
            E { tag: 0x20051083, alias: "AdditionalConstraints", vr: VR::LT },
            E { tag: 0x20051087, alias: "PIIM_MR_STUDY_B1RMS", vr: VR::DS },
            E { tag: 0x20051092, alias: "ContrastInformationSequence", vr: VR::SQ },
            E { tag: 0x20051095, alias: "Diffusion2KDTI", vr: VR::CS },
            E { tag: 0x20051096, alias: "DiffusionOrder", vr: VR::IS },
            E { tag: 0x20051097, alias: "IsJEditingSeries ", vr: VR::CS },
            E { tag: 0x20051098, alias: "MRSpectrumEditingType", vr: VR::SS },
            E { tag: 0x20051099, alias: "MRSeriesNrOfDiffOrder", vr: VR::SL },
        ],
    },
    P {
        creator: "SIEMENS MED",
        entries: &[
            E { tag: 0x70011010, alias: "Dummy", vr: VR::LT },
            E { tag: 0x70031010, alias: "Header", vr: VR::LT },
            E { tag: 0x70051010, alias: "Dummy", vr: VR::LT },
        ],
    },
    P {
        creator: "SIEMENS MED BRAIN ORIENTATION DATA",
        entries: &[
            E { tag: 0x00271006, alias: "Brain Orientation Value", vr: VR::CS },
        ],
    },
    P {
        creator: "SIEMENS MED MEASUREMENT",
        entries: &[
            E { tag: 0x00271001, alias: "Percist Cylinder Position", vr: VR::DS },
            E { tag: 0x00271002, alias: "Percist Cylinder Axis", vr: VR::DS },
            E { tag: 0x00271003, alias: "Percist Cylinder Radius", vr: VR::DS },
            E { tag: 0x00271004, alias: "Isocontour Threshold", vr: VR::LT },
            E { tag: 0x00271005, alias: "Auto Created", vr: VR::LO },
            E { tag: 0x00271006, alias: "Finding Creation Mode", vr: VR::CS },
            E { tag: 0x00271007, alias: "Pet Segmentation Threshold", vr: VR::DS },
            E { tag: 0x00271008, alias: "Change Rate", vr: VR::DS },
            E { tag: 0x00271009, alias: "Volume Doubling Time", vr: VR::DS },
            E { tag: 0x00271010, alias: "Change Rates", vr: VR::OB },
        ],
    },
    P {
        creator: "SIEMENS MED MI",
        entries: &[
            E { tag: 0x00671001, alias: "MI Scan ID", vr: VR::LT },
            E { tag: 0x00671002, alias: "Scanner Console Generation", vr: VR::LO },
            E { tag: 0x00671003, alias: "Recon Parameters", vr: VR::OB },
            E { tag: 0x00671004, alias: "Group Reconstruction ID", vr: VR::LO },
            E { tag: 0x00671005, alias: "Device IVK", vr: VR::LO },
            E { tag: 0x00671014, alias: "Raw Data Description", vr: VR::LO },
            E { tag: 0x00671016, alias: "Raw Data Series Instance UIDs", vr: VR::UI },
            E { tag: 0x00671017, alias: "Raw Data Referenced Series Instance UIDs", vr: VR::UI },
        ],
    },
    P {
        creator: "SIEMENS MED ORIENTATION RESULT",
        entries: &[
            E { tag: 0x00271005, alias: "Cardiac Orientation Value", vr: VR::CS },
        ],
    },
    P {
        creator: "SIEMENS MED PT",
        entries: &[
            E { tag: 0x00711021, alias: "Reference To Registration", vr: VR::UI },
            E { tag: 0x00711022, alias: "Decay Correction DateTime", vr: VR::DT },
            E { tag: 0x00711023, alias: "Registration Matrix", vr: VR::US },
            E { tag: 0x00711024, alias: "Table Motion", vr: VR::CS },
            E { tag: 0x00711025, alias: "Lumped Constant", vr: VR::FD },
            E { tag: 0x00711026, alias: "Histogramming Method", vr: VR::CS },
        ],
    },
    P {
        creator: "SIEMENS MED PT MU MAP",
        entries: &[
            E { tag: 0x00711001, alias: "SOP Class of Source", vr: VR::UI },
            E { tag: 0x00711002, alias: "Related Mu Map Series", vr: VR::UI },
        ],
    },
    P {
        creator: "SIEMENS MED RTSTRUCT",
        entries: &[
            E { tag: 0x00631032, alias: "GTV Marker Position", vr: VR::DS },
        ],
    },
    P {
        creator: "SIEMENS MI RWVM SUV",
        entries: &[
            E { tag: 0x00411001, alias: "SUV Decay Correction Method", vr: VR::CS },
        ],
    },
    P {
        creator: "SIEMENS PET DERIVED",
        entries: &[
            E { tag: 0x00751001, alias: "Volume Index", vr: VR::US },
            E { tag: 0x00751002, alias: "Time Slice Duration", vr: VR::IS },
            E { tag: 0x00751003, alias: "Frame Reference Time Sequence", vr: VR::SQ },
        ],
    },
    P {
        creator: "SIEMENS RA GEN",
        entries: &[
            E { tag: 0x00111026, alias: "PtopTotalSkinDose", vr: VR::SL },
            E { tag: 0x0019101f, alias: "DefaultTableIsoCenterHeight", vr: VR::SS },
            E { tag: 0x001910a2, alias: "SceneNumber", vr: VR::SL },
            E { tag: 0x001910a4, alias: "AcquisitionMode", vr: VR::SS },
            E { tag: 0x001910a5, alias: "AcquisitonFrameRate", vr: VR::SS },
            E { tag: 0x001910a6, alias: "ECGFlag", vr: VR::SL },
            E { tag: 0x001910a7, alias: "AdditionalSceneData", vr: VR::SL },
            E { tag: 0x001910a8, alias: "FileCopyFlag", vr: VR::SL },
            E { tag: 0x001910a9, alias: "PhlebovisionFlag", vr: VR::SL },
            E { tag: 0x001910aa, alias: "Co2Flag", vr: VR::SL },
            E { tag: 0x001910ab, alias: "MaxSpeed", vr: VR::SS },
            E { tag: 0x001910ac, alias: "StepWidth", vr: VR::SS },
            E { tag: 0x001910ad, alias: "DigitalAcquisitionZoom", vr: VR::SL },
            E { tag: 0x001910ff, alias: "Internal", vr: VR::SS },
            E { tag: 0x00211027, alias: "PlaneBImagesExist", vr: VR::SS },
            E { tag: 0x00211028, alias: "NoOf2MBChunks", vr: VR::SS },
            E { tag: 0x00211040, alias: "ArchiveSWInternalVersion", vr: VR::SS },
        ],
    },
    P {
        creator: "SIEMENS RA PLANE A",
        entries: &[
            E { tag: 0x00111028, alias: "FluoroTimerA", vr: VR::SL },
            E { tag: 0x00111029, alias: "FluoroSkinDoseA", vr: VR::SL },
            E { tag: 0x0011102a, alias: "TotalSkinDoseA", vr: VR::SL },
            E { tag: 0x0011102b, alias: "FluoroDoseAreaProductA", vr: VR::SL },
            E { tag: 0x0011102c, alias: "TotalDoseAreaProductA", vr: VR::SL },
            E { tag: 0x00191015, alias: "OfflineUID", vr: VR::LT },
            E { tag: 0x00191018, alias: "Internal", vr: VR::SS },
            E { tag: 0x00191019, alias: "Internal", vr: VR::SS },
            E { tag: 0x0019101a, alias: "Internal", vr: VR::SS },
            E { tag: 0x0019101b, alias: "Internal", vr: VR::SS },
            E { tag: 0x0019101c, alias: "Internal", vr: VR::SS },
            E { tag: 0x0019101d, alias: "Internal", vr: VR::SS },
            E { tag: 0x0019101e, alias: "Internal", vr: VR::SS },
            E { tag: 0x0019101f, alias: "Internal", vr: VR::SS },
            E { tag: 0x0019102a, alias: "AcquisitionDelay", vr: VR::SS },
            E { tag: 0x001910ae, alias: "IIToCoverDistance", vr: VR::SL },
            E { tag: 0x001910b0, alias: "LastFramePhase1", vr: VR::SS },
            E { tag: 0x001910b1, alias: "FrameRatePhase1", vr: VR::SS },
            E { tag: 0x001910b2, alias: "LastFramePhase2", vr: VR::SS },
            E { tag: 0x001910b3, alias: "FrameRatePhase2", vr: VR::SS },
            E { tag: 0x001910b4, alias: "LastFramePhase3", vr: VR::SS },
            E { tag: 0x001910b5, alias: "FrameRatePhase3", vr: VR::SS },
            E { tag: 0x001910b6, alias: "LastFramePhase4", vr: VR::SS },
            E { tag: 0x001910b7, alias: "FrameRatePhase4", vr: VR::SS },
            E { tag: 0x001910b8, alias: "GammaOfNativeImage", vr: VR::SS },
            E { tag: 0x001910b9, alias: "GammaOfTVSystem", vr: VR::SS },
            E { tag: 0x001910bb, alias: "PixelshiftX", vr: VR::SL },
            E { tag: 0x001910bc, alias: "PixelshiftY", vr: VR::SL },
            E { tag: 0x001910bd, alias: "MaskAverageFactor", vr: VR::SL },
            E { tag: 0x001910be, alias: "BlankingCircleFlag", vr: VR::SL },
            E { tag: 0x001910bf, alias: "CircleRowStart", vr: VR::SL },
            E { tag: 0x001910c0, alias: "CircleRowEnd", vr: VR::SL },
            E { tag: 0x001910c1, alias: "CircleColumnStart", vr: VR::SL },
            E { tag: 0x001910c2, alias: "CircleColumnEnd", vr: VR::SL },
            E { tag: 0x001910c3, alias: "CircleDiameter", vr: VR::SL },
            E { tag: 0x001910c4, alias: "RectangularCollimaterFlag", vr: VR::SL },
            E { tag: 0x001910c5, alias: "RectangleRowStart", vr: VR::SL },
            E { tag: 0x001910c6, alias: "RectangleRowEnd", vr: VR::SL },
            E { tag: 0x001910c7, alias: "RectangleColumnStart", vr: VR::SL },
            E { tag: 0x001910c8, alias: "RectangleColumnEnd", vr: VR::SL },
            E { tag: 0x001910c9, alias: "RectangleAngulation", vr: VR::SL },
            E { tag: 0x001910ca, alias: "IrisCollimatorFlag", vr: VR::SL },
            E { tag: 0x001910cb, alias: "IrisRowStart", vr: VR::SL },
            E { tag: 0x001910cc, alias: "IrisRowEnd", vr: VR::SL },
            E { tag: 0x001910cd, alias: "IrisColumnStart", vr: VR::SL },
            E { tag: 0x001910ce, alias: "IrisColumnEnd", vr: VR::SL },
            E { tag: 0x001910cf, alias: "IrisAngulation", vr: VR::SL },
            E { tag: 0x001910d1, alias: "NumberOfFramesPlane", vr: VR::SS },
            E { tag: 0x001910d2, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910d3, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910d4, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910d5, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910d6, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910d7, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910d8, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910d9, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910da, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910db, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910dc, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910dd, alias: "AnatomicBackground", vr: VR::SL },
            E { tag: 0x001910de, alias: "AutoWindowBase", vr: VR::SL },
            E { tag: 0x001910df, alias: "Internal", vr: VR::SS },
            E { tag: 0x001910e0, alias: "Internal", vr: VR::SL },
        ],
    },
    P {
        creator: "SIEMENS RA PLANE B",
        entries: &[
            E { tag: 0x00111028, alias: "FluoroTimerB", vr: VR::SL },
            E { tag: 0x00111029, alias: "FluoroSkinDoseB", vr: VR::SL },
            E { tag: 0x0011102a, alias: "TotalSkinDoseB", vr: VR::SL },
            E { tag: 0x0011102b, alias: "FluoroDoseAreaProductB", vr: VR::SL },
            E { tag: 0x0011102c, alias: "TotalDoseAreaProductB", vr: VR::SL },
        ],
    },
    P {
        creator: "SIENET",
        entries: &[
            E { tag: 0x00991002, alias: "DataObjectAttributes", vr: VR::UL },
        ],
    },
    P {
        creator: "SONOWAND AS",
        entries: &[
            E { tag: 0x01351010, alias: "UltrasoundScannerName", vr: VR::LO },
            E { tag: 0x01351011, alias: "TransducerSerial", vr: VR::LO },
            E { tag: 0x01351012, alias: "ProbeApplication", vr: VR::LO },
        ],
    },
    P {
        creator: "SPI-P-Private-DCI Release 1",
        entries: &[
            E { tag: 0x00191010, alias: "ECGTimeMapDataBitsAllocated", vr: VR::UN },
            E { tag: 0x00191011, alias: "ECGTimeMapDataBitsStored", vr: VR::UN },
            E { tag: 0x00191012, alias: "ECGTimeMapDataHighBit", vr: VR::UN },
            E { tag: 0x00191013, alias: "ECGTimeMapDataRepresentation", vr: VR::UN },
            E { tag: 0x00191014, alias: "ECGTimeMapDataSmallestDataValue", vr: VR::UN },
            E { tag: 0x00191015, alias: "ECGTimeMapDataLargestDataValue", vr: VR::UN },
            E { tag: 0x00191016, alias: "ECGTimeMapDataNumberOfDataValues", vr: VR::UN },
            E { tag: 0x00191017, alias: "ECGTimeMapData", vr: VR::UN },
        ],
    },
    P {
        creator: "SPI-P-Private_ICS Release 1",
        entries: &[
            E { tag: 0x00291043, alias: "Unknown", vr: VR::SQ },
            E { tag: 0x00291044, alias: "Unknown", vr: VR::SQ },
        ],
    },
    P {
        creator: "SVISION",
        entries: &[
            E { tag: 0x00251021, alias: "Unknown", vr: VR::UI },
        ],
    },
];
