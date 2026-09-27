"""Centralized logging module for the Enterprise Business Report Generator.

Configures file and console logging with configurable logging levels,
proper formatting, and directory resolution.
"""

import logging
import os
from pathlib import Path
from typing import Optional

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(
    log_dir: Optional[str | Path] = None,
    log_file_name: str = "application.log",
    log_level: str = "INFO",
    enable_console: bool = False,
) -> logging.Logger:
    """Configure centralized logging for the application.

    Args:
        log_dir: Directory where log files are stored. Defaults to 'logs'.
        log_file_name: Name of the log file. Defaults to 'application.log'.
        log_level: Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        enable_console: If True, attach a stream handler to log to console.

    Returns:
        The root or application logger instance.
    """
    global _configured

    if log_dir is None:
        log_dir = Path(os.getenv("LOG_DIRECTORY", "logs"))
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / log_file_name

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger("report_generator")
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not _configured:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

        # File Handler (logs to logs/application.log)
        file_handler = logging.FileHandler(str(log_file_path), encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Optional Console Handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        root_logger.propagate = False
        _configured = True

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Retrieve a namespaced child logger.

    Args:
        name: Name of the module or component requesting a logger.

    Returns:
        logging.Logger configured for the component.
    """
    if not _configured:
        setup_logging()

    if name:
        return logging.getLogger(f"report_generator.{name}")
    return logging.getLogger("report_generator")
