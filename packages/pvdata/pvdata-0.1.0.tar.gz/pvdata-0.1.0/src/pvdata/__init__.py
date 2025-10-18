"""
pvdata - High-performance toolkit for photovoltaic data processing

This package provides tools for efficient storage, processing, and analysis
of photovoltaic (solar) time-series data.

Core features:
- 2-8x compression ratio (CSV to Parquet)
- 5.5x read speedup
- 50-75% memory reduction through dtype optimization
- Batch processing with parallel support
- Time series resampling and aggregation
- Data quality analysis and gap detection

Quick Start:
    >>> import pvdata as pv
    >>> df = pv.read_csv('data.csv')  # Automatic optimization
    >>> pv.write_parquet(df, 'data.parquet')  # Compressed storage
    >>> results = pv.batch_convert('csv/', 'parquet/')  # Batch conversion

For detailed usage, see the User Guide at docs/USER_GUIDE.md
"""

from pvdata.__version__ import __version__

# Core IO functions
from pvdata.io import (
    read_csv,
    read_parquet,
    write_parquet,
    batch_convert,
    get_parquet_info,
)

# Import submodules for direct access
from pvdata import io
from pvdata import processing
from pvdata import config
from pvdata import utils

__all__ = [
    "__version__",
    # Convenience functions
    "read_csv",
    "read_parquet",
    "write_parquet",
    "batch_convert",
    "get_parquet_info",
    # Submodules
    "io",
    "processing",
    "config",
    "utils",
]
