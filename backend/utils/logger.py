"""
QueueMind — Logging Utilities
-------------------------------
Structured, colorized logging setup shared across all agents.
"""

import logging
import sys
from typing import Optional


# ANSI color codes
RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
GREY   = "\033[90m"


LEVEL_COLORS = {
    logging.DEBUG:    GREY,
    logging.INFO:     BLUE,
    logging.WARNING:  YELLOW,
    logging.ERROR:    RED,
    logging.CRITICAL: RED + BOLD,
}

LEVEL_ICONS = {
    logging.DEBUG:    "·",
    logging.INFO:     "ℹ",
    logging.WARNING:  "⚠",
    logging.ERROR:    "✗",
    logging.CRITICAL: "💀",
}


class ColorFormatter(logging.Formatter):
    """Pretty, color-coded log formatter for terminal output."""

    def format(self, record: logging.LogRecord) -> str:
        color = LEVEL_COLORS.get(record.levelno, RESET)
        icon  = LEVEL_ICONS.get(record.levelno, "·")

        time_str  = self.formatTime(record, "%H:%M:%S")
        level_str = f"{color}{icon} {record.levelname:<8}{RESET}"
        name_str  = f"{CYAN}{record.name:<26}{RESET}"
        msg_str   = f"{color if record.levelno >= logging.WARNING else ''}{record.getMessage()}{RESET}"

        if record.exc_info:
            msg_str += "\n" + self.formatException(record.exc_info)

        return f"{GREY}{time_str}{RESET}  {level_str}  {name_str}  {msg_str}"


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure root logging with color formatter.

    Args:
        level:    Minimum log level (default INFO).
        log_file: Optional path to write plain-text logs alongside terminal output.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    root.handlers.clear()

    # Console handler (colorized)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ColorFormatter())
    root.addHandler(console)

    # Optional file handler (plain text)
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(name)-26s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        root.addHandler(fh)

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "watchfiles.main", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper — use instead of logging.getLogger()."""
    return logging.getLogger(f"queuemind.{name}")
