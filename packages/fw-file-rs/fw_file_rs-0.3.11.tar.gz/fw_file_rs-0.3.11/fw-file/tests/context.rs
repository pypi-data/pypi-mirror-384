use std::collections::HashMap;

use fw_file::dcm::{Context, create_dcm_as_bytes};

#[test]
fn test_context() {
    let ctx = Context::new()
        .include_tags(vec!["PatientName", "PatientID"])
        .mappings(vec!["custom_mapping"])
        .max_size(2048)
        .stop_at_tags(vec![(0x7fe0, 0x0010)]);

    let tags = HashMap::from([
        ("PatientID", "CHAIN001".into()),
        ("PatientName", "Chain^Test".into()),
        ("StudyInstanceUID", "1.2.3.4.5.6".into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();

    let header = ctx.parse_header(bytes).expect("Parse failed");
    assert!(header.contains_key("PatientName"));
    assert!(header.contains_key("PatientID"));

    let fw_meta = ctx.get_fw_meta(header).expect("FW meta failed");
    assert!(fw_meta.contains_key("subject.label"));
}

#[test]
fn test_context_deid_header_without_profile() {
    let ctx = Context::new();

    let tags = HashMap::from([("PatientName", "Test^Patient".into())]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();

    let result = ctx.deid_header(bytes);
    assert!(result.is_err());
    assert_eq!(
        result.unwrap_err(),
        "No de-identification profile configured"
    );
}

#[test]
fn test_context_deid_header_with_profile() {
    let yaml = r#"
version: 1
rules:
  - action: remove
    tag: PatientName
"#;
    let ctx = Context::new()
        .deid_profile(yaml)
        .expect("Profile creation failed");

    let tags = HashMap::from([
        ("PatientName", "Test^Patient".into()),
        ("PatientID", "TEST123".into()),
    ]);
    let buffer = create_dcm_as_bytes(tags).expect("Failed to create DICOM");
    let bytes = buffer.get_ref();

    let result = ctx.deid_header(bytes);
    assert!(result.is_ok());
}
