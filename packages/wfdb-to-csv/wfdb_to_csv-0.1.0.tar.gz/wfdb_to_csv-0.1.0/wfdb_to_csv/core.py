import wfdb
import pandas as pd
import datetime
import os
import json
from tqdm import tqdm


def read_wfdb(input_file, duration=None, metadata_file=None, verbose=True):
    """
    Read WFDB (.hea/.dat) file and return a Pandas DataFrame.

    Args:
        input_file (str): Path to the .hea file
        duration (int): Seconds to read (optional)
        metadata_file (str): Optional metadata JSON output path
        verbose (bool): Print details to console

    Returns:
        pd.DataFrame: Data with 'time' (UNIX ns) + lead columns
    """
    record_name = os.path.splitext(input_file)[0]
    header = wfdb.rdheader(record_name)
    fs = header.fs
    sig_names = [ sig_name.split()[0] for sig_name in header.sig_name ]
    num_samples = header.sig_len
    num_leads = header.n_sig

    # Duration limit
    if duration:
        num_samples = min(num_samples, int(fs * duration))

    record = wfdb.rdrecord(record_name, sampto=num_samples)
    signals = record.p_signal

    # Determine start time
    start_date = getattr(header, "base_date", None)
    start_time = getattr(header, "base_time", None)
    if start_date and start_time:
        start_datetime = datetime.datetime.combine(start_date, start_time)
    else:
        start_datetime = datetime.datetime.now()

    base_epoch_ns = int(start_datetime.timestamp() * 1e9)
    interval_ns = int(1e9 / fs)

    if verbose:
        print("\nHEA File Info:")
        print(f"  File         : {os.path.basename(input_file)}")
        print(f"  Leads        : {num_leads}")
        print(f"  Samples      : {num_samples}")
        print(f"  Sampling Hz  : {fs}")
        print(f"  Start Time   : {start_datetime}")
        print()

    # Create dataframe
    timestamps = [base_epoch_ns + i * interval_ns for i in range(len(signals))]
    df = pd.DataFrame(signals, columns=sig_names)
    df.insert(0, "time", timestamps)

    # Metadata
    details = {
        "Filename": os.path.basename(input_file),
        "Leads": num_leads,
        "Samples": len(signals),
        "Sampling Hz": fs,
        "Signal Names": sig_names,
        "Start Datetime": str(start_datetime),
    }

    if metadata_file:
        with open(metadata_file, "w") as f:
            json.dump(details, f, indent=4)
        if verbose:
            print(f"JSON metadata written to: {metadata_file}")

    return df


def wfdb_to_csv(input_file, output_file=None, metadata_file=None, duration=None, verbose=True):
    """
    Convert HEA/DAT files to CSV with UNIX epoch ns timestamps.
    """
    base, _ = os.path.splitext(input_file)
    if not output_file:
        output_file = base + ".csv"
    if not metadata_file:
        metadata_file = base + ".json"

    df = read_wfdb(
        input_file=input_file,
        duration=duration,
        metadata_file=metadata_file,
        verbose=verbose,
    )

    if verbose:
        print(f"Writing to CSV: {output_file}")
    df.to_csv(output_file, index=False)
    if verbose:
        print(f"CSV file written to: {output_file}")
