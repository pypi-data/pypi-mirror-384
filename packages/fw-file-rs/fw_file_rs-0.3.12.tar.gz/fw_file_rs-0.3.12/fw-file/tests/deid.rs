use std::collections::HashMap;

use dicom_core::{Tag, VR};
use fw_file::dcm::{CreateDicomValue, DeidProfile, ProfileParseError, create_dcm_as_bytes};
use rstest::rstest;

#[rstest]
#[case("StudyDate")]
#[case("00080020")]
#[case("(0008, 0020)")]
#[case("0x00080020")]
fn test_deid_replace_study_date_by_various_tag_formats(#[case] tag_identifier: &str) {
    let tags = HashMap::from([
        ("PatientName", "Test^Patient".into()),
        ("StudyDate", "20000101".into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = format!(
        r#"
version: 1
name: test profile
dicom:
  fields:
    - name: "{tag_identifier}"
      replace-with: "20220101"
"#
    );

    let profile = DeidProfile::from_yaml(&yaml).unwrap();
    let result = profile.deid_dcm(&dcm).expect("deid failed");

    let obj = dicom_object::from_reader(result.as_slice()).unwrap();
    let val = obj.element_by_name("StudyDate").unwrap().to_str().unwrap();
    assert_eq!(val, "20220101");
}

#[test]
fn test_deid_remove_field() {
    let tags = HashMap::from([
        ("PatientName", "Test^Patient".into()),
        ("PatientID", "123456".into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = r#"
version: 1
name: test profile
dicom:
  fields:
    - name: PatientID
      remove: true
"#;

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).expect("deid failed");

    let obj = dicom_object::from_reader(result.as_slice()).unwrap();
    assert!(obj.element_by_name("PatientID").is_err());
    let val = obj
        .element_by_name("PatientName")
        .unwrap()
        .to_str()
        .unwrap();
    assert_eq!(val, "Test^Patient");
}

#[test]
fn test_validate_vr_date_invalid() {
    let tags = HashMap::from([("StudyDate", "20000101".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = r#"
version: 1
name: test profile
dicom:
  fields:
    - name: StudyDate
      replace-with: "notadate"
"#;

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let err = profile.deid_dcm(&dcm).unwrap_err();
    assert!(err.contains("cannot be parsed as DA"));
}

#[test]
fn test_deid_replace_patient_name() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  fields:
    - name: PatientName
      replace-with: "Anon^Patient"
"#;

    let tags = HashMap::from([("PatientName", "Test^Patient".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    let val = obj
        .element_by_name("PatientName")
        .unwrap()
        .to_str()
        .unwrap();
    assert_eq!(val, "Anon^Patient");
}

#[test]
fn test_deid_hash_patient_name() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  fields:
    - name: PatientName
      hash: true
"#;

    let tags = HashMap::from([("PatientName", "Test^Patient".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    let val = obj
        .element_by_name("PatientName")
        .unwrap()
        .to_str()
        .unwrap();
    assert_eq!(val, "7a33e38537816612");
}

#[test]
fn test_deid_hash_study_instance_uid() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  fields:
    - name: StudyInstanceUID
      hashuid: true
"#;

    let tags = HashMap::from([(
        "StudyInstanceUID",
        "1.2.840.113619.6.283.4.983142589.7316.1300473420.841".into(),
    )]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    let val = obj
        .element_by_name("StudyInstanceUID")
        .unwrap()
        .to_str()
        .unwrap();
    assert_eq!(
        val,
        "1.2.840.113619.551726.420312.177022.222461.230571.501817.841"
    );
}

#[test]
fn test_deid_increment_patient_birth_date() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  date-increment: 11
  fields:
    - name: PatientBirthDate
      increment-date: true
"#;

    let tags = HashMap::from([("PatientBirthDate", "19990101".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    let val = obj
        .element_by_name("PatientBirthDate")
        .unwrap()
        .to_str()
        .unwrap();
    assert_eq!(val, "19990112");
}

#[test]
fn test_deid_increment_empty_patient_birth_date() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  date-increment: 11
  fields:
    - name: PatientBirthDate
      increment-date: true
"#;

    let tags = HashMap::from([("PatientBirthDate", "".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    let val = obj
        .element_by_name("PatientBirthDate")
        .unwrap()
        .to_str()
        .unwrap();
    assert_eq!(val, "");
}

#[test]
fn test_deid_jitter_patient_weight() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  jitter-range: 10
  jitter-type: int
  fields:
    - name: PatientWeight
      jitter: true
"#;

    let tags = HashMap::from([("PatientWeight", 55.into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    let val = obj
        .element_by_name("PatientWeight")
        .unwrap()
        .to_str()
        .unwrap()
        .trim()
        .parse::<i64>()
        .unwrap();
    assert_ne!(val, 55);
}

#[test]
fn test_deid_patient_age_from_birthdate() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  patient-age-from-birthdate: true
  patient-age-units: Y
  fields:
    - name: PatientBirthDate
      remove: true
"#;

    let tags = HashMap::from([
        ("PatientBirthDate", "20000101".into()),
        ("StudyDate", "20220101".into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    assert!(obj.element_by_name("PatientBirthDate").is_err());
    let val = obj.element_by_name("PatientAge").unwrap().to_str().unwrap();
    assert_eq!(val, "022Y");
}

#[test]
fn test_deid_recurse_sequence() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  recurse-sequence: true
  fields:
    - name: StudyInstanceUID
      hashuid: true
"#;

    let seq_item = HashMap::from([
        (
            "StudyInstanceUID",
            "1.2.840.113619.6.283.4.983142589.7316.1300473420.841".into(),
        ),
        ("StudyDate", "20220101".into()),
    ]);
    let tags = HashMap::from([("ReferencedStudySequence", vec![seq_item].into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    let study_uid = if let dicom_core::DicomValue::Sequence(seq) = obj
        .element_by_name("ReferencedStudySequence")
        .unwrap()
        .value()
    {
        seq.items()
            .get(0)
            .and_then(|item| item.element_by_name("StudyInstanceUID").ok())
            .and_then(|e| e.to_str().ok())
            .unwrap()
    } else {
        panic!("ReferencedStudySequence is not a sequence!");
    };
    assert_eq!(
        study_uid,
        "1.2.840.113619.551726.420312.177022.222461.230571.501817.841"
    );
}

#[test]
fn test_deid_replace_with_sequence() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  recurse-sequence: true
  fields:
    - name: ReferencedStudySequence
      replace-with: []
"#;

    let seq_item = HashMap::from([(
        "StudyInstanceUID",
        "1.2.840.113619.6.283.4.983142589.7316.1300473420.841".into(),
    )]);
    let tags = HashMap::from([("ReferencedStudySequence", vec![seq_item].into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    let sequence = obj.element_by_name("ReferencedStudySequence").unwrap();
    match sequence.value() {
        dicom_core::DicomValue::Sequence(seq) => {
            assert!(seq.items().is_empty(), "Sequence is not empty!");
        }
        _ => panic!("ReferencedStudySequence is not a sequence!"),
    }
}

#[test]
fn test_deid_remove_undefined() {
    let yaml = r#"
version: 1
name: test profile
dicom:
  remove-undefined: true
  fields:
    - name: ReferencedStudySequence.*.StudyInstanceUID
    - name: PatientAge
      replace-with: REDACTED
"#;

    let seq_item = HashMap::from([
        (
            "StudyInstanceUID",
            "1.2.840.113619.6.283.4.983142589.7316.1300473420.841".into(),
        ),
        ("StudyDate", "20220101".into()),
    ]);
    let tags = HashMap::from([
        ("PatientAge", "022Y".into()),
        ("ReferencedStudySequence", vec![seq_item].into()),
        (
            "StudyInstanceUID",
            "1.2.840.113619.6.283.4.983142589.7316.1300473420.841".into(),
        ),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).unwrap();
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();

    assert!(obj.element_by_name("StudyInstanceUID").is_err());
    let study_uid = if let dicom_core::DicomValue::Sequence(seq) = obj
        .element_by_name("ReferencedStudySequence")
        .unwrap()
        .value()
    {
        seq.items()
            .get(0)
            .and_then(|item| item.element_by_name("StudyInstanceUID").ok())
            .and_then(|e| e.to_str().ok())
            .unwrap()
    } else {
        panic!("ReferencedStudySequence is not a sequence!");
    };
    assert_eq!(
        study_uid,
        "1.2.840.113619.6.283.4.983142589.7316.1300473420.841"
    );
    let val = obj.element_by_name("PatientAge").unwrap().to_str().unwrap();
    assert_eq!(val, "REDACTED");
}

#[test]
fn test_deid_regex_field() {
    let tags = HashMap::from([
        ("StudyDate", "20250908".into()),
        ("SeriesDate", "20250908".into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = r#"
version: 1
name: test profile
dicom:
  date-increment: 10
  fields:
    - regex: .*Date.*
      increment-date: true
"#;

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).expect("deid failed");

    let obj = dicom_object::from_reader(result.as_slice()).unwrap();
    let val = obj.element_by_name("StudyDate").unwrap().to_str().unwrap();
    assert_eq!(val, "20250918");
    let val = obj.element_by_name("SeriesDate").unwrap().to_str().unwrap();
    assert_eq!(val, "20250918");
}

#[test]
fn test_deid_regex_field_hex() {
    let tags = HashMap::from([
        ("StudyDate", "20250908".into()),
        ("SeriesDate", "20250908".into()),
        ("PatientBirthDate", "20000101".into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = r#"
version: 1
name: test profile
dicom:
  date-increment: 10
  fields:
    - regex: 0008002.*
      increment-date: true
"#;

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).expect("deid failed");

    let obj = dicom_object::from_reader(result.as_slice()).unwrap();
    let val = obj.element_by_name("StudyDate").unwrap().to_str().unwrap();
    assert_eq!(val, "20250918");
    let val = obj.element_by_name("SeriesDate").unwrap().to_str().unwrap();
    assert_eq!(val, "20250918");
    let val = obj
        .element_by_name("PatientBirthDate")
        .unwrap()
        .to_str()
        .unwrap();
    assert_eq!(val, "20000101");
}

#[test]
fn test_deid_private_tag() {
    let tags = HashMap::from([
        ("0009,0010", "GEMS_IMAG_01".into()),
        (
            "0009,1001",
            CreateDicomValue::PrimitiveAndVR("some value".into(), VR::LO),
        ),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = r#"
version: 1
name: test profile
dicom:
  fields:
    - name: (0009, "GEMS_IMAG_01", 01)
      replace-with: "REDACTED"
"#;

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).expect("deid failed");

    let obj = dicom_object::from_reader(result.as_slice()).unwrap();
    let val = obj.element(Tag(0x0009, 0x1001)).unwrap().to_str().unwrap();
    assert_eq!(val, "REDACTED");
}

#[test]
fn test_deid_replace_with_upsert_private_tag() {
    let tags = HashMap::from([("StudyDate", "20250908".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = r#"
version: 1
name: test profile
dicom:
  fields:
    - name: (0031, "AGFA PACS Archive Mirroring 1.0", 01)
      replace-with: "1758127490"
"#;

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).expect("deid failed");

    let obj = dicom_object::from_reader(result.as_slice()).unwrap();
    let val = obj.element(Tag(0x0031, 0x0001)).unwrap().to_str().unwrap();
    assert_eq!(val, "AGFA PACS Archive Mirroring 1.0");
    let val = obj.element(Tag(0x0031, 0x0101)).unwrap().to_str().unwrap();
    assert_eq!(val, "1758127490");
}

#[test]
fn test_deid_remove_private_tags() {
    let tags = HashMap::from([
        ("StudyDate", "20250908".into()),
        ("2005,0010", "Philips MR Imaging DD 001".into()),
        (
            "2005,1070",
            CreateDicomValue::PrimitiveAndVR("some value".into(), VR::LO),
        ),
        (
            "2005,1071",
            CreateDicomValue::PrimitiveAndVR(2.1.into(), VR::FL),
        ),
        ("2005,0020", "Philips MR Imaging DD 002".into()),
        (
            "2005,202d",
            CreateDicomValue::PrimitiveAndVR("value".into(), VR::FL),
        ),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = r#"
version: 1
name: test profile
dicom:
  remove-private-tags: true
  fields:
    - name: (2005, "Philips MR Imaging DD 001", 70)
      replace-with: "REDACTED"
"#;

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).expect("deid failed");

    let obj = dicom_object::from_reader(result.as_slice()).unwrap();
    // remove private tags
    assert!(obj.element(Tag(0x2005, 0x0020)).is_err());
    assert!(obj.element(Tag(0x2005, 0x202d)).is_err());
    assert!(obj.element(Tag(0x2005, 0x1071)).is_err());
    // other tags are kept
    let val = obj.element_by_name("StudyDate").unwrap().to_str().unwrap();
    assert_eq!(val, "20250908");
    let val = obj.element(Tag(0x2005, 0x0010)).unwrap().to_str().unwrap();
    assert_eq!(val, "Philips MR Imaging DD 001");
    let val = obj.element(Tag(0x2005, 0x1070)).unwrap().to_str().unwrap();
    assert_eq!(val, "REDACTED");
}

#[test]
fn test_profile_deid_repeater_tag() {
    let tags = HashMap::from([
        ("6000,0022", "some value".into()),
        ("6002,0022", "some value".into()),
        ("6004,0022", "some value".into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let dcm = buffer.get_ref().clone();

    let yaml = r#"
version: 1
name: test profile
dicom:
  remove-private-tags: true
  fields:
    - name: (60xx, 0022)
      replace-with: REDACTED
"#;

    let profile = DeidProfile::from_yaml(yaml).unwrap();
    let result = profile.deid_dcm(&dcm).expect("deid failed");
    let obj = dicom_object::from_reader(result.as_slice()).unwrap();
    let val = obj.element(Tag(0x6000, 0x0022)).unwrap().to_str().unwrap();
    assert_eq!(val, "REDACTED");
    let val = obj.element(Tag(0x6002, 0x0022)).unwrap().to_str().unwrap();
    assert_eq!(val, "REDACTED");
    let val = obj.element(Tag(0x6004, 0x0022)).unwrap().to_str().unwrap();
    assert_eq!(val, "REDACTED");
}

#[test]
fn test_profile_unsupported_version() {
    let yaml = r#"
version: 99
name: test
dicom: {}
"#;

    let err = DeidProfile::from_yaml(yaml).unwrap_err();
    match err {
        ProfileParseError::UnsupportedVersion(v) => assert_eq!(v, 99),
        e => panic!("Expected UnsupportedVersion, got {e:?}"),
    }
}
