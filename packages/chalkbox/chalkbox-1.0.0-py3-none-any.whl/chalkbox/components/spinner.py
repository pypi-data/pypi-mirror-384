from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console as RichConsole
from rich.live import Live
from rich.spinner import Spinner as RichSpinner
from rich.text import Text

from ..core.console import get_console
from ..core.theme import get_theme


class Spinner:
    """Context-managed spinner with success/fail states."""

    def __init__(
        self,
        text: str = "Loading...",
        spinner: str = "dots",
        console: RichConsole | None = None,
        transient: bool = True,
        refresh_per_second: float = 10,
    ):
        """Initialize spinner."""
        self.text = text
        self.spinner_style = spinner
        self.console = console or get_console()
        self.transient = transient
        self.refresh_per_second = refresh_per_second
        self.theme = get_theme()
        self._status: Text | None = None
        self._live: Live | None = None

    def __enter__(self) -> "Spinner":
        """Start the spinner."""
        spinner = RichSpinner(self.spinner_style, text=self.text)
        self._live = Live(
            spinner,
            console=self.console,
            transient=self.transient,
            refresh_per_second=self.refresh_per_second,
        )
        self._live.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the spinner."""
        if self._live:
            self._live.stop()

            # Show final status if not transient
            if not self.transient and self._status:
                self.console.print(self._status)

    def update(self, text: str) -> None:
        """Update spinner text."""
        if self._live and self._live.is_started:
            spinner = RichSpinner(self.spinner_style, text=text)
            self._live.update(spinner)
            self.text = text

    def success(self, text: str | None = None) -> None:
        """Mark spinner as successful."""
        if text is None:
            text = self.text

        glyph = self.theme.glyphs["success"]
        color = self.theme.get_style("success")

        self._status = Text(f"{glyph} {text}", style=color)

        if self._live and self._live.is_started:
            self._live.update(self._status)

    def error(self, text: str | None = None) -> None:
        """Mark spinner as failed."""
        if text is None:
            text = f"Failed: {self.text}"

        glyph = self.theme.glyphs["error"]
        color = self.theme.get_style("error")

        self._status = Text(f"{glyph} {text}", style=color)

        if self._live and self._live.is_started:
            self._live.update(self._status)

    def warning(self, text: str | None = None) -> None:
        """Mark spinner with warning."""
        if text is None:
            text = self.text

        glyph = self.theme.glyphs["warning"]
        color = self.theme.get_style("warning")

        self._status = Text(f"{glyph} {text}", style=color)

        if self._live and self._live.is_started:
            self._live.update(self._status)


@contextmanager
def spinner(text: str = "Loading...", **kwargs: Any) -> Generator[Spinner, None, None]:
    """
    Convenience context manager for spinners.

    Example:
        with spinner("Processing data...") as sp:
            # do work
            sp.success("Data processed!")
    """
    sp = Spinner(text, **kwargs)
    with sp:
        yield sp
