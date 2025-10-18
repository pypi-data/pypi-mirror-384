"""
Tests for configuration module
"""

import pytest
import pandas as pd
import numpy as np

from pvdata.config import (
    ParquetConfig,
    DTypeMapper,
    ConfigManager,
    config,
)


class TestParquetConfig:
    """Tests for ParquetConfig class"""

    def test_standard_preset(self):
        """Test STANDARD preset"""
        preset = ParquetConfig.STANDARD
        assert preset.compression == "snappy"
        assert preset.row_group_size == 100000
        assert preset.use_dictionary is True
        assert preset.optimize_dtypes is False

    def test_optimized_preset(self):
        """Test OPTIMIZED preset"""
        preset = ParquetConfig.OPTIMIZED
        assert preset.compression == "zstd"
        assert preset.compression_level == 3
        assert preset.optimize_dtypes is True

    def test_fast_preset(self):
        """Test FAST preset"""
        preset = ParquetConfig.FAST
        assert preset.compression == "snappy"
        assert preset.row_group_size == 500000
        assert preset.use_dictionary is False

    def test_get_preset(self):
        """Test getting preset by name"""
        preset = ParquetConfig.get_preset("optimized")
        assert preset.compression == "zstd"

        preset = ParquetConfig.get_preset("STANDARD")
        assert preset.compression == "snappy"

    def test_get_preset_invalid(self):
        """Test getting invalid preset name"""
        with pytest.raises(ValueError, match="Unknown preset"):
            ParquetConfig.get_preset("invalid_preset")

    def test_create_custom(self):
        """Test creating custom configuration"""
        custom = ParquetConfig.create_custom(
            compression="gzip", compression_level=6, row_group_size=50000
        )
        assert custom.compression == "gzip"
        assert custom.compression_level == 6
        assert custom.row_group_size == 50000

    def test_to_dict(self):
        """Test conversion to dictionary"""
        preset = ParquetConfig.OPTIMIZED
        d = preset.to_dict()
        assert isinstance(d, dict)
        assert d["compression"] == "zstd"
        assert d["compression_level"] == 3


class TestDTypeMapper:
    """Tests for DTypeMapper class"""

    def test_default_map(self):
        """Test default dtype mapping"""
        assert DTypeMapper.DEFAULT_MAP["Year"] == "int16"
        assert DTypeMapper.DEFAULT_MAP["Month"] == "int8"
        assert DTypeMapper.DEFAULT_MAP["eff"] == "float32"

    def test_optimize_integer_small(self):
        """Test optimizing small integers"""
        s = pd.Series([1, 2, 3, 4, 5], dtype="int64")
        dtype = DTypeMapper.optimize_dtype(s)
        # Positive integers optimize to unsigned types
        assert dtype == "uint8"

    def test_optimize_integer_large(self):
        """Test optimizing large integers"""
        s = pd.Series([1000, 2000, 3000], dtype="int64")
        dtype = DTypeMapper.optimize_dtype(s)
        # Positive integers optimize to unsigned types
        assert dtype == "uint16"

    def test_optimize_float(self):
        """Test optimizing float"""
        s = pd.Series([1.1, 2.2, 3.3], dtype="float64")
        dtype = DTypeMapper.optimize_dtype(s)
        assert dtype == "float32"

    def test_optimize_unsigned(self):
        """Test optimizing unsigned integers"""
        s = pd.Series([0, 10, 20, 30], dtype="int64")
        dtype = DTypeMapper.optimize_dtype(s)
        assert dtype == "uint8"

    def test_apply_mapping(self):
        """Test applying dtype mapping to DataFrame"""
        df = pd.DataFrame(
            {"Year": [2020, 2021, 2022], "Month": [1, 2, 3], "eff": [85.5, 90.2, 88.1]}
        )

        df_opt = DTypeMapper.apply_mapping(df)

        assert df_opt["Year"].dtype == np.int16
        assert df_opt["Month"].dtype == np.int8
        assert df_opt["eff"].dtype == np.float32

    def test_apply_mapping_custom(self):
        """Test applying custom dtype mapping"""
        df = pd.DataFrame({"col1": [1, 2, 3]})

        custom_map = {"col1": "int8"}
        df_opt = DTypeMapper.apply_mapping(df, custom_map=custom_map)

        assert df_opt["col1"].dtype == np.int8

    def test_apply_mapping_auto_optimize(self):
        """Test auto-optimization of unmapped columns"""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [1.1, 2.2, 3.3]})

        df_opt = DTypeMapper.apply_mapping(df, auto_optimize=True)

        # Positive integers optimize to unsigned types
        assert df_opt["col1"].dtype == np.uint8
        assert df_opt["col2"].dtype == np.float32

    def test_get_memory_savings(self):
        """Test calculating memory savings"""
        df = pd.DataFrame(
            {
                "Year": pd.Series([2020, 2021, 2022], dtype="int64"),
                "eff": pd.Series([85.5, 90.2, 88.1], dtype="float64"),
            }
        )

        df_opt = DTypeMapper.apply_mapping(df)
        stats = DTypeMapper.get_memory_savings(df, df_opt)

        assert stats["savings_percent"] > 0
        assert stats["memory_after_mb"] < stats["memory_before_mb"]


