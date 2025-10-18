"""
Tests for IO module (readers and operations)
"""

import pytest
import pandas as pd
import numpy as np

from pvdata.io.reader import CSVReader, ParquetReader
from pvdata.io.operations import read_csv, read_parquet, get_parquet_info
from pvdata.utils.exceptions import FileNotFoundError, FileFormatError


class TestCSVReader:
    """Tests for CSVReader class"""

    def test_csv_reader_initialization(self):
        """Test CSVReader initialization"""
        reader = CSVReader()
        assert reader.optimize_dtypes is True

        reader = CSVReader(optimize_dtypes=False)
        assert reader.optimize_dtypes is False

    def test_read_csv_basic(self, tmp_path):
        """Test basic CSV reading"""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        df_original = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0], "c": ["x", "y", "z"]})
        df_original.to_csv(csv_file, index=False)

        # Read CSV
        reader = CSVReader()
        df = reader.read(csv_file)

        # Verify data
        assert len(df) == 3
        assert list(df.columns) == ["a", "b", "c"]
        assert df["a"].tolist() == [1, 2, 3]

    def test_read_csv_with_optimization(self, tmp_path):
        """Test CSV reading with dtype optimization"""
        # Create test CSV with large dtypes
        csv_file = tmp_path / "test_opt.csv"
        df_original = pd.DataFrame(
            {
                "small_int": np.array([1, 2, 3, 4, 5], dtype=np.int64),
                "small_float": np.array([1.5, 2.5, 3.5, 4.5, 5.5], dtype=np.float64),
            }
        )
        df_original.to_csv(csv_file, index=False)

        # Read with optimization
        reader = CSVReader(optimize_dtypes=True)
        df = reader.read(csv_file)

        # Check memory was saved
        assert reader.memory_saved_pct > 0
        assert reader.memory_after < reader.memory_before

        # Verify dtypes were optimized
        assert df["small_int"].dtype in [np.uint8, np.int8, np.uint16, np.int16]

    def test_read_csv_without_optimization(self, tmp_path):
        """Test CSV reading without dtype optimization"""
        csv_file = tmp_path / "test_no_opt.csv"
        df_original = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        df_original.to_csv(csv_file, index=False)

        reader = CSVReader(optimize_dtypes=False)
        reader.read(csv_file)

        # No optimization should occur
        assert reader.memory_saved_pct == 0.0
        assert reader.memory_before == reader.memory_after

    def test_read_csv_file_not_found(self):
        """Test reading non-existent file"""
        reader = CSVReader()
        with pytest.raises(FileNotFoundError):
            reader.read("/nonexistent/file.csv")

    def test_read_csv_with_pandas_args(self, tmp_path):
        """Test CSV reading with pandas arguments"""
        csv_file = tmp_path / "test_args.csv"
        df_original = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df_original.to_csv(csv_file, index=False, sep=";")

        reader = CSVReader()
        df = reader.read(csv_file, sep=";")

        assert len(df) == 3
        assert list(df.columns) == ["a", "b"]

    def test_read_chunks(self, tmp_path):
        """Test reading CSV in chunks"""
        csv_file = tmp_path / "test_chunks.csv"
        df_original = pd.DataFrame({"a": range(100), "b": range(100, 200)})
        df_original.to_csv(csv_file, index=False)

        reader = CSVReader()
        chunks = list(reader.read_chunks(csv_file, chunksize=25))

        # Should have 4 chunks
        assert len(chunks) == 4

        # Each chunk should have 25 rows
        for chunk in chunks:
            assert len(chunk) == 25

        # Verify total data
        df_combined = pd.concat(chunks, ignore_index=True)
        assert len(df_combined) == 100

    def test_read_chunks_with_optimization(self, tmp_path):
        """Test reading chunks with optimization"""
        csv_file = tmp_path / "test_chunks_opt.csv"
        df_original = pd.DataFrame({"a": np.array(range(50), dtype=np.int64)})
        df_original.to_csv(csv_file, index=False)

        reader = CSVReader(optimize_dtypes=True)
        chunks = list(reader.read_chunks(csv_file, chunksize=10))

        # Verify dtypes are optimized in chunks
        for chunk in chunks:
            assert chunk["a"].dtype in [np.uint8, np.int8, np.uint16, np.int16]


