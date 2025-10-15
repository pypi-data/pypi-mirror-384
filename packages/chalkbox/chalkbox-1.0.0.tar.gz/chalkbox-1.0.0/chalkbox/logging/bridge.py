import json
import logging
from pathlib import Path
from typing import Any

from rich.logging import RichHandler

from ..core.console import get_console
from ..core.theme import get_theme


class ChalkBoxRichHandler(RichHandler):
    """Extended RichHandler with ChalkBox theming."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with ChalkBox defaults."""
        console = kwargs.pop("console", get_console())
        kwargs.setdefault("rich_tracebacks", True)
        kwargs.setdefault("markup", True)
        kwargs.setdefault("show_time", True)
        kwargs.setdefault("show_level", True)
        kwargs.setdefault("show_path", True)

        super().__init__(console=console, **kwargs)

        self.theme = get_theme()
        self._setup_level_styles()

    def _setup_level_styles(self) -> None:
        """Setup level-specific styles."""
        # NOTE: RichHandler's highlighter doesn't have a highlights attribute
        # This is a no-op for now but kept for potential custom highlighting
        pass


class JSONFileHandler(logging.Handler):
    """Handler that writes JSON logs to a file for machine parsing."""

    def __init__(self, filename: str, **kwargs: Any) -> None:
        """Initialize JSON file handler."""
        super().__init__(**kwargs)
        self.filename = Path(filename)
        self.filename.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:
        """Write log record as JSON."""
        try:
            log_entry = {
                "timestamp": record.created,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            if hasattr(record, "extra_data"):
                log_entry["extra"] = record.extra_data

            if record.exc_info:
                import traceback

                log_entry["exception"] = traceback.format_exception(*record.exc_info)

            with open(self.filename, "a") as f:
                json.dump(log_entry, f)
                f.write("\n")
        except Exception:
            self.handleError(record)


def setup_logging(
    level: str = "INFO",
    format: str | None = None,
    json_file: str | None = None,
    show_time: bool = True,
    show_level: bool = True,
    show_path: bool = True,
    rich_tracebacks: bool = True,
) -> logging.Logger:
    """Setup opinionated logging configuration."""
    root_logger = logging.getLogger()

    # Clear existing handlers
    root_logger.handlers.clear()

    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    rich_handler = ChalkBoxRichHandler(
        show_time=show_time,
        show_level=show_level,
        show_path=show_path,
        rich_tracebacks=rich_tracebacks,
    )

    if format:
        rich_handler.setFormatter(logging.Formatter(format))

    root_logger.addHandler(rich_handler)

    # Add JSON handler if requested
    if json_file:
        json_handler = JSONFileHandler(json_file)
        json_handler.setLevel(log_level)
        root_logger.addHandler(json_handler)

    return root_logger


def get_logger(name: str, level: str | None = None, **kwargs: Any) -> logging.Logger:
    """Get a logger with ChalkBox configuration."""
    if not logging.getLogger().handlers:
        setup_logging(level=level or "INFO", **kwargs)

    logger = logging.getLogger(name)

    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)

    return logger


class StructuredLogger:
    """Logger wrapper for structured logging with extra data."""

    def __init__(self, logger: logging.Logger):
        """Initialize with a logger."""
        self.logger = logger

    def log(self, level: str, message: str, **extra_data: Any) -> None:
        """Log with structured extra data."""
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra={"extra_data": extra_data})

    def debug(self, message: str, **extra_data: Any) -> None:
        """Log debug with extra data."""
        self.log("debug", message, **extra_data)

    def info(self, message: str, **extra_data: Any) -> None:
        """Log info with extra data."""
        self.log("info", message, **extra_data)

    def warning(self, message: str, **extra_data: Any) -> None:
        """Log warning with extra data."""
        self.log("warning", message, **extra_data)

    def error(self, message: str, **extra_data: Any) -> None:
        """Log error with extra data."""
        self.log("error", message, **extra_data)
