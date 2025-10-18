"""
Tests for Writer and Batch modules
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from pvdata.io.writer import ParquetWriter
from pvdata.io.batch import BatchConverter, BatchProcessor, ConversionResult
from pvdata.io.operations import write_parquet, batch_convert
from pvdata.utils.exceptions import ValidationError, FileError


class TestParquetWriter:
    """Tests for ParquetWriter class"""

    def test_writer_initialization_default(self):
        """Test ParquetWriter initialization with defaults"""
        writer = ParquetWriter()
        assert writer.compression == "zstd"
        assert writer.compression_level == 3
        assert writer.optimize_dtypes is True

    def test_writer_initialization_preset(self):
        """Test ParquetWriter with preset"""
        writer = ParquetWriter(preset="fast")
        assert writer.compression == "snappy"

    def test_writer_initialization_custom(self):
        """Test ParquetWriter with custom settings"""
        writer = ParquetWriter(compression="gzip", compression_level=9, optimize_dtypes=False)
        assert writer.compression == "gzip"
        assert writer.compression_level == 9
        assert writer.optimize_dtypes is False

    def test_write_basic(self, tmp_path):
        """Test basic Parquet writing"""
        parquet_file = tmp_path / "test.parquet"
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0], "c": ["x", "y", "z"]})

        writer = ParquetWriter()
        writer.write(df, parquet_file)

        # Verify file exists
        assert parquet_file.exists()

        # Read back and verify
        df_read = pd.read_parquet(parquet_file)
        assert len(df_read) == 3
        assert list(df_read.columns) == ["a", "b", "c"]

    def test_write_with_compression(self, tmp_path):
        """Test writing with different compression algorithms"""
        df = pd.DataFrame({"a": range(1000), "b": np.random.randn(1000)})

        compressions = ["zstd", "snappy", "gzip"]
        for compression in compressions:
            parquet_file = tmp_path / f"test_{compression}.parquet"

            writer = ParquetWriter(compression=compression)
            writer.write(df, parquet_file)

            assert parquet_file.exists()
            assert writer.compression_ratio > 0

    def test_write_empty_dataframe(self, tmp_path):
        """Test writing empty DataFrame"""
        parquet_file = tmp_path / "empty.parquet"
        df = pd.DataFrame()

        writer = ParquetWriter()
        with pytest.raises(ValidationError, match="empty DataFrame"):
            writer.write(df, parquet_file)

    def test_write_no_columns(self, tmp_path):
        """Test writing DataFrame with no columns"""
        parquet_file = tmp_path / "no_cols.parquet"
        df = pd.DataFrame(index=[0, 1, 2])

        writer = ParquetWriter()
        with pytest.raises(ValidationError, match="empty DataFrame|no columns"):
            writer.write(df, parquet_file)

    def test_write_with_optimization(self, tmp_path):
        """Test writing with dtype optimization"""
        parquet_file = tmp_path / "optimized.parquet"
        df = pd.DataFrame(
            {
                "small_int": np.array([1, 2, 3, 4, 5], dtype=np.int64),
                "small_float": np.array([1.5, 2.5, 3.5, 4.5, 5.5], dtype=np.float64),
            }
        )

        writer = ParquetWriter(optimize_dtypes=True)
        writer.write(df, parquet_file)

        assert parquet_file.exists()
        assert writer.compressed_size > 0

    def test_compression_stats(self, tmp_path):
        """Test compression statistics"""
        parquet_file = tmp_path / "stats.parquet"
        df = pd.DataFrame({"a": range(1000), "b": range(1000, 2000)})

        writer = ParquetWriter()
        writer.write(df, parquet_file)

        stats = writer.get_compression_stats()
        assert "original_size" in stats
        assert "compressed_size" in stats
        assert "compression_ratio" in stats
        # Compression ratio can be < 1 for small, already optimized data
        assert stats["compression_ratio"] > 0

    def test_write_batches(self, tmp_path):
        """Test batch writing for large datasets"""
        parquet_file = tmp_path / "batches.parquet"
        df = pd.DataFrame({"a": range(10000), "b": range(10000, 20000)})

        writer = ParquetWriter()
        writer.write_batches(df, parquet_file, batch_size=2000)

        assert parquet_file.exists()

        # Read back and verify
        df_read = pd.read_parquet(parquet_file)
        assert len(df_read) == 10000

    def test_append(self, tmp_path):
        """Test appending to existing file"""
        parquet_file = tmp_path / "append.parquet"

        # Write initial data
        df1 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        writer = ParquetWriter()
        writer.write(df1, parquet_file)

        # Append more data
        df2 = pd.DataFrame({"a": [7, 8, 9], "b": [10, 11, 12]})
        writer.append(df2, parquet_file)

        # Read back
        df_combined = pd.read_parquet(parquet_file)
        assert len(df_combined) == 6
        assert df_combined["a"].tolist() == [1, 2, 3, 7, 8, 9]

    def test_append_new_file(self, tmp_path):
        """Test appending creates new file if doesn't exist"""
        parquet_file = tmp_path / "new_append.parquet"
        df = pd.DataFrame({"a": [1, 2, 3]})

        writer = ParquetWriter()
        writer.append(df, parquet_file)

        assert parquet_file.exists()
        df_read = pd.read_parquet(parquet_file)
        assert len(df_read) == 3


