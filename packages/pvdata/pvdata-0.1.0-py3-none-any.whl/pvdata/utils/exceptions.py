"""
Custom exceptions for pvdata package

This module defines a hierarchy of exceptions for better error handling
and debugging throughout the pvdata package.
"""


class PVDataError(Exception):
    """Base exception for all pvdata errors"""

    pass


class ConfigurationError(PVDataError):
    """Raised when there's a configuration issue"""

    pass


class ValidationError(PVDataError):
    """Raised when data validation fails"""

    pass


class FileError(PVDataError):
    """Base exception for file-related errors"""

    pass


class FileNotFoundError(FileError):
    """Raised when a required file is not found"""

    pass


class FileFormatError(FileError):
    """Raised when file format is invalid or unsupported"""

    pass


class DataTypeError(PVDataError):
    """Raised when data type conversion or optimization fails"""

    pass


class CompressionError(PVDataError):
    """Raised when compression/decompression fails"""

    pass


class QueryError(PVDataError):
    """Raised when a query operation fails"""

    pass


class ProcessingError(PVDataError):
    """Raised when data processing fails"""

    pass


class OptimizationError(PVDataError):
    """Raised when optimization fails"""

    pass
