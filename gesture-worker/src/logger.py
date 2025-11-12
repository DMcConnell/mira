"""
Logger utility module - provides standardized logging configuration for the gesture worker.
"""

import logging
import sys
from typing import Optional

from .config import ENV

# Configure root logger
_logger_configured = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    If name is None, returns the root logger.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    global _logger_configured

    if not _logger_configured:
        # Set log level based on environment
        log_level = logging.DEBUG if ENV == "pi" else logging.INFO

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Create console handler with formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        # Add handler to root logger
        root_logger.addHandler(console_handler)

        _logger_configured = True

    if name:
        return logging.getLogger(name)
    return logging.getLogger()