class TestParquetReader:
    """Tests for ParquetReader class"""

    def test_parquet_reader_initialization(self):
        """Test ParquetReader initialization"""
        reader = ParquetReader()
        assert reader.file_metadata is None

    def test_read_parquet_basic(self, tmp_path):
        """Test basic Parquet reading"""
        # Create test Parquet file
        parquet_file = tmp_path / "test.parquet"
        df_original = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0], "c": ["x", "y", "z"]})
        df_original.to_parquet(parquet_file, index=False)

        # Read Parquet
        reader = ParquetReader()
        df = reader.read(parquet_file)

        # Verify data
        assert len(df) == 3
        assert list(df.columns) == ["a", "b", "c"]
        pd.testing.assert_frame_equal(df, df_original)

    def test_read_parquet_columns(self, tmp_path):
        """Test reading specific columns"""
        parquet_file = tmp_path / "test_cols.parquet"
        df_original = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
        df_original.to_parquet(parquet_file, index=False)

        reader = ParquetReader()
        df = reader.read(parquet_file, columns=["a", "c"])

        # Should only have selected columns
        assert list(df.columns) == ["a", "c"]
        assert len(df) == 3

    def test_read_parquet_file_not_found(self):
        """Test reading non-existent file"""
        reader = ParquetReader()
        with pytest.raises(FileNotFoundError):
            reader.read("/nonexistent/file.parquet")

    def test_get_metadata(self, tmp_path):
        """Test getting Parquet metadata"""
        parquet_file = tmp_path / "test_meta.parquet"
        df_original = pd.DataFrame({"a": range(100), "b": range(100, 200), "c": range(200, 300)})
        df_original.to_parquet(parquet_file, index=False)

        reader = ParquetReader()
        metadata = reader.get_metadata(parquet_file)

        # Verify metadata
        assert metadata["num_rows"] == 100
        assert metadata["num_columns"] == 3
        assert set(metadata["columns"]) == {"a", "b", "c"}
        assert metadata["num_row_groups"] >= 1

    def test_get_metadata_file_not_found(self):
        """Test getting metadata for non-existent file"""
        reader = ParquetReader()
        with pytest.raises(FileNotFoundError):
            reader.get_metadata("/nonexistent/file.parquet")

    def test_read_row_group(self, tmp_path):
        """Test reading specific row group"""
        parquet_file = tmp_path / "test_rowgroup.parquet"
        df_original = pd.DataFrame({"a": range(1000), "b": range(1000, 2000)})
        # Write with small row groups
        df_original.to_parquet(parquet_file, index=False, row_group_size=250)

        reader = ParquetReader()

        # Read first row group
        df_rg = reader.read_row_group(parquet_file, 0)

        # Should have data from first row group
        assert len(df_rg) == 250
        assert list(df_rg.columns) == ["a", "b"]

    def test_read_row_group_out_of_range(self, tmp_path):
        """Test reading row group with invalid index"""
        parquet_file = tmp_path / "test_rg_range.parquet"
        df_original = pd.DataFrame({"a": [1, 2, 3]})
        df_original.to_parquet(parquet_file, index=False)

        reader = ParquetReader()

        with pytest.raises(FileFormatError, match="out of range"):
            reader.read_row_group(parquet_file, 999)


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_read_csv_function(self, tmp_path):
        """Test read_csv convenience function"""
        csv_file = tmp_path / "test.csv"
        df_original = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df_original.to_csv(csv_file, index=False)

        # Read using convenience function
        df = read_csv(csv_file)

        assert len(df) == 3
        assert list(df.columns) == ["a", "b"]

    def test_read_csv_function_no_optimization(self, tmp_path):
        """Test read_csv with optimization disabled"""
        csv_file = tmp_path / "test_no_opt.csv"
        df_original = pd.DataFrame({"a": [1, 2, 3]})
        df_original.to_csv(csv_file, index=False)

        df = read_csv(csv_file, optimize_dtypes=False)
        assert len(df) == 3

    def test_read_parquet_function(self, tmp_path):
        """Test read_parquet convenience function"""
        parquet_file = tmp_path / "test.parquet"
        df_original = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df_original.to_parquet(parquet_file, index=False)

        df = read_parquet(parquet_file)

        pd.testing.assert_frame_equal(df, df_original)

    def test_read_parquet_function_with_columns(self, tmp_path):
        """Test read_parquet with column selection"""
        parquet_file = tmp_path / "test_cols.parquet"
        df_original = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
        df_original.to_parquet(parquet_file, index=False)

        df = read_parquet(parquet_file, columns=["a", "b"])

        assert list(df.columns) == ["a", "b"]
        assert len(df) == 3

    def test_get_parquet_info_function(self, tmp_path):
        """Test get_parquet_info convenience function"""
        parquet_file = tmp_path / "test_info.parquet"
        df_original = pd.DataFrame({"a": range(50), "b": range(50, 100)})
        df_original.to_parquet(parquet_file, index=False)

        info = get_parquet_info(parquet_file)

        assert info["num_rows"] == 50
        assert info["num_columns"] == 2
        assert set(info["columns"]) == {"a", "b"}


class TestIntegration:
    """Integration tests for IO module"""

    def test_csv_to_parquet_workflow(self, tmp_path):
        """Test reading CSV and writing Parquet"""
        # Create CSV
        csv_file = tmp_path / "input.csv"
        df_original = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=100, freq="h"),
                "power": np.random.randint(0, 1000, 100),
                "voltage": np.random.uniform(220, 240, 100),
            }
        )
        df_original.to_csv(csv_file, index=False)

        # Read CSV with optimization
        df_csv = read_csv(csv_file, optimize_dtypes=True)

        # Write to Parquet
        parquet_file = tmp_path / "output.parquet"
        df_csv.to_parquet(parquet_file, index=False)

        # Read back Parquet
        df_parquet = read_parquet(parquet_file)

        # Verify data integrity
        assert len(df_parquet) == 100
        assert set(df_parquet.columns) == {"timestamp", "power", "voltage"}

    def test_large_file_chunked_processing(self, tmp_path):
        """Test processing large file in chunks"""
        # Create large CSV
        csv_file = tmp_path / "large.csv"
        df_original = pd.DataFrame({"a": range(10000), "b": range(10000, 20000)})
        df_original.to_csv(csv_file, index=False)

        # Process in chunks
        reader = CSVReader()
        total_sum = 0
        chunk_count = 0

        for chunk in reader.read_chunks(csv_file, chunksize=1000):
            total_sum += chunk["a"].sum()
            chunk_count += 1

        # Verify
        assert chunk_count == 10
        assert total_sum == sum(range(10000))

    def test_parquet_column_projection(self, tmp_path):
        """Test reading only needed columns from Parquet"""
        # Create Parquet with many columns
        parquet_file = tmp_path / "wide.parquet"
        df_original = pd.DataFrame({f"col_{i}": range(100) for i in range(20)})
        df_original.to_parquet(parquet_file, index=False)

        # Read only 2 columns
        df_subset = read_parquet(parquet_file, columns=["col_0", "col_10"])

        # Verify
        assert len(df_subset.columns) == 2
        assert list(df_subset.columns) == ["col_0", "col_10"]
        assert len(df_subset) == 100
