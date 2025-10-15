from typing import Any, Literal

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from ..core.console import get_console
from ..core.theme import get_theme


class Section:
    """Section/panel component with consistent styling."""

    def __init__(
        self,
        title: str,
        subtitle: str | None = None,
        footer: str | None = None,
        padding: int | tuple | None = None,
        expand: bool = False,
        border_style: str | None = None,
        title_align: Literal["left", "center", "right"] = "left",
        subtitle_align: Literal["left", "center", "right"] = "right",
    ):
        """Create a section."""
        self.title = title
        self.subtitle = subtitle
        self.footer = footer
        self.padding = padding
        self.expand = expand
        self.border_style = border_style
        self.title_align = title_align
        self.subtitle_align = subtitle_align
        self.theme = get_theme()
        self.console = get_console()
        self._content: list[RenderableType] = []

    def __enter__(self) -> "Section":
        """Enter context for building section content."""
        self._content = []
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and render section."""
        if self._content:
            self.console.print(self.__rich__())

    def add(self, content: RenderableType) -> None:
        """Add content to the section."""
        self._content.append(content)

    def add_text(self, text: str, style: str | None = None) -> None:
        """Add styled text to the section."""
        self._content.append(Text(text, style=style or ""))

    def add_spacing(self, lines: int = 1) -> None:
        """Add vertical spacing."""
        for _ in range(lines):
            self._content.append("")

    def __rich__(self) -> RenderableType:
        """Render the section as a Rich renderable."""
        # Determine padding
        padding: int | tuple[int, int]
        if self.padding is None:
            padding = (self.theme.spacing["sm"], self.theme.spacing["default"])
        elif isinstance(self.padding, int):
            padding = self.padding
        else:
            padding = self.padding

        # Build content
        if self._content:
            content = self._content[0] if len(self._content) == 1 else Group(*self._content)
        else:
            content = Text("(empty section)", style=self.theme.get_style("muted"))

        # Build title with optional subtitle
        title = f"{self.title}\n[dim]{self.subtitle}[/dim]" if self.subtitle else self.title

        # Determine border style
        border_style = self.border_style or self.theme.get_style("primary")

        # Create panel
        return Panel(
            content,
            title=title,
            title_align=self.title_align,
            subtitle=self.footer,
            subtitle_align=self.subtitle_align,
            border_style=border_style,
            padding=padding,
            expand=self.expand,
        )

    @classmethod
    def create_collapsible(
        cls, title: str, content: RenderableType, collapsed: bool = False, **kwargs: Any
    ) -> "Section":
        """Create a collapsible section."""
        theme = get_theme()

        # Add collapse indicator to title
        indicator = "▼" if not collapsed else "▶"
        full_title = f"{indicator} {title}"

        section = cls(full_title, **kwargs)

        if not collapsed:
            section.add(content)
        else:
            section.add_text("(collapsed)", style=theme.get_style("muted"))

        return section
