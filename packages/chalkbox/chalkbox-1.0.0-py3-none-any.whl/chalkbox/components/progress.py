from typing import Any

from rich.progress import (
    BarColumn,
    DownloadColumn,
    MofNCompleteColumn,
    Progress as RichProgress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from ..core.console import get_console
from ..core.theme import get_theme


class Progress:
    """Enhanced progress bar with multitask support."""

    def __init__(
        self,
        console: Any | None = None,
        transient: bool = False,
        expand: bool = False,
        auto_refresh: bool = True,
    ):
        """Initialize progress bar."""
        self.console = console or get_console()
        self.theme = get_theme()
        self.transient = transient
        self.expand = expand
        self.auto_refresh = auto_refresh
        self._progress: RichProgress | None = None

    def __enter__(self) -> "Progress":
        """Start progress display."""
        # Create progress with themed columns
        self._progress = RichProgress(
            SpinnerColumn(style=self.theme.get_style("primary")),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(
                complete_style=self.theme.get_style("success"),
                finished_style=self.theme.get_style("success"),
            ),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=self.transient,
            expand=self.expand,
            auto_refresh=self.auto_refresh,
        )
        self._progress.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop progress display."""
        if self._progress:
            self._progress.stop()

    def add_task(self, description: str, total: float | None = None, **kwargs: Any) -> TaskID:
        """Add a new task to track."""
        if self._progress:
            return self._progress.add_task(description, total=total, **kwargs)
        raise RuntimeError("Progress not started (use context manager)")

    def update(
        self,
        task_id: TaskID,
        *,
        advance: float | None = None,
        completed: float | None = None,
        total: float | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Update task progress."""
        if self._progress:
            self._progress.update(
                task_id,
                advance=advance,
                completed=completed,
                total=total,
                description=description,
                **kwargs,
            )

    def remove_task(self, task_id: TaskID) -> None:
        """Remove a task from display."""
        if self._progress:
            self._progress.remove_task(task_id)

    @classmethod
    def create_simple(cls, description: str = "Processing...") -> "Progress":
        """Create a simple single-task progress bar."""
        return cls(transient=True)

    @classmethod
    def create_download(cls) -> "Progress":
        """Create a progress bar optimized for downloads."""
        console = get_console()
        theme = get_theme()

        progress = RichProgress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(
                complete_style=theme.get_style("success"),
                finished_style=theme.get_style("success"),
            ),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        )

        # Wrap in our Progress class
        wrapper = cls()
        wrapper._progress = progress
        return wrapper
