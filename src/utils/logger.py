import logging
import os
import sys


def setup_logger(
    name: str, level: str | None = None, format_string: str | None = None
) -> logging.Logger:
    """Set up a logger with consistent formatting"""

    # Get log level from environment or default to INFO
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level))

    # Create formatter
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Don't propagate to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return setup_logger(name)
