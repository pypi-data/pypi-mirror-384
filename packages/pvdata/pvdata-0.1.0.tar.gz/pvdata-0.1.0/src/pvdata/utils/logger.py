"""
Logging utilities for pvdata package

Provides consistent logging across the package with configurable
output formats and log levels.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(levelname)s: %(message)s"
DETAILED_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
)


def setup_logger(
    name: str = "pvdata",
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[Path] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Set up a logger with specified configuration

    Args:
        name: Logger name (default: 'pvdata')
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        format_string: Custom format string (default: DEFAULT_FORMAT)
        log_file: Optional file path for file output
        console: Whether to log to console (default: True)

    Returns:
        Configured logger instance

    Examples:
        >>> logger = setup_logger('pvdata.io', level='DEBUG')
        >>> logger.info('Processing file...')

        >>> # Log to file
        >>> logger = setup_logger(
        ...     'pvdata',
        ...     log_file=Path('pvdata.log'),
        ...     console=False
        ... )
    """
    logger = logging.getLogger(name)

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Use default format if not specified
    if format_string is None:
        format_string = DEFAULT_FORMAT

    formatter = logging.Formatter(format_string)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the specified name

    Args:
        name: Logger name

    Returns:
        Logger instance

    Examples:
        >>> logger = get_logger('pvdata.io')
        >>> logger.info('Message')
    """
    return logging.getLogger(name)


def set_log_level(level: str, logger_name: Optional[str] = None) -> None:
    """
    Set log level for a logger or all pvdata loggers

    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        logger_name: Optional specific logger name (default: all pvdata loggers)

    Examples:
        >>> set_log_level('DEBUG')  # Set all pvdata loggers to DEBUG
        >>> set_log_level('WARNING', 'pvdata.io')  # Set specific logger
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    if logger_name:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)
    else:
        # Set level for all pvdata loggers
        for name in logging.Logger.manager.loggerDict:
            if name.startswith("pvdata"):
                logging.getLogger(name).setLevel(numeric_level)


# Create default package logger
_default_logger = setup_logger("pvdata", level="INFO", format_string=SIMPLE_FORMAT)
