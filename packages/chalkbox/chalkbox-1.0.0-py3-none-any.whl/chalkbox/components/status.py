from typing import Any

from rich.status import Status as RichStatus

from ..core.console import get_console
from ..core.theme import get_theme


class Status:
    """
    Themed status display with spinner.

    Unlike Spinner (which uses Live and blocks console), Status allows
    console output to continue while showing ongoing status.
    """

    def __init__(
        self,
        message: str = "Working...",
        spinner: str = "dots",
        spinner_style: str | None = None,
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ):
        """Initialize status display."""
        self.message = message
        self.spinner_name = spinner
        self.custom_spinner_style = spinner_style
        self.speed = speed
        self.refresh_per_second = refresh_per_second
        self.console = get_console()
        self.theme = get_theme()
        self._status: RichStatus | None = None

    def __enter__(self) -> "Status":
        """Start the status display."""
        # Apply themed styling
        spinner_style = self.custom_spinner_style or self.theme.get_style("primary")

        # Create Rich status
        self._status = self.console.status(
            self.message,
            spinner=self.spinner_name,
            spinner_style=spinner_style,
            speed=self.speed,
            refresh_per_second=self.refresh_per_second,
        )
        self._status.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the status display."""
        if self._status:
            self._status.__exit__(exc_type, exc_val, exc_tb)

    def update(
        self,
        message: str | None = None,
        spinner: str | None = None,
        spinner_style: str | None = None,
        speed: float | None = None,
    ) -> None:
        """Update status display."""
        if self._status:
            if message is not None:
                self._status.update(status=message)
            if spinner is not None:
                # Update spinner name only - Rich Status handles the spinner internally
                self.spinner_name = spinner
                if spinner_style is not None:
                    self.custom_spinner_style = spinner_style
            if speed is not None:
                self._status.update(speed=speed)

    def stop(self) -> None:
        """Stop the status display."""
        if self._status:
            self._status.stop()

    def start(self) -> None:
        """Start the status display."""
        if self._status:
            self._status.start()

    @classmethod
    def show(
        cls,
        message: str,
        spinner: str = "dots",
        **kwargs: Any,
    ) -> "Status":
        """Quick status display."""
        return cls(message=message, spinner=spinner, **kwargs)


# Convenience function for quick status display
def status(message: str, **kwargs: Any) -> Status:
    """
    Create a status display context manager.

    Example:
        with status("Processing data..."):
            # Your work here
            time.sleep(2)
    """
    return Status(message=message, **kwargs)
