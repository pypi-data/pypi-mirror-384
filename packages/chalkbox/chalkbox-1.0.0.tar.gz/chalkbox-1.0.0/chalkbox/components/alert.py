from typing import Any, Literal

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from ..core.theme import get_theme

AlertLevel = Literal["debug", "info", "success", "warning", "error", "critical"]


class Alert:
    """Alert/callout component with severity levels."""

    def __init__(
        self,
        message: str,
        level: AlertLevel = "info",
        title: str | None = None,
        details: str | None = None,
        border_style: str | None = None,
        title_align: Literal["left", "center", "right"] = "left",
        padding: tuple[int, int] | int = (0, 1),
    ):
        """Create an alert."""
        self.message = message
        self.level = level
        self.title = title
        self.details = details
        self.border_style = border_style
        self.title_align = title_align
        self.padding = padding
        self.theme = get_theme()

    def __rich__(self) -> RenderableType:
        """Render the alert as a Rich renderable."""
        glyph = self.theme.glyphs.get(self.level, self.theme.glyphs["info"])
        color = self.theme.get_style(self.level)

        # Build content
        content_parts = []

        # Main message with icon (single space between glyph and message)
        main_text = Text(f"{glyph} {self.message}", style=color)
        content_parts.append(main_text)

        # Add details if provided (directly below main message, no blank line)
        if self.details:
            details_text = Text(self.details, style=self.theme.get_style("muted"))
            content_parts.append(details_text)

        # Combine content
        content: RenderableType = (
            Group(*content_parts) if len(content_parts) > 1 else content_parts[0]
        )

        # Determine title
        if self.title:
            panel_title = self.title
        else:
            # Default titles based on level
            default_titles = {
                "debug": "Debug",
                "info": "Info",
                "success": "Success",
                "warning": "Warning",
                "error": "Error",
                "critical": "Critical",
            }
            panel_title = default_titles.get(self.level, "Alert")

        # Create panel with themed border
        border_style = self.border_style or color

        return Panel(
            content,
            title=panel_title,
            title_align=self.title_align,
            border_style=border_style,
            padding=self.padding,
        )

    @classmethod
    def info(cls, message: str, **kwargs: Any) -> "Alert":
        """Create an info alert."""
        return cls(message, level="info", **kwargs)

    @classmethod
    def success(cls, message: str, **kwargs: Any) -> "Alert":
        """Create a success alert."""
        return cls(message, level="success", **kwargs)

    @classmethod
    def warning(cls, message: str, **kwargs: Any) -> "Alert":
        """Create a warning alert."""
        return cls(message, level="warning", **kwargs)

    @classmethod
    def error(cls, message: str, **kwargs: Any) -> "Alert":
        """Create an error alert."""
        return cls(message, level="error", **kwargs)

    @classmethod
    def debug(cls, message: str, **kwargs: Any) -> "Alert":
        """Create a debug alert."""
        return cls(message, level="debug", **kwargs)

    @classmethod
    def critical(cls, message: str, **kwargs: Any) -> "Alert":
        """Create a critical alert."""
        return cls(message, level="critical", **kwargs)
