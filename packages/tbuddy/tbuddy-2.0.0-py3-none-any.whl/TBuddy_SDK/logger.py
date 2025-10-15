"""Structured logging for TBuddy SDK"""
import logging
import sys
import json
from typing import Any, Dict, Optional
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include any extra fields
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)

        # Include exception info if present
        if record.exc_info:
            log_record["error_type"] = type(record.exc_info[1]).__name__
            log_record["error_message"] = str(record.exc_info[1])

        return json.dumps(log_record)


class StructuredLogger:
    """Structured logger with JSON and text output support"""

    def __init__(self, name: str, level: str = "INFO", format_type: str = "json"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create handler
        handler = logging.StreamHandler(sys.stdout)

        # Set formatter
        if format_type == "json":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare extra context for logging"""
        return extra or {}

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra={"extra_data": self._add_context(kwargs)})

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={"extra_data": self._add_context(kwargs)})

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={"extra_data": self._add_context(kwargs)})

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        context = kwargs.copy()
        self.logger.error(
            message,
            extra={"extra_data": self._add_context(context)},
            exc_info=error,
        )

    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra={"extra_data": self._add_context(kwargs)})


def get_logger(name: str, level: str = "INFO", format_type: str = "json") -> StructuredLogger:
    """
    Get or create a structured logger

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type (json or text)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, level, format_type)
