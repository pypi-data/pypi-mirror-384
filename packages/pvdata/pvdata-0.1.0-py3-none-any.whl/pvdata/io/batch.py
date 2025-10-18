"""
Batch processing module for converting and processing multiple files

Provides utilities for batch CSV to Parquet conversion and multi-file processing:
- BatchConverter: Convert multiple CSV files to Parquet
- BatchProcessor: Process multiple files with custom operations
"""

from pathlib import Path
from typing import Optional, Union, List, Callable, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import time

from pvdata.io.reader import CSVReader
from pvdata.io.writer import ParquetWriter
from pvdata.utils.exceptions import FileError
from pvdata.utils.decorators import log_execution, measure_time
from pvdata.utils.logger import get_logger

logger = get_logger(__name__)


class ConversionResult:
    """Result of a single file conversion"""

    def __init__(
        self,
        input_file: Path,
        output_file: Path,
        success: bool,
        rows: int = 0,
        original_size: int = 0,
        compressed_size: int = 0,
        duration: float = 0.0,
        error: Optional[str] = None,
    ):
        self.input_file = input_file
        self.output_file = output_file
        self.success = success
        self.rows = rows
        self.original_size = original_size
        self.compressed_size = compressed_size
        self.duration = duration
        self.error = error

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio"""
        if self.original_size > 0 and self.compressed_size > 0:
            return self.original_size / self.compressed_size
        return 0.0

    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        return (
            f"ConversionResult({status} {self.input_file.name} -> "
            f"{self.output_file.name}, {self.rows} rows, "
            f"{self.compression_ratio:.1f}x compression)"
        )


class BatchConverter:
    """
    Batch converter for CSV to Parquet conversion

    Features:
    - Convert multiple CSV files to Parquet in batch
    - Parallel processing with multiple workers
    - Progress tracking and reporting
    - Automatic file discovery with glob patterns
    - Configurable compression and optimization

    Examples:
        >>> converter = BatchConverter()
        >>> results = converter.convert_directory("data/csv/", "data/parquet/")
        >>> print(f"Converted {len(results)} files")

        >>> # With custom configuration
        >>> converter = BatchConverter(
        ...     compression="zstd",
        ...     compression_level=5,
        ...     max_workers=4
        ... )
        >>> results = converter.convert_files(csv_files, output_dir)
    """

    def __init__(
        self,
        compression: str = "zstd",
        compression_level: Optional[int] = 3,
        optimize_dtypes: bool = True,
        max_workers: int = 1,
        use_processes: bool = False,
    ):
        """
        Initialize BatchConverter

        Args:
            compression: Compression algorithm
            compression_level: Compression level
            optimize_dtypes: Optimize dtypes before writing
            max_workers: Number of parallel workers (1 = sequential)
            use_processes: Use processes instead of threads for parallel execution
        """
        self.compression = compression
        self.compression_level = compression_level
        self.optimize_dtypes = optimize_dtypes
        self.max_workers = max_workers
        self.use_processes = use_processes

        self.results: List[ConversionResult] = []

    @measure_time()
    @log_execution(level="INFO", include_args=False)
    def convert_directory(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        pattern: str = "*.csv",
        recursive: bool = False,
    ) -> List[ConversionResult]:
        """
        Convert all CSV files in a directory to Parquet

        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            pattern: File pattern to match (default: "*.csv")
            recursive: Search subdirectories recursively

        Returns:
            List of conversion results

        Examples:
            >>> converter = BatchConverter()
            >>> results = converter.convert_directory("data/csv/", "data/parquet/")
            >>> success_count = sum(1 for r in results if r.success)
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)

        if not input_dir.exists():
            raise FileError(f"Input directory does not exist: {input_dir}")

        # Find all CSV files
        if recursive:
            csv_files = list(input_dir.rglob(pattern))
        else:
            csv_files = list(input_dir.glob(pattern))

        if not csv_files:
            logger.warning(f"No files matching '{pattern}' found in {input_dir}")
            return []

        logger.info(f"Found {len(csv_files)} CSV files to convert")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert files
        return self.convert_files(csv_files, output_dir)

    def convert_files(
        self,
        csv_files: List[Union[str, Path]],
        output_dir: Union[str, Path],
        preserve_structure: bool = False,
    ) -> List[ConversionResult]:
        """
        Convert multiple CSV files to Parquet

        Args:
            csv_files: List of CSV file paths
            output_dir: Output directory path
            preserve_structure: Preserve directory structure from input files

        Returns:
            List of conversion results

        Examples:
            >>> files = ["data1.csv", "data2.csv", "data3.csv"]
            >>> converter = BatchConverter(max_workers=2)
            >>> results = converter.convert_files(files, "output/")
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_files = [Path(f) for f in csv_files]

        if self.max_workers > 1:
            logger.info(f"Converting {len(csv_files)} files with {self.max_workers} workers")
            return self._convert_parallel(csv_files, output_dir, preserve_structure)
        else:
            logger.info(f"Converting {len(csv_files)} files sequentially")
            return self._convert_sequential(csv_files, output_dir, preserve_structure)

    def _convert_sequential(
        self,
        csv_files: List[Path],
        output_dir: Path,
        preserve_structure: bool,
    ) -> List[ConversionResult]:
        """Convert files sequentially"""
        self.results = []

        for i, csv_file in enumerate(csv_files, 1):
            logger.info(f"Converting {i}/{len(csv_files)}: {csv_file.name}")
            result = self._convert_single_file(csv_file, output_dir, preserve_structure)
            self.results.append(result)

            if result.success:
                logger.info(
                    f"  ✓ {result.rows} rows, {result.compression_ratio:.1f}x compression, "
                    f"{result.duration:.2f}s"
                )
            else:
                logger.error(f"  ✗ Failed: {result.error}")

        return self.results

    def _convert_parallel(
        self,
        csv_files: List[Path],
        output_dir: Path,
        preserve_structure: bool,
    ) -> List[ConversionResult]:
        """Convert files in parallel"""
        self.results = []

        # Choose executor type
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    self._convert_single_file, csv_file, output_dir, preserve_structure
                ): csv_file
                for csv_file in csv_files
            }

            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_file):
                csv_file = future_to_file[future]
                completed += 1

                try:
                    result = future.result()
                    self.results.append(result)

                    if result.success:
                        logger.info(
                            f"[{completed}/{len(csv_files)}] ✓ {csv_file.name}: "
                            f"{result.rows} rows, {result.compression_ratio:.1f}x, "
                            f"{result.duration:.2f}s"
                        )
                    else:
                        logger.error(
                            f"[{completed}/{len(csv_files)}] ✗ {csv_file.name}: " f"{result.error}"
                        )

                except Exception as e:
                    logger.error(f"[{completed}/{len(csv_files)}] ✗ {csv_file.name}: {e}")
                    self.results.append(
                        ConversionResult(
                            csv_file,
                            output_dir / f"{csv_file.stem}.parquet",
                            success=False,
                            error=str(e),
                        )
                    )

        return self.results

    def _convert_single_file(
        self,
        csv_file: Path,
        output_dir: Path,
        preserve_structure: bool,
    ) -> ConversionResult:
        """Convert a single CSV file to Parquet"""
        start_time = time.time()

        try:
            # Determine output path
            if preserve_structure:
                # This would require tracking the original base path
                output_file = output_dir / f"{csv_file.stem}.parquet"
            else:
                output_file = output_dir / f"{csv_file.stem}.parquet"

            # Read CSV
            reader = CSVReader(optimize_dtypes=self.optimize_dtypes)
            df = reader.read(csv_file)

            rows = len(df)
            original_size = csv_file.stat().st_size

            # Write Parquet
            writer = ParquetWriter(
                compression=self.compression,
                compression_level=self.compression_level,
                optimize_dtypes=False,  # Already optimized by reader
            )
            writer.write(df, output_file)

            compressed_size = output_file.stat().st_size
            duration = time.time() - start_time

            return ConversionResult(
                csv_file,
                output_file,
                success=True,
                rows=rows,
                original_size=original_size,
                compressed_size=compressed_size,
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return ConversionResult(
                csv_file,
                output_dir / f"{csv_file.stem}.parquet",
                success=False,
                duration=duration,
                error=str(e),
            )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of conversion results

        Returns:
            Dictionary with summary statistics

        Examples:
            >>> converter = BatchConverter()
            >>> results = converter.convert_directory("data/", "output/")
            >>> summary = converter.get_summary()
            >>> print(f"Success rate: {summary['success_rate']:.1f}%")
        """
        if not self.results:
            return {}

        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        total_original_size = sum(r.original_size for r in successful)
        total_compressed_size = sum(r.compressed_size for r in successful)
        total_rows = sum(r.rows for r in successful)
        total_duration = sum(r.duration for r in self.results)

        avg_compression = (
            total_original_size / total_compressed_size if total_compressed_size > 0 else 0
        )

        return {
            "total_files": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) * 100,
            "total_rows": total_rows,
            "total_original_size": total_original_size,
            "total_compressed_size": total_compressed_size,
            "avg_compression_ratio": avg_compression,
            "space_saved_pct": (1 - 1 / avg_compression) * 100 if avg_compression > 0 else 0,
            "total_duration": total_duration,
            "original_size_mb": total_original_size / 1024**2,
            "compressed_size_mb": total_compressed_size / 1024**2,
        }

    def print_summary(self) -> None:
        """Print a formatted summary of conversion results"""
        summary = self.get_summary()

        if not summary:
            print("No conversion results available")
            return

        print("\n" + "=" * 60)
        print("Batch Conversion Summary")
        print("=" * 60)
        print(f"Total files:         {summary['total_files']}")
        print(f"Successful:          {summary['successful']} ✓")
        print(f"Failed:              {summary['failed']} ✗")
        print(f"Success rate:        {summary['success_rate']:.1f}%")
        print()
        print(f"Total rows:          {summary['total_rows']:,}")
        print(f"Original size:       {summary['original_size_mb']:.2f} MB")
        print(f"Compressed size:     {summary['compressed_size_mb']:.2f} MB")
        print(f"Compression ratio:   {summary['avg_compression_ratio']:.1f}x")
        print(f"Space saved:         {summary['space_saved_pct']:.1f}%")
        print(f"Total duration:      {summary['total_duration']:.2f}s")
        print("=" * 60)


