# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 Matthew Watkins <mwatkins@linuxfoundation.org>

"""Logging helpers.

Phase 1 (Minimal Cleanup):
- Restored minimal GerritRichHandler and setup_logging ONLY to satisfy existing tests.
- Removed unused progress-aware and styled helper functions from earlier design.
- File-based logging continues to live in file_logging.py.
"""

from __future__ import annotations

import inspect
import logging
from contextlib import contextmanager
from typing import Any, Iterator

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


# Minimal theme (can be expanded later if reused elsewhere)
GERRIT_THEME = Theme(
    {
        "info": "cyan",
        "warning": "magenta",
        "error": "bold red",
        "critical": "bold white on red",
        "success": "green",
    }
)


class GerritRichHandler(RichHandler):
    """Thin wrapper around RichHandler retained for backward compatibility with tests."""

    def __init__(self, console: Console | None = None, **kwargs: Any) -> None:
        if console is None:
            console = Console(theme=GERRIT_THEME, stderr=True)
        # Pass through kwargs so tests using show_time/show_level etc. keep working
        super().__init__(console=console, **kwargs)


def setup_logging(
    level: str = "INFO",
    quiet: bool = False,
    verbose: bool = False,
    console: Console | None = None,
) -> logging.Logger:
    """Minimal logging setup compatible with existing tests.

    Args:
        level: Base log level (ignored if quiet/verbose override it)
        quiet: If True, only errors and above
        verbose: If True, debug logging enabled
        console: Optional Rich Console to direct output to
    """
    if quiet:
        effective_level = logging.ERROR
    elif verbose:
        effective_level = logging.DEBUG
    else:
        effective_level = getattr(logging, level.upper(), logging.INFO)

    if console is None:
        console = Console(theme=GERRIT_THEME, stderr=True)

    root = logging.getLogger()
    root.setLevel(effective_level)

    # Clear existing handlers to avoid duplicates in tests
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = GerritRichHandler(
        console=console,
        show_time=False,  # Keep output compact for tests
        show_level=True,
        show_path=False,
        markup=True,
        rich_tracebacks=verbose,
        tracebacks_show_locals=verbose,
    )
    handler.setLevel(effective_level)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root.addHandler(handler)

    # Suppress noisy third-party modules unless verbose
    if not verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

    return logging.getLogger("gerrit_clone")


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger for the caller (or provided name).

    Falls back to 'gerrit_clone' when the caller cannot be determined.
    """
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_name = frame.f_back.f_globals.get("__name__", "gerrit_clone")
        else:
            caller_name = "gerrit_clone"
        name = caller_name

    return logging.getLogger(name)


class _SuppressConsoleFilter(logging.Filter):
    """Thread-safe filter to suppress console output during Rich display.

    This filter blocks all log records when suppression is active.
    It's designed to be added/removed from handlers in a thread-safe manner.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Block all records when this filter is active."""
        return False


@contextmanager
def suppress_console_logging(verbose: bool = False) -> Iterator[None]:
    """Context manager to temporarily suppress console logging handlers.

    This is used during Rich Live display to prevent log messages from
    interfering with the progress display. File logging continues normally.

    Uses a logging.Filter approach which is thread-safe and doesn't mutate
    handler state directly.

    Args:
        verbose: If True, don't suppress logging (useful for debugging)

    Yields:
        None
    """
    # In verbose mode, don't suppress logging - users want to see everything
    if verbose:
        yield
        return

    root = logging.getLogger()

    # Find all RichHandler instances
    rich_handlers = [h for h in root.handlers if isinstance(h, RichHandler)]

    # Create a single filter instance to share across handlers
    suppress_filter = _SuppressConsoleFilter()

    # Add filter to all RichHandler instances
    for handler in rich_handlers:
        handler.addFilter(suppress_filter)

    try:
        yield
    finally:
        # Remove filter from all handlers
        for handler in rich_handlers:
            handler.removeFilter(suppress_filter)
