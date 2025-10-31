"""Logging configuration for IMP application."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class IMPLogger:
    """Logger class for IMP application."""

    _instance: Optional[logging.Logger] = None

    @classmethod
    def get_logger(
        cls,
        name: str = "IMP",
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        Get or create logger instance.

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep

        Returns:
            Logger instance
        """
        if cls._instance is not None:
            return cls._instance

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))

        # Remove existing handlers
        logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if log_file is provided)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        cls._instance = logger
        return logger

    @classmethod
    def reset(cls):
        """Reset logger instance."""
        cls._instance = None
