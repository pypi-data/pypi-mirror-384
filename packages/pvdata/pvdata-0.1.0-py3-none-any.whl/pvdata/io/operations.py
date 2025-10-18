"""
Convenience functions for reading and writing data files

Provides simple, high-level functions for common operations.
"""

from pathlib import Path
from typing import Optional, Union, List, Any

import pandas as pd

from pvdata.io.reader import CSVReader, ParquetReader
from pvdata.io.writer import ParquetWriter
from pvdata.io.batch import BatchConverter
from pvdata.utils.logger import get_logger

logger = get_logger(__name__)


def read_csv(
    filepath: Union[str, Path], optimize_dtypes: bool = True, **kwargs: Any
) -> pd.DataFrame:
    """
    Read CSV file with automatic dtype optimization

    Convenience function that wraps CSVReader for simple usage.

    Args:
        filepath: Path to CSV file
        optimize_dtypes: Whether to optimize dtypes automatically (default: True)
        **kwargs: Additional arguments passed to pd.read_csv

    Returns:
        DataFrame with optimized dtypes

    Examples:
        >>> import pvdata as pv
        >>> df = pv.read_csv("data.csv")
        >>> print(df.dtypes)

        >>> # Disable optimization
        >>> df = pv.read_csv("data.csv", optimize_dtypes=False)

        >>> # With pandas arguments
        >>> df = pv.read_csv("data.csv", sep=";", encoding="utf-8")
    """
    reader = CSVReader(optimize_dtypes=optimize_dtypes)
    df = reader.read(filepath, **kwargs)

    # Log memory savings
    if optimize_dtypes and reader.memory_saved_pct > 0:
        logger.info(
            f"Memory optimization: {reader.memory_saved_pct:.1f}% reduction "
            f"({reader.memory_before / 1024**2:.2f} MB -> "
            f"{reader.memory_after / 1024**2:.2f} MB)"
        )

    return df


def read_parquet(
    filepath: Union[str, Path],
    columns: Optional[List[str]] = None,
    filters: Optional[List] = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Read Parquet file with optional column selection and filtering

    Convenience function that wraps ParquetReader for simple usage.

    Args:
        filepath: Path to Parquet file
        columns: List of columns to read (None = all columns)
        filters: PyArrow-style filters for row selection
        **kwargs: Additional arguments passed to pd.read_parquet

    Returns:
        DataFrame with selected data

    Examples:
        >>> import pvdata as pv
        >>> df = pv.read_parquet("data.parquet")

        >>> # Read specific columns
        >>> df = pv.read_parquet("data.parquet", columns=["timestamp", "power"])

        >>> # With filters
        >>> filters = [('power', '>', 1000)]
        >>> df = pv.read_parquet("data.parquet", filters=filters)
    """
    reader = ParquetReader()
    return reader.read(filepath, columns=columns, filters=filters, **kwargs)


def get_parquet_info(filepath: Union[str, Path]) -> dict:
    """
    Get metadata information from Parquet file

    Args:
        filepath: Path to Parquet file

    Returns:
        Dictionary with file metadata

    Examples:
        >>> import pvdata as pv
        >>> info = pv.get_parquet_info("data.parquet")
        >>> print(f"Rows: {info['num_rows']}")
        >>> print(f"Columns: {info['columns']}")
    """
    reader = ParquetReader()
    return reader.get_metadata(filepath)


def write_parquet(
    df: pd.DataFrame,
    filepath: Union[str, Path],
    compression: str = "zstd",
    compression_level: Optional[int] = 3,
    optimize_dtypes: bool = True,
    **kwargs: Any,
) -> None:
    """
    Write DataFrame to Parquet file with compression

    Convenience function that wraps ParquetWriter for simple usage.

    Args:
        df: DataFrame to write
        filepath: Output file path
        compression: Compression algorithm ("zstd", "snappy", "gzip", "brotli")
        compression_level: Compression level (algorithm-specific)
        optimize_dtypes: Optimize dtypes before writing
        **kwargs: Additional arguments passed to pyarrow.parquet.write_table

    Examples:
        >>> import pvdata as pv
        >>> pv.write_parquet(df, "output.parquet")

        >>> # With custom compression
        >>> pv.write_parquet(df, "output.parquet", compression="snappy")

        >>> # Maximum compression
        >>> pv.write_parquet(df, "output.parquet", compression="zstd", compression_level=9)
    """
    writer = ParquetWriter(
        compression=compression,
        compression_level=compression_level,
        optimize_dtypes=optimize_dtypes,
    )
    writer.write(df, filepath, **kwargs)

    # Log compression statistics
    if writer.compression_ratio > 0:
        logger.info(
            f"Compression: {writer.compression_ratio:.1f}x "
            f"({writer.original_size / 1024**2:.2f} MB -> "
            f"{writer.compressed_size / 1024**2:.2f} MB)"
        )


def batch_convert(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    pattern: str = "*.csv",
    compression: str = "zstd",
    compression_level: Optional[int] = 3,
    max_workers: int = 1,
    recursive: bool = False,
) -> List[Any]:
    """
    Batch convert CSV files to Parquet

    Convenience function for batch conversion with progress reporting.

    Args:
        input_dir: Input directory containing CSV files
        output_dir: Output directory for Parquet files
        pattern: File pattern to match (default: "*.csv")
        compression: Compression algorithm
        compression_level: Compression level
        max_workers: Number of parallel workers (1 = sequential)
        recursive: Search subdirectories recursively

    Returns:
        List of conversion results

    Examples:
        >>> import pvdata as pv
        >>> results = pv.batch_convert("data/csv/", "data/parquet/")
        >>> print(f"Converted {len(results)} files")

        >>> # Parallel processing
        >>> results = pv.batch_convert(
        ...     "data/csv/",
        ...     "data/parquet/",
        ...     max_workers=4
        ... )
    """
    converter = BatchConverter(
        compression=compression,
        compression_level=compression_level,
        max_workers=max_workers,
    )

    results = converter.convert_directory(
        input_dir, output_dir, pattern=pattern, recursive=recursive
    )

    # Print summary
    converter.print_summary()

    return results