class TestConfigManager:
    """Tests for ConfigManager class"""

    def test_init(self):
        """Test initialization"""
        cfg = ConfigManager()
        assert cfg.get("compression") == "zstd"
        assert cfg.get("n_jobs") == -1

    def test_get_set(self):
        """Test getting and setting values"""
        cfg = ConfigManager()
        cfg.set("test_key", "test_value")
        assert cfg.get("test_key") == "test_value"

    def test_get_default(self):
        """Test getting with default value"""
        cfg = ConfigManager()
        assert cfg.get("nonexistent", "default") == "default"

    def test_get_nested(self):
        """Test getting nested keys"""
        cfg = ConfigManager()
        cfg.set("parent.child", "value")
        assert cfg.get("parent.child") == "value"

    def test_update(self):
        """Test updating multiple values"""
        cfg = ConfigManager()
        cfg.update({"key1": "value1", "key2": "value2"})
        assert cfg.get("key1") == "value1"
        assert cfg.get("key2") == "value2"

    def test_reset(self):
        """Test resetting to defaults"""
        cfg = ConfigManager()
        cfg.set("compression", "snappy")
        cfg.reset()
        assert cfg.get("compression") == "zstd"

    def test_to_dict(self):
        """Test converting to dictionary"""
        cfg = ConfigManager()
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert "compression" in d

    def test_temporary_context(self):
        """Test temporary configuration context"""
        cfg = ConfigManager()
        cfg.set("compression", "zstd")

        with cfg.temporary(compression="snappy"):
            assert cfg.get("compression") == "snappy"

        assert cfg.get("compression") == "zstd"

    def test_save_load_json(self, tmp_path):
        """Test saving and loading JSON configuration"""
        cfg = ConfigManager()
        cfg.set("test_key", "test_value")

        config_file = tmp_path / "config.json"
        cfg.save_to_file(config_file)

        cfg2 = ConfigManager()
        cfg2.load_from_file(config_file)

        assert cfg2.get("test_key") == "test_value"

    def test_load_nonexistent_file(self):
        """Test loading non-existent file"""
        cfg = ConfigManager()
        with pytest.raises(FileNotFoundError):
            cfg.load_from_file("nonexistent.json")

    def test_unsupported_format(self, tmp_path):
        """Test unsupported file format"""
        cfg = ConfigManager()
        config_file = tmp_path / "config.txt"

        with pytest.raises(ValueError, match="Unsupported configuration file format"):
            cfg.save_to_file(config_file)

    def test_repr(self):
        """Test string representation"""
        cfg = ConfigManager()
        repr_str = repr(cfg)
        assert "ConfigManager" in repr_str

    def test_str(self):
        """Test human-readable string"""
        cfg = ConfigManager()
        str_repr = str(cfg)
        assert "compression" in str_repr


class TestGlobalConfig:
    """Tests for global config instance"""

    def test_global_config_exists(self):
        """Test that global config instance exists"""
        assert config is not None
        assert isinstance(config, ConfigManager)

    def test_global_config_usage(self):
        """Test using global config"""
        original_value = config.get("compression")

        config.set("compression", "test_value")
        assert config.get("compression") == "test_value"

        # Reset to original
        config.set("compression", original_value)
