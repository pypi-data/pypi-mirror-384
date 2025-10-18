"""
Writer module for Parquet files

Provides high-performance writers with compression and optimization:
- ParquetWriter: Advanced Parquet writing with compression and optimization
- write_parquet: Convenience function for quick writes
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pvdata.config import ParquetConfig, DTypeMapper
from pvdata.utils.exceptions import FileError, ValidationError
from pvdata.utils.decorators import handle_errors, log_execution, measure_time
from pvdata.utils.logger import get_logger

logger = get_logger(__name__)


class ParquetWriter:
    """
    Advanced Parquet file writer with compression and optimization

    Features:
    - Multiple compression algorithms (zstd, snappy, gzip, brotli)
    - Automatic dtype optimization
    - Row group size control
    - Statistics and dictionary encoding
    - Incremental writing for large datasets
    - Compression level tuning

    Examples:
        >>> writer = ParquetWriter()
        >>> writer.write(df, "output.parquet")
        >>> print(f"Compression ratio: {writer.compression_ratio:.1f}x")

        >>> # Use preset configuration
        >>> writer = ParquetWriter(preset="optimized")
        >>> writer.write(df, "output.parquet")

        >>> # Custom configuration
        >>> writer = ParquetWriter(
        ...     compression="zstd",
        ...     compression_level=5,
        ...     optimize_dtypes=True
        ... )
        >>> writer.write(df, "output.parquet")
    """

    def __init__(
        self,
        preset: Optional[str] = None,
        compression: Optional[str] = None,
        compression_level: Optional[int] = None,
        row_group_size: Optional[int] = None,
        use_dictionary: Optional[bool] = None,
        write_statistics: Optional[bool] = None,
        optimize_dtypes: bool = True,
    ):
        """
        Initialize ParquetWriter

        Args:
            preset: Configuration preset name
                ("standard", "optimized", "fast", "maximum_compression")
            compression: Compression algorithm
                ("zstd", "snappy", "gzip", "brotli", "none")
            compression_level: Compression level (algorithm-specific)
            row_group_size: Number of rows per row group
            use_dictionary: Enable dictionary encoding
            write_statistics: Write column statistics
            optimize_dtypes: Optimize dtypes before writing
        """
        self.optimize_dtypes = optimize_dtypes

        # Load preset or use defaults
        if preset:
            config = ParquetConfig.get_preset(preset)
            self.compression = compression or config.compression
            self.compression_level = (
                compression_level if compression_level is not None else config.compression_level
            )
            self.row_group_size = row_group_size or config.row_group_size
            self.use_dictionary = (
                use_dictionary if use_dictionary is not None else config.use_dictionary
            )
            self.write_statistics = (
                write_statistics if write_statistics is not None else config.write_statistics
            )
        else:
            # Use optimized defaults
            optimized = ParquetConfig.OPTIMIZED
            self.compression = compression or optimized.compression
            self.compression_level = (
                compression_level if compression_level is not None else optimized.compression_level
            )
            self.row_group_size = row_group_size or optimized.row_group_size
            self.use_dictionary = (
                use_dictionary if use_dictionary is not None else optimized.use_dictionary
            )
            self.write_statistics = (
                write_statistics if write_statistics is not None else optimized.write_statistics
            )

        # Statistics
        self.original_size = 0
        self.compressed_size = 0
        self.compression_ratio = 0.0

    @measure_time()
    @log_execution(level="DEBUG", include_args=False)
    @handle_errors(ValidationError, reraise=True)
    def write(
        self,
        df: pd.DataFrame,
        filepath: Union[str, Path],
        optimize_dtypes: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        """
        Write DataFrame to Parquet file

        Args:
            df: DataFrame to write
            filepath: Output file path
            optimize_dtypes: Override default dtype optimization
            **kwargs: Additional arguments for pyarrow.parquet.write_table

        Raises:
            ValidationError: If DataFrame is invalid
            FileError: If write operation fails

        Examples:
            >>> writer = ParquetWriter()
            >>> writer.write(df, "output.parquet")

            >>> # With custom settings
            >>> writer.write(df, "output.parquet", optimize_dtypes=False)
        """
        filepath = Path(filepath)

        # Validate input
        if df.empty:
            raise ValidationError("Cannot write empty DataFrame")

        if len(df.columns) == 0:
            raise ValidationError("DataFrame has no columns")

        # Optimize dtypes if requested
        should_optimize = optimize_dtypes if optimize_dtypes is not None else self.optimize_dtypes
        if should_optimize:
            logger.info("Optimizing dtypes before writing")
            df = DTypeMapper.apply_mapping(df, auto_optimize=True)

        # Calculate original size
        self.original_size = df.memory_usage(deep=True).sum()

        try:
            # Convert to PyArrow table
            table = pa.Table.from_pandas(df)

            # Prepare write options
            write_options = {
                "compression": self.compression,
                "use_dictionary": self.use_dictionary,
                "write_statistics": self.write_statistics,
                "row_group_size": self.row_group_size,
            }

            # Add compression level if supported
            if self.compression in ["zstd", "gzip", "brotli"] and self.compression_level:
                write_options["compression_level"] = self.compression_level

            # Merge with user kwargs
            write_options.update(kwargs)

            logger.info(
                f"Writing Parquet file: {filepath} "
                f"(compression={self.compression}, level={self.compression_level})"
            )

            # Write to file
            pq.write_table(table, filepath, **write_options)

            # Calculate compression ratio
            self.compressed_size = filepath.stat().st_size
            self.compression_ratio = (
                self.original_size / self.compressed_size if self.compressed_size > 0 else 0.0
            )

            logger.info(
                f"Successfully wrote {len(df)} rows, {len(df.columns)} columns. "
                f"File size: {self.compressed_size / 1024**2:.2f} MB, "
                f"Compression ratio: {self.compression_ratio:.2f}x"
            )

        except Exception as e:
            raise FileError(f"Failed to write Parquet file {filepath}: {str(e)}")

    @handle_errors(ValidationError, reraise=True)
    def write_batches(
        self,
        df: pd.DataFrame,
        filepath: Union[str, Path],
        batch_size: int = 100000,
        **kwargs: Any,
    ) -> None:
        """
        Write DataFrame in batches (for very large datasets)

        Args:
            df: DataFrame to write
            filepath: Output file path
            batch_size: Number of rows per batch
            **kwargs: Additional arguments for parquet writer

        Examples:
            >>> writer = ParquetWriter()
            >>> writer.write_batches(large_df, "output.parquet", batch_size=50000)
        """
        filepath = Path(filepath)

        if df.empty:
            raise ValidationError("Cannot write empty DataFrame")

        # Optimize dtypes if requested
        if self.optimize_dtypes:
            logger.info("Optimizing dtypes before writing")
            df = DTypeMapper.apply_mapping(df, auto_optimize=True)

        self.original_size = df.memory_usage(deep=True).sum()

        try:
            # Convert to PyArrow table
            table = pa.Table.from_pandas(df)

            # Prepare write options
            write_options = {
                "compression": self.compression,
                "use_dictionary": self.use_dictionary,
                "write_statistics": self.write_statistics,
            }

            if self.compression in ["zstd", "gzip", "brotli"] and self.compression_level:
                write_options["compression_level"] = self.compression_level

            write_options.update(kwargs)

            logger.info(
                f"Writing Parquet file in batches: {filepath} " f"(batch_size={batch_size})"
            )

            # Write using ParquetWriter for batch control
            schema = table.schema
            with pq.ParquetWriter(filepath, schema, **write_options) as parquet_writer:
                # Write in batches
                for i in range(0, len(table), batch_size):
                    batch = table.slice(i, min(batch_size, len(table) - i))
                    parquet_writer.write_table(batch)

                    if (i + batch_size) % (batch_size * 10) == 0:
                        logger.debug(f"Written {i + batch_size} rows...")

            # Calculate compression ratio
            self.compressed_size = filepath.stat().st_size
            self.compression_ratio = (
                self.original_size / self.compressed_size if self.compressed_size > 0 else 0.0
            )

            logger.info(
                f"Successfully wrote {len(df)} rows in batches. "
                f"File size: {self.compressed_size / 1024**2:.2f} MB, "
                f"Compression ratio: {self.compression_ratio:.2f}x"
            )

        except Exception as e:
            raise FileError(f"Failed to write Parquet file {filepath}: {str(e)}")

    def append(
        self,
        df: pd.DataFrame,
        filepath: Union[str, Path],
        **kwargs: Any,
    ) -> None:
        """
        Append DataFrame to existing Parquet file

        Note: This reads the entire file, appends data, and writes back.
        For true streaming appends, use write_batches with ParquetWriter.

        Args:
            df: DataFrame to append
            filepath: Existing Parquet file path
            **kwargs: Additional arguments

        Examples:
            >>> writer = ParquetWriter()
            >>> writer.append(new_data, "existing.parquet")
        """
        filepath = Path(filepath)

        if not filepath.exists():
            logger.warning(f"File {filepath} does not exist, creating new file")
            self.write(df, filepath, **kwargs)
            return

        try:
            # Read existing data
            logger.info(f"Reading existing file: {filepath}")
            existing_df = pd.read_parquet(filepath)

            # Concatenate
            combined_df = pd.concat([existing_df, df], ignore_index=True)

            logger.info(f"Appending {len(df)} rows to existing {len(existing_df)} rows")

            # Write combined data
            self.write(combined_df, filepath, **kwargs)

        except Exception as e:
            raise FileError(f"Failed to append to Parquet file {filepath}: {str(e)}")

    def get_compression_stats(self) -> Dict[str, Any]:
        """
        Get compression statistics from last write operation

        Returns:
            Dictionary with compression statistics

        Examples:
            >>> writer = ParquetWriter()
            >>> writer.write(df, "output.parquet")
            >>> stats = writer.get_compression_stats()
            >>> print(f"Saved {stats['space_saved_pct']:.1f}%")
        """
        space_saved_pct = (
            (1 - 1 / self.compression_ratio) * 100 if self.compression_ratio > 0 else 0
        )

        return {
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "compression_ratio": self.compression_ratio,
            "space_saved_pct": space_saved_pct,
            "original_size_mb": self.original_size / 1024**2,
            "compressed_size_mb": self.compressed_size / 1024**2,
        }
