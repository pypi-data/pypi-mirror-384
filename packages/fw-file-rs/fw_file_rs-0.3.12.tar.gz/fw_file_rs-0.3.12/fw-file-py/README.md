# fw-file-rs

Python bindings for the [fw-file-rs][fw-file-rs-repo] Rust library.

## Usage

```py
from fw_file_rs.dcm import Context, read_until_pixels

# Create a configured context using the builder pattern
ctx = (Context()
    .parse_include([
        "InstitutionAddress",
        "InstitutionName",
    ])
    .group_by(["StudyInstanceUID", "SeriesInstanceUID"])
    .split_localizer(True)
    .deid_profile("""
        version: 1
        name: profile
        dicom:
          fields:
            - name: PatientName
              replace-with: REDACTED
    """))
# Read DICOM header bytes from file
header_bytes = ctx.read_until_pixels("/path/to/dicom/file.dcm")
# Extract metadata using the configured context
meta = ctx.parse_header(header_bytes)
# Get Flywheel-specific metadata
fw_meta = ctx.get_fw_meta(meta)
# Group DICOM files by configured tags with localizer splitting
path_meta_pairs = [("1.dcm", meta)]
groups = ctx.group_series(path_meta_pairs)
# De-identify the DICOM header using the configured profile
deid_header = ctx.deid_header(header_bytes)
```

[fw-file-rs-repo]: https://gitlab.com/flywheel-io/tools/lib/fw-file-rs
