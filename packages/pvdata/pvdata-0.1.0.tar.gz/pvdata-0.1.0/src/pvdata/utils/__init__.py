"""
pvdata.utils - Utility functions

This module provides configuration, logging, and profiling utilities.
"""

# Configuration management (TASK_02 - Completed)
from pvdata.config import ConfigManager, config, ParquetConfig, DTypeMapper

# Logging and error handling (TASK_03 - Completed)
from pvdata.utils.logger import setup_logger, get_logger, set_log_level
from pvdata.utils.exceptions import (
    PVDataError,
    ConfigurationError,
    ValidationError,
    FileError,
    FileNotFoundError,
    FileFormatError,
    DataTypeError,
    CompressionError,
    QueryError,
    ProcessingError,
    OptimizationError,
)
from pvdata.utils.decorators import (
    handle_errors,
    log_execution,
    measure_time,
    validate_args,
    retry,
)

__all__ = [
    # Configuration
    "ConfigManager",
    "config",
    "ParquetConfig",
    "DTypeMapper",
    # Logging
    "setup_logger",
    "get_logger",
    "set_log_level",
    # Exceptions
    "PVDataError",
    "ConfigurationError",
    "ValidationError",
    "FileError",
    "FileNotFoundError",
    "FileFormatError",
    "DataTypeError",
    "CompressionError",
    "QueryError",
    "ProcessingError",
    "OptimizationError",
    # Decorators
    "handle_errors",
    "log_execution",
    "measure_time",
    "validate_args",
    "retry",
]
