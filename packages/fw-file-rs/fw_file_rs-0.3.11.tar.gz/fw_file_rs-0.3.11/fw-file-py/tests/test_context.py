from fw_file_rs.dcm import Context, create_dcm_as_bytes


def test_context_default():
    ctx = Context.default()

    tags = {
        "PatientID": "Patient1",
        "PatientName": "Patient^Test",
        "StudyInstanceUID": "1.2.3.4.5.6",
    }
    dcm_bytes = create_dcm_as_bytes(tags)

    header = ctx.parse_header(dcm_bytes)
    assert header["PatientID"] == "Patient1"
    assert header["PatientName"] == "Patient^Test"
    assert header["StudyInstanceUID"] == "1.2.3.4.5.6"
    meta = ctx.get_fw_meta(header)
    assert meta["subject.label"] == "Patient1"
    assert meta["subject.firstname"] == "Test"
    assert meta["subject.lastname"] == "Patient"
    assert meta["session.label"] == "1.2.3.4.5.6"


def test_context_deid_header_with_profile():
    yaml = """
version: 1
rules:
  - action: remove
    tag: PatientName
"""
    ctx = Context().deid_profile(yaml)

    tags = {
        "PatientName": "Test^Patient",
        "PatientID": "TEST123",
    }
    dcm_bytes = create_dcm_as_bytes(tags)

    result = ctx.deid_header(dcm_bytes)
    assert isinstance(result, bytes)
    assert len(result) > 0
