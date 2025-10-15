# fw-file-rs

A Rust library for reading, parsing, and de-identifying DICOM files with bindings for Python and JavaScript/WebAssembly.

## Features

- **DICOM Metadata Extraction**: Extract specific DICOM tags from files efficiently
- **DICOM Grouping**: Group DICOM files by metadata tags with localizer detection
- **DICOM De-identification**: Comprehensive de-identification using YAML profiles
- **Cross-platform**: Available as Rust library, Python package, and JavaScript/WASM module

## De-identification Profile Features

The library supports comprehensive DICOM de-identification through YAML configuration profiles. Here are the available features:

### Profile Structure

```yaml
version: 1
name: "Profile Name"
dicom:
  # Global options
  date-increment: 30                   # Days to shift all dates
  jitter-type: "float"                 # "float" or "int"
  jitter-range: 2.0                    # Range for jittering values
  patient-age-from-birthdate: true     # Calculate age from birth/study dates
  patient-age-units: "Y"               # "Y", "M", or "D" for years/months/days
  recurse-sequence: false              # Apply actions to nested sequences
  remove-private-tags: true            # Remove all private tags
  remove-undefined: false              # Remove tags not explicitly defined

  # Field-specific transformations
  fields:
    - name: "PatientName"              # Tag name, hex, or (group,element)
      replace-with: "REDACTED"         # Replace with static value
    - name: "PatientID"
      remove: true                     # Remove tag completely
    - name: "StudyInstanceUID"
      hashuid: true                   # Hash UID maintaining structure
    - name: "PatientBirthDate"
      increment-date: true             # Apply date-increment
    - name: "PatientWeight"
      jitter: true                     # Add random noise
      jitter-range: 5.0                # Override global jitter range
      jitter-min: 40.0                 # Minimum value after jittering
      jitter-max: 200.0                # Maximum value after jittering
    - regex: ".*Date.*"                # Use regex to match multiple tags
      increment-date: true
    - name: "(0031, \"AGFA PACS Archive Mirroring 1.0\", 01)"  # Private tags
      replace-with: "MODIFIED"
```

### Field Identification Methods

1. **Tag Names**: `"PatientName"`, `"StudyDate"`
2. **Hex Format**: `"00100010"`, `"0x00100010"`
3. **Tuple Format**: `"(0010, 0010)"`, `"(0008, 0020)"`
4. **Private Tags**: `"(group, \"creator\", element)"` format
5. **Repeater Tags**: `"(60xx, 0022)"`, `"50xx0010"` - Use `x` or `X` as wildcards
6. **Regex Patterns**: Match multiple tags with regular expressions

### Transformation Actions

#### replace-with
Replace tag value with a static string. Validates against DICOM VR constraints.
```yaml
- name: "PatientName"
  replace-with: "ANONYMOUS"
```

#### remove
Completely remove the tag from the DICOM file.
```yaml
- name: "PatientComments"
  remove: true
```

#### hash
Apply SHA-256 hash and truncate to 16 characters for anonymization.
```yaml
- name: "PatientID"
  hash: true
```

#### hashuid
Hash UIDs while preserving DICOM UID structure and length constraints.
```yaml
- name: "StudyInstanceUID"
  hashuid: true
```

#### increment-date
Shift dates by a specified number of days (uses global `date-increment`).
```yaml
- name: "StudyDate"
  increment-date: true
```

#### jitter
Add controlled random noise to numeric values.
```yaml
- name: "PatientWeight"
  jitter: true
  jitter-type: "float"      # or "int"
  jitter-range: 5.0         # ±5 units
  jitter-min: 40.0          # Minimum allowed value
  jitter-max: 200.0         # Maximum allowed value
```

### Global Options

- **date-increment**: Number of days to shift all dates
- **jitter-type**: Default jittering type (`"float"` or `"int"`)
- **jitter-range**: Default range for jittering operations
- **patient-age-from-birthdate**: Auto-calculate patient age from birth date and study date
- **patient-age-units**: Preferred units for patient age (`"Y"`, `"M"`, `"D"`)
- **recurse-sequence**: Apply field rules to nested DICOM sequences
- **remove-private-tags**: Remove all private tags (except those explicitly defined in fields)
- **remove-undefined**: Remove all tags except those explicitly defined in the profile

### Advanced Features

#### Sequence Recursion
Process nested DICOM sequences by setting `recurse-sequence: true`:
```yaml
dicom:
  recurse-sequence: true
  fields:
    - name: "StudyInstanceUID"
      hashuid: true  # Applied to all StudyInstanceUID tags in sequences too
```

#### Private Tag Support
Handle private DICOM tags with creator identification:
```yaml
fields:
  - name: "(2005, \"Philips MR Imaging DD 001\", 70)"
    replace-with: "REDACTED"
```

#### Regex Field Matching
Use regular expressions to match multiple related tags:
```yaml
fields:
  - regex: ".*Date.*"           # Match StudyDate, SeriesDate, etc.
    increment-date: true
  - regex: ".*InstanceUID.*"    # Match all UID tags
    hashuid: true
```

#### Repeater Tag Support
Handle DICOM repeater tags that use wildcards for group/element matching:
```yaml
fields:
  - name: "(60xx, 0022)"        # Matches (6000,0022), (6002,0022), (6004,0022), etc.
    replace-with: "REDACTED"
  - name: "50xx0010"
    remove: true
```

**Supported Patterns:**
- `(60xx, element)` - Wildcard in group for tuple format
- `50xx0010` - Wildcard in group for hex format
- `0x50xx0010` - Hex prefix with wildcards
- Wildcards only supported for groups 5xxx and 6xxx (overlay/curve repeating groups)

#### Patient Age Calculation
Automatically calculate and set patient age from birth date and study/series dates:
```yaml
dicom:
  patient-age-from-birthdate: true
  patient-age-units: "Y"        # Prefer years, fallback to months/days
  fields:
    - name: "PatientBirthDate"
      remove: true              # Remove after calculating age
```

## Development

```bash
# run all tests and build
just
# list all available commands
just --list
```