class TestBatchConverter:
    """Tests for BatchConverter class"""

    def test_converter_initialization(self):
        """Test BatchConverter initialization"""
        converter = BatchConverter()
        assert converter.compression == "zstd"
        assert converter.max_workers == 1

        converter = BatchConverter(max_workers=4, compression="snappy")
        assert converter.max_workers == 4
        assert converter.compression == "snappy"

    def test_convert_directory(self, tmp_path):
        """Test converting a directory of CSV files"""
        # Create test CSV files
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        parquet_dir = tmp_path / "parquet"

        for i in range(3):
            df = pd.DataFrame(
                {"a": range(i * 100, (i + 1) * 100), "b": range(i * 100, (i + 1) * 100)}
            )
            df.to_csv(csv_dir / f"file_{i}.csv", index=False)

        # Convert
        converter = BatchConverter()
        results = converter.convert_directory(csv_dir, parquet_dir)

        # Verify
        assert len(results) == 3
        assert all(r.success for r in results)
        assert all((parquet_dir / f"file_{i}.parquet").exists() for i in range(3))

    def test_convert_files(self, tmp_path):
        """Test converting specific files"""
        # Create test files
        csv_files = []
        for i in range(2):
            csv_file = tmp_path / f"input_{i}.csv"
            df = pd.DataFrame({"a": [1, 2, 3]})
            df.to_csv(csv_file, index=False)
            csv_files.append(csv_file)

        output_dir = tmp_path / "output"

        # Convert
        converter = BatchConverter()
        results = converter.convert_files(csv_files, output_dir)

        assert len(results) == 2
        assert all(r.success for r in results)

    def test_convert_empty_directory(self, tmp_path):
        """Test converting empty directory"""
        csv_dir = tmp_path / "empty_csv"
        csv_dir.mkdir()
        parquet_dir = tmp_path / "parquet"

        converter = BatchConverter()
        results = converter.convert_directory(csv_dir, parquet_dir)

        assert len(results) == 0

    def test_convert_nonexistent_directory(self, tmp_path):
        """Test converting non-existent directory"""
        converter = BatchConverter()

        with pytest.raises(FileError):
            converter.convert_directory("/nonexistent/dir", tmp_path / "out")

    def test_get_summary(self, tmp_path):
        """Test getting conversion summary"""
        # Create test files
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        parquet_dir = tmp_path / "parquet"

        for i in range(2):
            df = pd.DataFrame({"a": range(100)})
            df.to_csv(csv_dir / f"file_{i}.csv", index=False)

        converter = BatchConverter()
        converter.convert_directory(csv_dir, parquet_dir)

        summary = converter.get_summary()
        assert summary["total_files"] == 2
        assert summary["successful"] == 2
        assert summary["failed"] == 0
        assert summary["success_rate"] == 100.0

    def test_conversion_result(self):
        """Test ConversionResult class"""
        result = ConversionResult(
            input_file=Path("input.csv"),
            output_file=Path("output.parquet"),
            success=True,
            rows=100,
            original_size=1000,
            compressed_size=200,
            duration=1.5,
        )

        assert result.success is True
        assert result.compression_ratio == 5.0
        assert "✓" in repr(result)


