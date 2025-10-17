from fw_file_rs.dcm import create_dcm_as_bytes, parse_header, get_fw_meta


def test_parse_header():
    dcm_bytes = create_dcm_as_bytes(
        {
            "PatientID": "test",
            "ImageOrientationPatient": [1, 0, 0, 0, 1, 0],
            "PatientName": None,
        }
    )
    meta = parse_header(dcm_bytes)
    assert meta == {
        "PatientID": "test",
        "ImageOrientationPatient": [1, 0, 0, 0, 1, 0],
        "PatientName": None,
    }


def test_get_fw_meta():
    meta = {"PatientName": "Test^Patient", "PatientID": "123456"}
    fw_meta = get_fw_meta(meta)
    expected = {
        "subject.label": "123456",
        "subject.lastname": "Test",
        "subject.firstname": "Patient",
    }
    assert fw_meta == expected
