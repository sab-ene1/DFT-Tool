"""Logging configuration for the Digital Forensics Triage Tool."""

import logging
import os
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

def setup_logging(log_file: Optional[str] = None) -> None:
    """Configure logging for the application.
    
    Args:
        log_file: Optional path to log file. If None, logs only to console.
    """
    # Create log directory if it doesn't exist
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create a file handler that logs messages to a file
    if log_file:
        handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Create console handler for stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)

    logger.info("Logging is set up.")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)
