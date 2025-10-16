# HEA to CSV Converter

A Python package and CLI to convert WFDB ECG recordings (.HEA/.DAT) to CSV format with timestamped entries using UNIX epoch nanoseconds.

## WFDB Format

The WFDB format consists of two files per recording:  

- **.hea**: Header file containing metadata about the recording (number of leads, sampling rate, start time, etc.)  
- **.dat**: Binary file containing the actual ECG signal samples.  

For complete details, refer to [WFDB Format Documentation](https://physionet.org/content/wfdb/).

## Features

- Converts all leads with precise timestamp for each sample (UNIX epoch in nanoseconds)  
- Handles multiple leads and variable durations  
- Progress bar for large datasets  
- Metadata printed and saved in JSON format (filename, leads, sampling rate, start time, etc.)  
- CLI support for direct command-line use  
- Output CSV includes `time` column as the first column (nanoseconds)

## Installation

Install from PyPI:

```bash
pip install hea_to_csv
```

## Usage

### As a Python Module

```python
from hea_to_csv import wfdb_to_csv

# Basic usage
wfdb_to_csv("recording.hea")  # Save as recording.csv

# With parameters
wfdb_to_csv(
    "recording.hea",
    output_file="example.csv",
    metadata_file="recording.json",
    verbose=True
)
```

### CLI Usage

```bash
python -m hea_to_csv <input_file> [-o <output_file>] [-m <metadata_file>] [-q]
```

## CLI Parameters

| Argument | Description |
|----------|-------------|
| `input_file` | Path to the input HEA file (required) |
| `--output, -o <file_path>` | Optional output CSV file path (default: same as input file but with `.csv`) |
| `--metadata, -m <file_path>` | Optional JSON metadata output path (default: same as input file but with `.json`) |
| `--quiet, -q` | Suppress console output (default: False) |

## Change Log

### v0.1.1
- Change csv column name to Lead_{i}.csv 


### v0.1.0
- Initial release  
- Converts HEA/DAT files to CSV with timestamp  
- Saves recording metadata in JSON format  

## License

MIT License

