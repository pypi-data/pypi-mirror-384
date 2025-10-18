"""
Configuration management for pvdata

This module provides configuration presets and utilities for optimizing
Parquet storage and data type management.
"""

from pvdata.config.parquet import ParquetConfig, ParquetConfigPreset
from pvdata.config.dtype_mapper import DTypeMapper
from pvdata.config.manager import ConfigManager, config

__all__ = [
    "ParquetConfig",
    "ParquetConfigPreset",
    "DTypeMapper",
    "ConfigManager",
    "config",
]
