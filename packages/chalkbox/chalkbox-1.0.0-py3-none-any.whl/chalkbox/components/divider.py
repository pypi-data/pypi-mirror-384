from typing import Any, Literal

from rich.console import RenderableType
from rich.rule import Rule

from ..core.console import get_console
from ..core.theme import get_theme


class Divider:
    """Themed horizontal rule for visual separation."""

    def __init__(
        self,
        title: str = "",
        align: Literal["left", "center", "right"] = "center",
        style: str | None = None,
        characters: str = "─",
    ):
        """Create a divider."""
        self.title = title
        self.align = align
        self.custom_style = style
        self.characters = characters
        self.theme = get_theme()
        self.console = get_console()

    def __rich__(self) -> RenderableType:
        """Render the divider as a Rich renderable."""
        style = self.custom_style or self.theme.get_style("primary")

        # Only pass title if it is not empty
        if self.title:
            return Rule(
                title=self.title,
                characters=self.characters,
                style=style,
                align=self.align,
            )
        else:
            return Rule(
                characters=self.characters,
                style=style,
                align=self.align,
            )

    def print(self) -> None:
        """Print the divider to console."""
        self.console.print(self.__rich__())

    @classmethod
    def section(cls, title: str, **kwargs: Any) -> "Divider":
        """Create a divider for a section heading."""
        return cls(title=title, align="left", **kwargs)

    @classmethod
    def separator(cls, **kwargs: Any) -> "Divider":
        """Create a simple separator without title."""
        return cls(title="", **kwargs)

    @classmethod
    def double(cls, title: str = "", **kwargs: Any) -> "Divider":
        """Create a divider with double-line characters."""
        return cls(title=title, characters="═", **kwargs)

    @classmethod
    def heavy(cls, title: str = "", **kwargs: Any) -> "Divider":
        """Create a divider with heavy characters."""
        return cls(title=title, characters="━", **kwargs)

    @classmethod
    def light(cls, title: str = "", **kwargs: Any) -> "Divider":
        """Create a divider with light characters."""
        return cls(title=title, characters="─", **kwargs)

    @classmethod
    def dotted(cls, title: str = "", **kwargs: Any) -> "Divider":
        """Create a divider with dotted characters."""
        return cls(title=title, characters="·", **kwargs)

    @classmethod
    def dashed(cls, title: str = "", **kwargs: Any) -> "Divider":
        """Create a divider with dashed characters."""
        return cls(title=title, characters="╌", **kwargs)
