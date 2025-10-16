import argparse
import sys
import os
from .core import wfdb_to_csv


def main():
    parser = argparse.ArgumentParser(
        description="Convert WFDB (HEA/DAT) file to CSV with timestamp in UNIX epoch nanoseconds."
    )
    parser.add_argument("input", help="Input HEA file path (.hea)")
    parser.add_argument("-o", "--output", help="Output CSV file path (optional)")
    parser.add_argument("-m", "--metadata", help="Saves JSON Metadata to file (optional)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress console output")

    args = parser.parse_args()
    verbose = not args.quiet

    try:
        wfdb_to_csv(
            input_file=args.input,
            output_file=args.output,
            metadata_file=args.metadata,
            verbose=verbose,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


main()