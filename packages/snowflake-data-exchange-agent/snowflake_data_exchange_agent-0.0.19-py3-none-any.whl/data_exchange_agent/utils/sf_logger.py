"""
Enhanced logging utilities for the data exchange agent.

This module provides the SFLogger class which implements enhanced logging
functionality with file rotation, custom formatting, and integration with
the data exchange agent's logging infrastructure.
"""

import logging
import os
import sys

from data_exchange_agent.constants.paths import ROOT_LOGS_FOLDER_PATH


class SFLogger:
    """
    Custom logging class with enhanced functionality for the data exchange agent.

    This class provides structured logging with file and console output,
    configurable log levels, and context-aware formatting.

    This is implemented as a singleton to ensure only one logger instance exists.
    """

    def __init__(
        self,
        name: str = "data_exchange_agent",
        log_level: str = "INFO",
        log_dir: str | None = None,
        console_output: bool = True,
        file_output: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ) -> None:
        """
        Initialize the custom logger.

        Args:
            name: Logger name (typically module or class name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (defaults to logs/ in project root)
            console_output: Whether to output logs to console
            file_output: Whether to output logs to file
            max_file_size: Maximum size of log file before rotation
            backup_count: Number of backup files to keep

        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        log_dir = ROOT_LOGS_FOLDER_PATH
        os.makedirs(log_dir, exist_ok=True)

        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )

        # Set up file handler with rotation
        if file_output:
            from logging.handlers import RotatingFileHandler

            log_file = os.path.join(log_dir, f"{name}.log")
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_file_size, backupCount=backup_count
            )
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)

        # Set up console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, exception: Exception | None = None, **kwargs) -> None:
        """
        Log error message with optional exception details.

        Args:
            message: Error message
            exception: Optional exception to log with traceback
            **kwargs: Additional logging arguments

        """
        self.logger.error(message, **kwargs)
        if exception:
            self.logger.exception("Exception details:", exc_info=exception)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, **kwargs)

    def log_task_start(self, task_id: str, task_type: str) -> None:
        """
        Log task start with structured information.

        Args:
            task_id: Unique task identifier
            task_type: Type of task being started

        """
        self.info(f"TASK_START | ID: {task_id} | Type: {task_type}")

    def log_task_complete(
        self, task_id: str, duration: float, records_processed: int = 0
    ) -> None:
        """
        Log task completion with metrics.

        Args:
            task_id: Unique task identifier
            duration: Task execution time in seconds
            records_processed: Number of records processed

        """
        self.info(
            f"TASK_COMPLETE | ID: {task_id} | Duration: {duration:.2f}s | Records: {records_processed}"
        )

    def log_task_error(
        self, task_id: str, error: Exception, context: dict | None = None
    ) -> None:
        """
        Log task error with context.

        Args:
            task_id: Unique task identifier
            error: Exception that occurred
            context: Additional context information

        """
        context_str = f" | Context: {context}" if context else ""
        self.error(
            f"TASK_ERROR | ID: {task_id} | Error: {str(error)}{context_str}",
            exception=error,
        )

    def log_data_operation(
        self, operation: str, source: str, records: int, duration: float
    ) -> None:
        """
        Log data operation metrics.

        Args:
            operation: Type of operation (extract, transform, load)
            source: Data source identifier
            records: Number of records processed
            duration: Operation duration in seconds

        """
        self.info(
            f"DATA_OP | Operation: {operation} | Source: {source} | Records: {records} | Duration: {duration:.2f}s"
        )

    def set_level(self, level: str) -> None:
        """
        Change the logging level.

        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        """
        self.logger.setLevel(getattr(logging, level.upper()))
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, level.upper()))
