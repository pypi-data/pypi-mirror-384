from dataclasses import dataclass
from enum import Enum
from typing import Any

from rich.console import RenderableType
from rich.live import Live
from rich.table import Table
from rich.text import Text

from ..core.console import get_console
from ..core.theme import get_theme


class StepStatus(Enum):
    """Step status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    """Individual step in a stepper."""

    name: str
    description: str | None = None
    status: StepStatus = StepStatus.PENDING


class Stepper:
    """Step tracking component with status indicators."""

    def __init__(
        self,
        title: str | None = None,
        show_numbers: bool = True,
        show_description: bool = True,
        live: bool = False,
    ):
        """Create a stepper."""
        self.title = title
        self.show_numbers = show_numbers
        self.show_description = show_description
        self.live_mode = live
        self.theme = get_theme()
        self.console = get_console()
        self._steps: list[Step] = []
        self._current_index: int = -1
        self._live: Live | None = None

    def add_step(self, name: str, description: str | None = None) -> int:
        """Add a step to the stepper."""
        step = Step(name, description)
        self._steps.append(step)
        return len(self._steps) - 1

    def add_steps(self, steps: list[str]) -> None:
        """Add multiple steps at once."""
        for step in steps:
            if isinstance(step, str):
                self.add_step(step)
            elif isinstance(step, tuple):
                self.add_step(step[0], step[1] if len(step) > 1 else None)

    def start(self, index: int) -> None:
        """Start a step."""
        if 0 <= index < len(self._steps):
            self._steps[index].status = StepStatus.RUNNING
            self._current_index = index
            self._update_display()

    def complete(self, index: int) -> None:
        """Mark a step as complete."""
        if 0 <= index < len(self._steps):
            self._steps[index].status = StepStatus.DONE
            self._update_display()

    def fail(self, index: int, error: str | None = None) -> None:
        """Mark a step as failed."""
        if 0 <= index < len(self._steps):
            self._steps[index].status = StepStatus.FAILED
            if error and self._steps[index].description:
                self._steps[index].description = f"{self._steps[index].description}\n{error}"
            elif error:
                self._steps[index].description = error
            self._update_display()

    def skip(self, index: int) -> None:
        """Mark a step as skipped."""
        if 0 <= index < len(self._steps):
            self._steps[index].status = StepStatus.SKIPPED
            self._update_display()

    def next(self) -> int | None:
        """Move to and start the next pending step."""
        # Complete current step if running
        if (
            self._current_index >= 0
            and self._steps[self._current_index].status == StepStatus.RUNNING
        ):
            self.complete(self._current_index)

        # Find next pending step
        for i in range(self._current_index + 1, len(self._steps)):
            if self._steps[i].status == StepStatus.PENDING:
                self.start(i)
                return i

        return None

    def _update_display(self) -> None:
        """Update the live display if enabled."""
        if self.live_mode and self._live and self._live.is_started:
            self._live.update(self.__rich__())

    def __enter__(self) -> "Stepper":
        """Start live display."""
        if self.live_mode:
            self._live = Live(
                self.__rich__(),
                console=self.console,
                refresh_per_second=4,
            )
            self._live.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop live display."""
        if self._live:
            self._live.stop()
            # Show final state
            self.console.print(self.__rich__())

    def __rich__(self) -> RenderableType:
        """Render the stepper as a Rich renderable."""
        if not self._steps:
            return Text("(no steps)", style=self.theme.get_style("muted"))

        # Create table for steps
        table = Table(
            show_header=False,
            show_edge=False,
            show_lines=False,
            box=None,
            padding=(0, 1),
            title=self.title,
        )

        # Add columns
        if self.show_numbers:
            table.add_column("Num", width=3, no_wrap=True)
        table.add_column("Status", width=3, no_wrap=True)
        table.add_column("Step")

        # Status glyphs and colors
        status_config = {
            StepStatus.PENDING: (self.theme.glyphs["pending"], self.theme.get_style("muted")),
            StepStatus.RUNNING: (self.theme.glyphs["running"], self.theme.get_style("warning")),
            StepStatus.DONE: (self.theme.glyphs["complete"], self.theme.get_style("success")),
            StepStatus.FAILED: (self.theme.glyphs["failed"], self.theme.get_style("error")),
            StepStatus.SKIPPED: (self.theme.glyphs["skipped"], self.theme.get_style("muted")),
        }

        # Add rows
        for i, step in enumerate(self._steps, 1):
            glyph, style = status_config[step.status]

            # Build row
            row = []

            if self.show_numbers:
                row.append(Text(f"{i}.", style=style))

            row.append(Text(glyph, style=style))

            # Step name and description
            if self.show_description and step.description:
                step_text = Text()
                step_text.append(step.name, style=style)
                step_text.append("\n")
                step_text.append(step.description, style=self.theme.get_style("muted"))
                row.append(step_text)
            else:
                row.append(Text(step.name, style=style))

            table.add_row(*row)

        return table

    @classmethod
    def from_list(cls, steps: list[str], **kwargs: Any) -> "Stepper":
        """Create a stepper from a list of step names."""
        stepper = cls(**kwargs)
        stepper.add_steps(steps)
        return stepper
