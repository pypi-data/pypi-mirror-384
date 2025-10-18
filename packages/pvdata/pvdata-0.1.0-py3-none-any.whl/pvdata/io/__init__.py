"""
pvdata.io - Input/Output operations for photovoltaic data

This module provides high-performance reading and writing operations
for CSV and Parquet files, with automatic optimization.
"""

# Reader classes (TASK_04)
from pvdata.io.reader import CSVReader, ParquetReader

# Writer classes (TASK_05)
from pvdata.io.writer import ParquetWriter

# Batch processing (TASK_05 & TASK_06)
from pvdata.io.batch import BatchConverter, BatchProcessor, ConversionResult

# Convenience functions
from pvdata.io.operations import (
    read_csv,
    read_parquet,
    get_parquet_info,
    write_parquet,
    batch_convert,
)

__all__ = [
    # Reader classes
    "CSVReader",
    "ParquetReader",
    # Writer classes
    "ParquetWriter",
    # Batch processing
    "BatchConverter",
    "BatchProcessor",
    "ConversionResult",
    # Convenience functions
    "read_csv",
    "read_parquet",
    "get_parquet_info",
    "write_parquet",
    "batch_convert",
]