class BatchProcessor:
    """
    Generic batch processor for multiple files

    Features:
    - Process multiple files with custom functions
    - Parallel processing with threads or processes
    - Error handling and reporting
    - Progress tracking

    Examples:
        >>> def process_func(filepath):
        ...     df = pd.read_parquet(filepath)
        ...     # Do processing
        ...     return result
        >>>
        >>> processor = BatchProcessor(process_func, max_workers=4)
        >>> results = processor.process_directory("data/parquet/")
    """

    def __init__(
        self,
        process_func: Callable[[Path], Any],
        max_workers: int = 1,
        use_processes: bool = False,
    ):
        """
        Initialize BatchProcessor

        Args:
            process_func: Function to process each file (takes Path, returns Any)
            max_workers: Number of parallel workers
            use_processes: Use processes instead of threads
        """
        self.process_func = process_func
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.results: List[Tuple[Path, Any, Optional[str]]] = []

    @measure_time()
    @log_execution(level="INFO", include_args=False)
    def process_directory(
        self,
        input_dir: Union[str, Path],
        pattern: str = "*.parquet",
        recursive: bool = False,
    ) -> List[Tuple[Path, Any, Optional[str]]]:
        """
        Process all files matching pattern in directory

        Args:
            input_dir: Input directory path
            pattern: File pattern to match
            recursive: Search subdirectories recursively

        Returns:
            List of tuples (filepath, result, error)

        Examples:
            >>> processor = BatchProcessor(my_func, max_workers=2)
            >>> results = processor.process_directory("data/", "*.parquet")
        """
        input_dir = Path(input_dir)

        if not input_dir.exists():
            raise FileError(f"Input directory does not exist: {input_dir}")

        # Find files
        if recursive:
            files = list(input_dir.rglob(pattern))
        else:
            files = list(input_dir.glob(pattern))

        if not files:
            logger.warning(f"No files matching '{pattern}' found in {input_dir}")
            return []

        logger.info(f"Found {len(files)} files to process")

        return self.process_files(files)

    def process_files(self, files: List[Union[str, Path]]) -> List[Tuple[Path, Any, Optional[str]]]:
        """
        Process multiple files

        Args:
            files: List of file paths

        Returns:
            List of tuples (filepath, result, error)
        """
        files = [Path(f) for f in files]

        if self.max_workers > 1:
            logger.info(f"Processing {len(files)} files with {self.max_workers} workers")
            return self._process_parallel(files)
        else:
            logger.info(f"Processing {len(files)} files sequentially")
            return self._process_sequential(files)

    def _process_sequential(self, files: List[Path]) -> List[Tuple[Path, Any, Optional[str]]]:
        """Process files sequentially"""
        self.results = []

        for i, filepath in enumerate(files, 1):
            logger.info(f"Processing {i}/{len(files)}: {filepath.name}")

            try:
                result = self.process_func(filepath)
                self.results.append((filepath, result, None))
                logger.info("  ✓ Success")
            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                self.results.append((filepath, None, str(e)))

        return self.results

    def _process_parallel(self, files: List[Path]) -> List[Tuple[Path, Any, Optional[str]]]:
        """Process files in parallel"""
        self.results = []

        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_func, filepath): filepath for filepath in files
            }

            completed = 0
            for future in as_completed(future_to_file):
                filepath = future_to_file[future]
                completed += 1

                try:
                    result = future.result()
                    self.results.append((filepath, result, None))
                    logger.info(f"[{completed}/{len(files)}] ✓ {filepath.name}")
                except Exception as e:
                    logger.error(f"[{completed}/{len(files)}] ✗ {filepath.name}: {e}")
                    self.results.append((filepath, None, str(e)))

        return self.results
