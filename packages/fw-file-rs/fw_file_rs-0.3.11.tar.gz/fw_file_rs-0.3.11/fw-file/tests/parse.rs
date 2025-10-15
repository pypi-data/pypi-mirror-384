use std::collections::HashMap;

use fw_file::dcm::{
    CreateDicomValue, DEFAULT_TAGS, DicomValue, create_dcm_as_bytes, get_fw_meta, parse_header,
};

#[test]
fn test_get_dcm_meta() {
    let tags = HashMap::from([
        ("PatientName", "Test^Patient".into()),
        ("PatientID", "123456".into()),
    ]);

    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();

    let meta = parse_header(bytes, &["PatientName"]).expect("Failed to get DICOM meta");
    let patient_name = meta.get("PatientName").expect("Missing PatientName");

    assert_eq!(
        patient_name,
        &DicomValue::Str("Test^Patient".to_string()),
        "Unexpected PatientName value"
    );
}

fn create_dcm_and_get_meta(tags: HashMap<&str, CreateDicomValue>) -> HashMap<String, String> {
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();
    let dcm_meta = parse_header(bytes, DEFAULT_TAGS).expect("Failed to get dcm meta");
    get_fw_meta(dcm_meta, &[]).expect("Failed to get FW meta")
}

#[test]
fn test_get_fw_meta_basic_fields() {
    let tags = HashMap::from([
        ("PatientID", "SUBJ001".into()),
        ("PatientName", "Test^Patient".into()),
        ("PatientSex", "M".into()),
        ("StudyInstanceUID", "1.2.3.4.5.6.7.8.9".into()),
        ("SeriesInstanceUID", "1.2.3.4.5.6.7.8.10".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(meta.get("subject.label"), Some(&"SUBJ001".to_string()));
    assert_eq!(meta.get("subject.firstname"), Some(&"Patient".to_string()));
    assert_eq!(meta.get("subject.lastname"), Some(&"Test".to_string()));
    assert_eq!(meta.get("subject.sex"), Some(&"M".to_string()));
    assert_eq!(
        meta.get("session.uid"),
        Some(&"1.2.3.4.5.6.7.8.9".to_string())
    );
    assert_eq!(
        meta.get("acquisition.uid"),
        Some(&"1.2.3.4.5.6.7.8.10".to_string())
    );
}

#[test]
fn test_get_fw_meta_patient_name_parsing() {
    let tags = HashMap::from([
        ("PatientName", "Doe^John^Middle".into()),
        ("PatientID", "123".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(meta.get("subject.firstname"), Some(&"John".to_string()));
    assert_eq!(meta.get("subject.lastname"), Some(&"Doe".to_string()));

    let tags = HashMap::from([
        ("PatientName", "John Doe".into()),
        ("PatientID", "124".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(meta.get("subject.firstname"), Some(&"John".to_string()));
    assert_eq!(meta.get("subject.lastname"), Some(&"Doe".to_string()));

    let tags = HashMap::from([("PatientName", "Cher".into()), ("PatientID", "125".into())]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(meta.get("subject.firstname"), None);
    assert_eq!(meta.get("subject.lastname"), Some(&"Cher".to_string()));
}

#[test]
fn test_get_fw_meta_session_age_from_patient_age() {
    let tags = HashMap::from([
        ("PatientAge", "030Y".into()),
        ("PatientID", "AGE001".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    let expected_seconds = (30.0 * 365.25 * 86400.0) as i64;
    assert_eq!(meta.get("session.age"), Some(&expected_seconds.to_string()));

    let age_tests = vec![
        ("010M", 10.0 * 30.0 * 86400.0), // months
        ("005W", 5.0 * 7.0 * 86400.0),   // weeks
        ("100D", 100.0 * 86400.0),       // days
    ];

    for (age_str, expected_seconds) in age_tests {
        let tags = HashMap::from([
            ("PatientAge", age_str.into()),
            ("PatientID", "AGE_TEST".into()),
        ]);
        let meta = create_dcm_and_get_meta(tags);

        assert_eq!(
            meta.get("session.age"),
            Some(&(expected_seconds as i64).to_string())
        );
    }
}

#[test]
fn test_get_fw_meta_session_labels() {
    let tags = HashMap::from([
        ("StudyDescription", "Brain MRI Study".into()),
        ("StudyInstanceUID", "1.2.3.4.5".into()),
        ("PatientID", "LABEL001".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(
        meta.get("session.label"),
        Some(&"Brain MRI Study".to_string())
    );

    let tags = HashMap::from([
        ("StudyInstanceUID", "1.2.3.4.6".into()),
        ("PatientID", "LABEL002".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(meta.get("session.label"), Some(&"1.2.3.4.6".to_string()));
}

#[test]
fn test_get_fw_meta_acquisition_labels() {
    let tags = HashMap::from([
        ("SeriesDescription", "T1 MPRAGE".into()),
        ("SeriesNumber", 3i64.into()),
        ("SeriesInstanceUID", "1.2.3.4.5.6".into()),
        ("PatientID", "ACQ001".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(
        meta.get("acquisition.label"),
        Some(&"3 - T1 MPRAGE".to_string())
    );

    let tags = HashMap::from([
        ("ProtocolName", "FLAIR Protocol".into()),
        ("SeriesInstanceUID", "1.2.3.4.5.7".into()),
        ("PatientID", "ACQ002".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(
        meta.get("acquisition.label"),
        Some(&"FLAIR Protocol".to_string())
    );
}

#[test]
fn test_get_fw_meta_operators_name() {
    let tags = HashMap::from([
        ("OperatorsName", "Smith^John".into()),
        ("PatientID", "OP001".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(
        meta.get("session.operator"),
        Some(&"John Smith".to_string())
    );

    let tags = HashMap::from([
        (
            "OperatorsName",
            vec!["Smith^John".to_string(), "Doe^Jane".to_string()].into(),
        ),
        ("PatientID", "OP002".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(
        meta.get("session.operator"),
        Some(&"John Smith, Jane Doe".to_string())
    );
}

#[test]
fn test_get_fw_meta_weight() {
    let tags = HashMap::from([
        ("PatientWeight", 70.5f64.into()),
        ("PatientID", "WEIGHT001".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert_eq!(meta.get("session.weight"), Some(&"70.5".to_string()));
}

#[test]
fn test_get_fw_meta_timestamps() {
    let tags = HashMap::from([
        ("StudyDate", "20231215".into()),
        ("StudyTime", "143022.123456".into()),
        ("SeriesDate", "20231216".into()),
        ("SeriesTime", "150000.000000".into()),
        ("AcquisitionDateTime", "20231217150030.123456+0100".into()),
        ("PatientID", "TIME001".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    assert!(meta.contains_key("session.timestamp"));
    assert!(meta.contains_key("acquisition.timestamp"));
    let session_ts = meta.get("session.timestamp").unwrap();
    assert!(session_ts.contains("2023-12-15"));
    assert!(session_ts.contains("T"));
    let acq_ts = meta.get("acquisition.timestamp").unwrap();
    assert!(acq_ts.contains("2023-12-17"));
    assert!(acq_ts.contains("T"));
}

#[test]
fn test_get_fw_meta_uid_timestamp_extraction() {
    let uid_with_timestamp = "1.2.840.113619.2.55.3.604688119.868.20250923111111.456";
    let tags = HashMap::from([
        ("StudyInstanceUID", uid_with_timestamp.into()),
        ("PatientID", "UID001".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);
    assert_eq!(
        meta.get("session.timestamp"),
        Some(&"2025-09-23T11:11:11+00:00".to_string())
    );
}

#[test]
fn test_get_fw_meta_timezone_handling() {
    let tags = HashMap::from([
        ("StudyDate", "20231215".into()),
        ("StudyTime", "143022.123456".into()),
        ("TimezoneOffsetFromUTC", "0500".into()),
        ("PatientID", "TZ001".into()),
    ]);
    let meta = create_dcm_and_get_meta(tags);

    let session_ts = meta.get("session.timestamp").unwrap();
    println!("{:?}", session_ts);
    assert!(session_ts.contains("+05:00") || session_ts.contains("Z"));
}

#[test]
fn test_get_fw_meta_empty_dicom() {
    let empty_tags = HashMap::new();
    let buffer = create_dcm_as_bytes(empty_tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();
    let dcm_meta = parse_header(bytes, DEFAULT_TAGS).expect("Failed to get dcm meta");
    let result = get_fw_meta(dcm_meta, &[]);

    assert!(result.is_ok());
    let meta = result.unwrap();
    assert!(meta.is_empty() || meta.len() == 0);
}

#[test]
fn test_get_dcm_value_with_empty_string() {
    let tags = HashMap::from([("PatientName", "".into()), ("PatientID", "TEST001".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();

    let meta = parse_header(bytes, &["PatientName"]).expect("Failed to parse header");
    let value = meta.get("PatientName").expect("PatientName should exist");

    match value {
        DicomValue::Empty => (),
        _ => panic!("Expected empty string or Empty, got: {:?}", value),
    }
}

#[test]
fn test_get_dcm_value_with_normal_values() {
    let tags = HashMap::from([
        ("PatientName", "Test^Patient".into()),
        ("PatientID", "123456".into()),
        ("SeriesNumber", 5i64.into()),
        ("PatientWeight", 70.5f64.into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();

    let meta = parse_header(bytes, &["PatientName", "SeriesNumber", "PatientWeight"])
        .expect("Failed to parse header");

    let value = meta.get("PatientName").expect("PatientName should exist");
    assert_eq!(value, &DicomValue::Str("Test^Patient".to_string()));
    let value = meta.get("SeriesNumber").expect("SeriesNumber should exist");
    assert_eq!(value, &DicomValue::Int(5));
    let value = meta
        .get("PatientWeight")
        .expect("PatientWeight should exist");
    assert_eq!(value, &DicomValue::Float(70.5));
}

#[test]
fn test_get_dcm_value_with_multi_values() {
    let tags = HashMap::from([
        ("PatientID", "MULTI001".into()),
        (
            "ImageOrientationPatient",
            vec![1.0f64, 0.0, 0.0, 0.0, 1.0, 0.0].into(),
        ),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();

    let meta = parse_header(bytes, &["ImageOrientationPatient"]).expect("Failed to parse header");
    let value = meta
        .get("ImageOrientationPatient")
        .expect("ImageOrientationPatient should exist");

    match value {
        DicomValue::Floats(v) => assert_eq!(v, &vec![1.0, 0.0, 0.0, 0.0, 1.0, 0.0]),
        _ => panic!("Expected Floats, got: {:?}", value),
    }
}

#[test]
fn test_get_dcm_value_missing_tag() {
    let tags = HashMap::from([("PatientID", "MISSING001".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();

    let meta = parse_header(bytes, &["PatientName"]).expect("Failed to parse header");

    assert!(
        !meta.contains_key("PatientName"),
        "PatientName should not exist in metadata"
    );
}

#[test]
fn test_get_dcm_value_display() {
    assert_eq!(DicomValue::Int(42).to_string(), "42");
    assert_eq!(DicomValue::Float(3.14).to_string(), "3.14");
    assert_eq!(DicomValue::Str("test".to_string()).to_string(), "test");
    assert_eq!(
        DicomValue::Strings(vec!["a".to_string(), "b".to_string()]).to_string(),
        "[a, b]"
    );
    assert_eq!(DicomValue::Ints(vec![1, 2, 3]).to_string(), "[1, 2, 3]");
    assert_eq!(DicomValue::Floats(vec![1.1, 2.2]).to_string(), "[1.1, 2.2]");
    assert_eq!(DicomValue::Empty.to_string(), "");
}
