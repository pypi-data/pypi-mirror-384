from typing import Any

from rich.console import Console as RichConsole


class Console(RichConsole):
    """Extended Rich Console with ChalkBox enhancements."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize console with ChalkBox defaults."""
        kwargs.setdefault("highlight", False)
        super().__init__(*args, **kwargs)


_console: Console | None = None


def get_console(**kwargs: Any) -> Console:
    """
    Get the singleton console instance.

    Creates a new console on first call with provided kwargs.
    Subsequent calls return the same instance (kwargs ignored).
    """
    global _console
    if _console is None:
        _console = Console(**kwargs)
    return _console


def reset_console() -> None:
    """Reset the console singleton (mainly for testing)."""
    global _console
    _console = None