class TestBatchProcessor:
    """Tests for BatchProcessor class"""

    def test_processor_initialization(self):
        """Test BatchProcessor initialization"""

        def dummy_func(filepath):
            return len(pd.read_parquet(filepath))

        processor = BatchProcessor(dummy_func)
        assert processor.max_workers == 1

        processor = BatchProcessor(dummy_func, max_workers=2)
        assert processor.max_workers == 2

    def test_process_directory(self, tmp_path):
        """Test processing directory of files"""
        # Create test Parquet files
        parquet_dir = tmp_path / "parquet"
        parquet_dir.mkdir()

        for i in range(3):
            df = pd.DataFrame({"a": range(i * 10, (i + 1) * 10)})
            df.to_parquet(parquet_dir / f"file_{i}.parquet", index=False)

        # Define processing function
        def count_rows(filepath):
            df = pd.read_parquet(filepath)
            return len(df)

        # Process
        processor = BatchProcessor(count_rows)
        results = processor.process_directory(parquet_dir)

        assert len(results) == 3
        assert all(r[1] == 10 for r in results)  # Each file has 10 rows
        assert all(r[2] is None for r in results)  # No errors

    def test_process_files(self, tmp_path):
        """Test processing specific files"""
        # Create test files
        files = []
        for i in range(2):
            filepath = tmp_path / f"file_{i}.parquet"
            df = pd.DataFrame({"a": [1, 2, 3]})
            df.to_parquet(filepath, index=False)
            files.append(filepath)

        def get_columns(filepath):
            df = pd.read_parquet(filepath)
            return list(df.columns)

        processor = BatchProcessor(get_columns)
        results = processor.process_files(files)

        assert len(results) == 2
        assert all(r[1] == ["a"] for r in results)


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_write_parquet_function(self, tmp_path):
        """Test write_parquet convenience function"""
        parquet_file = tmp_path / "test.parquet"
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        write_parquet(df, parquet_file)

        assert parquet_file.exists()
        df_read = pd.read_parquet(parquet_file)
        # Check values match, dtypes may be optimized
        assert df_read["a"].tolist() == [1, 2, 3]
        assert df_read["b"].tolist() == [4, 5, 6]

    def test_write_parquet_with_compression(self, tmp_path):
        """Test write_parquet with custom compression"""
        parquet_file = tmp_path / "compressed.parquet"
        df = pd.DataFrame({"a": range(1000)})

        write_parquet(df, parquet_file, compression="snappy")

        assert parquet_file.exists()

    def test_batch_convert_function(self, tmp_path):
        """Test batch_convert convenience function"""
        # Create test CSV files
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()

        for i in range(2):
            df = pd.DataFrame({"a": range(50)})
            df.to_csv(csv_dir / f"file_{i}.csv", index=False)

        parquet_dir = tmp_path / "parquet"

        # Convert
        results = batch_convert(csv_dir, parquet_dir)

        assert len(results) == 2
        assert all(r.success for r in results)


class TestIntegration:
    """Integration tests for writer and batch modules"""

    def test_write_read_cycle(self, tmp_path):
        """Test write and read cycle"""
        parquet_file = tmp_path / "cycle.parquet"

        # Create and write data
        df_original = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=100, freq="h"),
                "power": np.random.randint(0, 1000, 100),
                "efficiency": np.random.uniform(15, 22, 100),
            }
        )

        write_parquet(df_original, parquet_file, optimize_dtypes=True)

        # Read back
        from pvdata.io import read_parquet

        df_read = read_parquet(parquet_file)

        assert len(df_read) == 100
        assert set(df_read.columns) == {"timestamp", "power", "efficiency"}

    def test_csv_to_parquet_workflow(self, tmp_path):
        """Test complete CSV to Parquet workflow"""
        # Create CSV files
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()

        for i in range(3):
            df = pd.DataFrame(
                {
                    "timestamp": pd.date_range("2024-01-01", periods=50, freq="5min"),
                    "value": range(50),
                }
            )
            df.to_csv(csv_dir / f"data_{i}.csv", index=False)

        parquet_dir = tmp_path / "parquet"

        # Convert
        converter = BatchConverter(compression="zstd", compression_level=5)
        results = converter.convert_directory(csv_dir, parquet_dir)

        # Verify
        assert len(results) == 3
        assert all(r.success for r in results)

        summary = converter.get_summary()
        # Compression ratio may be < 1 for very small files with Parquet overhead
        assert summary["avg_compression_ratio"] > 0

    def test_parallel_conversion(self, tmp_path):
        """Test parallel batch conversion"""
        # Create multiple CSV files
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()

        for i in range(5):
            df = pd.DataFrame({"a": range(i * 100, (i + 1) * 100), "b": range(100)})
            df.to_csv(csv_dir / f"file_{i}.csv", index=False)

        parquet_dir = tmp_path / "parquet"

        # Convert with multiple workers
        converter = BatchConverter(max_workers=2)
        results = converter.convert_directory(csv_dir, parquet_dir)

        assert len(results) == 5
        assert all(r.success for r in results)
        assert all((parquet_dir / f"file_{i}.parquet").exists() for i in range(5))
