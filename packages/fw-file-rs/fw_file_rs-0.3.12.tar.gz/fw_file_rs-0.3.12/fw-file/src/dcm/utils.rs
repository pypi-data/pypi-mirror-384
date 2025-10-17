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

use crate::dcm::dict::PRIVATE_DICT;

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
                // Handle sequences by parsing them recursively
                if header.vr == VR::SQ {
                    match parse_sequence_items(&mut decoder, header.len) {
                        Ok(seq_items) => {
                            let seq_value =
                                dicom_core::value::DataSetSequence::<InMemDicomObject>::new(
                                    seq_items, header.len,
                                );
                            let element = DataElement::new(header.tag, header.vr, seq_value);
                            dataset.put(element);
                            element_count += 1;
                        }
                        Err(_) => {
                            // If we can't parse the sequence, try to skip it
                            if header.len.0 != 0xFFFFFFFF {
                                decoder.skip_bytes(header.len.0).ok();
                            }
                        }
                    }
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

fn parse_sequence_items<R: Read + Seek>(
    decoder: &mut DynStatefulDecoder<&mut R>,
    seq_len: dicom_core::Length,
) -> Result<Vec<InMemDicomObject>, String> {
    let mut items = Vec::new();
    let seq_len = seq_len.0;
    let is_undefined = seq_len == 0xFFFFFFFF;
    let start_pos = decoder.position();

    loop {
        if !is_undefined && (decoder.position() - start_pos) >= seq_len as u64 {
            break;
        }

        match decoder.decode_item_header() {
            Ok(item_header) => {
                match item_header {
                    SequenceItemHeader::Item { len } => {
                        let item_start = decoder.position();
                        let mut item_obj =
                            InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
                        let item_len = len.0;
                        let is_item_undefined = item_len == 0xFFFFFFFF;

                        loop {
                            let curr_pos = decoder.position() - item_start;
                            if !is_item_undefined && curr_pos >= item_len as u64 {
                                break;
                            }

                            match decoder.decode_header() {
                                Ok(elem_header) => {
                                    // Check for Item Delimiter
                                    if elem_header.tag.0 == 0xFFFE && elem_header.tag.1 == 0xE00D {
                                        break;
                                    }

                                    if elem_header.vr == VR::SQ {
                                        match parse_sequence_items(decoder, elem_header.len) {
                                            Ok(nested_items) => {
                                                let seq_value = dicom_core::value::DataSetSequence::<
                                                    InMemDicomObject,
                                                >::new(
                                                    nested_items, elem_header.len
                                                );
                                                let element = DataElement::new(
                                                    elem_header.tag,
                                                    elem_header.vr,
                                                    seq_value,
                                                );
                                                item_obj.put(element);
                                            }
                                            Err(_) => {
                                                if elem_header.len.0 != 0xFFFFFFFF {
                                                    decoder.skip_bytes(elem_header.len.0).ok();
                                                }
                                            }
                                        }
                                    } else {
                                        match decoder.read_value(&elem_header) {
                                            Ok(value) => {
                                                let element = DataElement::new(
                                                    elem_header.tag,
                                                    elem_header.vr,
                                                    value,
                                                );
                                                item_obj.put(element);
                                            }
                                            Err(_) => {
                                                if elem_header.len.0 != 0xFFFFFFFF {
                                                    decoder.skip_bytes(elem_header.len.0).ok();
                                                }
                                            }
                                        }
                                    }
                                }
                                Err(_) => {
                                    break;
                                }
                            }
                        }

                        items.push(item_obj);
                    }
                    SequenceItemHeader::ItemDelimiter => {
                        // Item delimiter encountered (handled above)
                        continue;
                    }
                    SequenceItemHeader::SequenceDelimiter => {
                        // End of sequence
                        break;
                    }
                }
            }
            Err(_) => {
                // Couldn't decode item header, end of sequence
                break;
            }
        }
    }

    Ok(items)
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

pub fn get_private_tag_vr(group: u16, element: u8, creator: &str) -> Option<VR> {
    let tag = ((group as u32) << 16) | ((0x1000 | (element as u16 & 0xFF)) as u32);
    PRIVATE_DICT.get(creator)?.get(&tag).map(|entry| entry.vr)
}
