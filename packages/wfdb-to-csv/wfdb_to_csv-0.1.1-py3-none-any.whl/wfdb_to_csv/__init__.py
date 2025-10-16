"""
hea_to_csv module

Provides functionality to convert WFDB ECG recordings (.HEA/.DAT)
to timestamped CSV format using time (UNIX epoch ns) and lead data.

"""

from .core import read_wfdb, wfdb_to_csv

__all__ = ["read_wfdb", "wfdb_to_csv"]
__version__ = "0.1.0"
