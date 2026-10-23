"""Structured logging configuration with rotating files, Rich console, and in-memory log buffer."""

from __future__ import annotations

import collections
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Deque, List
from rich.logging import RichHandler
from src.core.settings import get_settings


class InMemoryLogBuffer(logging.Handler):
    """Circular buffer holding the most recent N log records for the TUI LOGS screen."""

    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.buffer: Deque[logging.LogRecord] = collections.deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        self.buffer.append(record)

    def get_records(self, limit: int = 200, level_filter: str = "ALL") -> List[logging.LogRecord]:
        records = list(self.buffer)
        if level_filter and level_filter.upper() != "ALL":
            target_level = getattr(logging, level_filter.upper(), logging.INFO)
            records = [r for r in records if r.levelno >= target_level]
        return records[-limit:]

    def clear(self) -> None:
        self.buffer.clear()


# Global in-memory log buffer
_memory_buffer = InMemoryLogBuffer(capacity=1000)


def setup_logging(log_level: str | None = None, log_file: Path | None = None) -> logging.Logger:
    """Initialize structured application logging."""
    settings = get_settings()
    level_str = log_level or settings.log_level
    level = getattr(logging, level_str.upper(), logging.INFO)
    file_path = log_file or settings.log_file

    logger = logging.getLogger("iot_ids")
    logger.setLevel(logging.DEBUG)  # Capture all; handlers filter

    # Prevent duplicate handlers on re-initialization
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. Rotating File Handler (bounded size)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=settings.max_log_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s:%(module)s:%(lineno)d] %(message)s"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)
    except Exception as exc:
        print(f"Warning: Failed to initialize file logger: {exc}")

    # 2. Rich Console Handler (for beautiful terminal execution outside TUI)
    rich_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
        tracebacks_show_locals=False
    )
    rich_handler.setLevel(level)
    logger.addHandler(rich_handler)

    # 3. In-memory buffer handler (for TUI)
    _memory_buffer.setLevel(logging.DEBUG)
    logger.addHandler(_memory_buffer)

    return logger


def get_logger(name: str = "iot_ids") -> logging.Logger:
    """Get a logger instance under the iot_ids namespace."""
    return logging.getLogger(f"iot_ids.{name}")


def get_log_buffer() -> InMemoryLogBuffer:
    """Get the active in-memory circular log buffer for TUI display."""
    return _memory_buffer
