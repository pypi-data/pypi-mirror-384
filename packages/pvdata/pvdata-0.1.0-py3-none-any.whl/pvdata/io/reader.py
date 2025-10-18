"""
Reader module for CSV and Parquet files

Provides high-performance readers with automatic optimization:
- CSVReader: CSV reading with automatic dtype optimization
- ParquetReader: High-performance Parquet reading with filtering
"""

from pathlib import Path
from typing import Optional, Union, List, Dict, Any

import pandas as pd
import pyarrow.parquet as pq

from pvdata.config import DTypeMapper
from pvdata.utils.exceptions import FileNotFoundError, FileFormatError
from pvdata.utils.decorators import handle_errors, log_execution, measure_time
from pvdata.utils.logger import get_logger

logger = get_logger(__name__)


class CSVReader:
    """
    CSV file reader with automatic dtype optimization

    Features:
    - Automatic dtype optimization for memory efficiency
    - Configurable chunk reading for large files
    - Intelligent type inference
    - Error handling and logging

    Examples:
        >>> reader = CSVReader()
        >>> df = reader.read("data.csv")
        >>> print(f"Memory saved: {reader.memory_saved_pct:.1f}%")

        >>> # Read with optimization disabled
        >>> df = reader.read("data.csv", optimize_dtypes=False)

        >>> # Read in chunks
        >>> for chunk in reader.read_chunks("large.csv", chunksize=10000):
        ...     process(chunk)
    """

    def __init__(self, optimize_dtypes: bool = True):
        """
        Initialize CSVReader

        Args:
            optimize_dtypes: Whether to optimize dtypes automatically
        """
        self.optimize_dtypes = optimize_dtypes
        self.memory_before = 0
        self.memory_after = 0
        self.memory_saved_pct = 0.0

    @measure_time()
    @log_execution(level="DEBUG", include_args=False)
    @handle_errors(FileNotFoundError, reraise=True)
    def read(
        self, filepath: Union[str, Path], optimize_dtypes: Optional[bool] = None, **kwargs: Any
    ) -> pd.DataFrame:
        """
        Read CSV file into DataFrame

        Args:
            filepath: Path to CSV file
            optimize_dtypes: Override default dtype optimization
            **kwargs: Additional arguments passed to pd.read_csv

        Returns:
            DataFrame with optimized dtypes

        Raises:
            FileNotFoundError: If file doesn't exist
            FileFormatError: If file format is invalid
        """
        filepath = Path(filepath)

        # Check file exists
        if not filepath.exists():
            raise FileNotFoundError(str(filepath))

        # Check file extension
        if filepath.suffix.lower() not in [".csv", ".txt"]:
            logger.warning(
                f"File {filepath} has unexpected extension {filepath.suffix}. "
                "Expected .csv or .txt"
            )

        try:
            # Read CSV
            logger.info(f"Reading CSV file: {filepath}")
            df = pd.read_csv(filepath, **kwargs)

            # Track original memory
            self.memory_before = df.memory_usage(deep=True).sum()

            # Optimize dtypes if requested
            should_optimize = (
                optimize_dtypes if optimize_dtypes is not None else self.optimize_dtypes
            )
            if should_optimize:
                df = self._optimize_dataframe(df)
                self.memory_after = df.memory_usage(deep=True).sum()
                self.memory_saved_pct = (
                    (self.memory_before - self.memory_after) / self.memory_before * 100
                    if self.memory_before > 0
                    else 0.0
                )
                logger.info(
                    f"Memory optimized: {self.memory_before / 1024**2:.2f} MB -> "
                    f"{self.memory_after / 1024**2:.2f} MB "
                    f"({self.memory_saved_pct:.1f}% reduction)"
                )
            else:
                self.memory_after = self.memory_before
                self.memory_saved_pct = 0.0

            logger.info(f"Successfully read {len(df)} rows, {len(df.columns)} columns")
            return df

        except pd.errors.ParserError as e:
            raise FileFormatError(f"Failed to parse CSV file {filepath}: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading CSV file {filepath}: {str(e)}")
            raise

    def read_chunks(
        self,
        filepath: Union[str, Path],
        chunksize: int = 10000,
        optimize_dtypes: Optional[bool] = None,
        **kwargs: Any,
    ):
        """
        Read CSV file in chunks (generator)

        Args:
            filepath: Path to CSV file
            chunksize: Number of rows per chunk
            optimize_dtypes: Override default dtype optimization
            **kwargs: Additional arguments passed to pd.read_csv

        Yields:
            DataFrame chunks with optimized dtypes

        Examples:
            >>> reader = CSVReader()
            >>> for chunk in reader.read_chunks("large.csv", chunksize=5000):
            ...     process(chunk)
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(str(filepath))

        should_optimize = optimize_dtypes if optimize_dtypes is not None else self.optimize_dtypes

        logger.info(f"Reading CSV file in chunks: {filepath} (chunksize={chunksize})")

        try:
            for chunk_num, chunk in enumerate(pd.read_csv(filepath, chunksize=chunksize, **kwargs)):
                if should_optimize:
                    chunk = self._optimize_dataframe(chunk)

                logger.debug(f"Read chunk {chunk_num + 1}: {len(chunk)} rows")
                yield chunk

        except pd.errors.ParserError as e:
            raise FileFormatError(f"Failed to parse CSV file {filepath}: {str(e)}")

    def _optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame dtypes using DTypeMapper

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with optimized dtypes
        """
        return DTypeMapper.apply_mapping(df, auto_optimize=True)


class ParquetReader:
    """
    Parquet file reader with advanced filtering capabilities

    Features:
    - Column selection for reduced memory usage
    - Row filtering with PyArrow predicates
    - Metadata inspection
    - High-performance columnar reading

    Examples:
        >>> reader = ParquetReader()
        >>> df = reader.read("data.parquet")

        >>> # Read specific columns
        >>> df = reader.read("data.parquet", columns=["timestamp", "power"])

        >>> # Get file metadata
        >>> metadata = reader.get_metadata("data.parquet")
        >>> print(f"Rows: {metadata['num_rows']}")
    """

    def __init__(self):
        """Initialize ParquetReader"""
        self.file_metadata = None

    @measure_time()
    @log_execution(level="DEBUG", include_args=False)
    @handle_errors(FileNotFoundError, reraise=True)
    def read(
        self,
        filepath: Union[str, Path],
        columns: Optional[List[str]] = None,
        filters: Optional[List] = None,
        use_threads: bool = True,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Read Parquet file into DataFrame

        Args:
            filepath: Path to Parquet file
            columns: List of columns to read (None = all columns)
            filters: PyArrow-style filters for row selection
            use_threads: Whether to use multi-threading
            **kwargs: Additional arguments passed to pd.read_parquet

        Returns:
            DataFrame with selected data

        Raises:
            FileNotFoundError: If file doesn't exist
            FileFormatError: If file format is invalid

        Examples:
            >>> reader = ParquetReader()
            >>> df = reader.read("data.parquet", columns=["timestamp", "power"])

            >>> # With filters (requires PyArrow)
            >>> filters = [('power', '>', 1000)]
            >>> df = reader.read("data.parquet", filters=filters)
        """
        filepath = Path(filepath)

        # Check file exists
        if not filepath.exists():
            raise FileNotFoundError(str(filepath))

        # Check file extension
        if filepath.suffix.lower() != ".parquet":
            logger.warning(
                f"File {filepath} has unexpected extension {filepath.suffix}. " "Expected .parquet"
            )

        try:
            logger.info(f"Reading Parquet file: {filepath}")

            # Read parquet file
            df = pd.read_parquet(
                filepath, columns=columns, filters=filters, use_threads=use_threads, **kwargs
            )

            logger.info(
                f"Successfully read {len(df)} rows, {len(df.columns)} columns. "
                f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
            )

            return df

        except Exception as e:
            raise FileFormatError(f"Failed to read Parquet file {filepath}: {str(e)}")

    @handle_errors(FileNotFoundError, reraise=True)
    def get_metadata(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Get Parquet file metadata

        Args:
            filepath: Path to Parquet file

        Returns:
            Dictionary with metadata information

        Examples:
            >>> reader = ParquetReader()
            >>> metadata = reader.get_metadata("data.parquet")
            >>> print(f"Rows: {metadata['num_rows']}")
            >>> print(f"Columns: {metadata['columns']}")
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(str(filepath))

        try:
            # Read metadata using PyArrow
            parquet_file = pq.ParquetFile(filepath)
            metadata = parquet_file.metadata

            self.file_metadata = {
                "num_rows": metadata.num_rows,
                "num_row_groups": metadata.num_row_groups,
                "columns": [metadata.schema.column(i).name for i in range(metadata.num_columns)],
                "num_columns": metadata.num_columns,
                "serialized_size": metadata.serialized_size,
                "format_version": metadata.format_version,
            }

            logger.debug(f"Metadata for {filepath}: {self.file_metadata}")
            return self.file_metadata

        except Exception as e:
            raise FileFormatError(f"Failed to read Parquet metadata from {filepath}: {str(e)}")

    def read_row_group(
        self, filepath: Union[str, Path], row_group_index: int, columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Read a specific row group from Parquet file

        Args:
            filepath: Path to Parquet file
            row_group_index: Index of row group to read
            columns: List of columns to read

        Returns:
            DataFrame with row group data

        Examples:
            >>> reader = ParquetReader()
            >>> # Read first row group
            >>> df = reader.read_row_group("data.parquet", 0)
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(str(filepath))

        try:
            parquet_file = pq.ParquetFile(filepath)

            if row_group_index >= parquet_file.num_row_groups:
                raise FileFormatError(
                    f"Row group index {row_group_index} out of range. "
                    f"File has {parquet_file.num_row_groups} row groups."
                )

            logger.info(f"Reading row group {row_group_index} from {filepath}")

            table = parquet_file.read_row_group(row_group_index, columns=columns)
            df = table.to_pandas()

            logger.debug(f"Read {len(df)} rows from row group {row_group_index}")
            return df

        except FileFormatError:
            raise
        except Exception as e:
            raise FileFormatError(
                f"Failed to read row group {row_group_index} from {filepath}: {str(e)}"
            )
