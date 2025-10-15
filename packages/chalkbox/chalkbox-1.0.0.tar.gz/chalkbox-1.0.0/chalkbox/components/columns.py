from typing import Any, Literal

from rich.columns import Columns as RichColumns
from rich.console import RenderableType

from ..core.console import get_console
from ..core.theme import get_theme


class ColumnLayout:
    """Themed multi-column layout for displaying items."""

    def __init__(
        self,
        items: list[Any] | None = None,
        equal: bool = False,
        expand: bool = False,
        width: int | None = None,
        column_first: bool = False,
        padding: tuple[int, int] = (0, 1),
        align: Literal["left", "center", "right"] = "left",
    ):
        """Create a column layout."""
        self.items = items or []
        self.equal = equal
        self.expand = expand
        self.width = width
        self.column_first = column_first
        self.padding = padding
        self.align = align
        self.console = get_console()
        self.theme = get_theme()

    def add(self, item: Any) -> None:
        """Add an item to the columns."""
        self.items.append(item)

    def add_many(self, items: list[Any]) -> None:
        """Add multiple items to the columns."""
        self.items.extend(items)

    def __rich__(self) -> RenderableType:
        """Render the columns as a Rich renderable."""
        if not self.items:
            from rich.text import Text

            return Text("(no items)", style=self.theme.get_style("muted"))

        return RichColumns(
            self.items,
            equal=self.equal,
            expand=self.expand,
            width=self.width,
            column_first=self.column_first,
            padding=self.padding,
            align=self.align,
        )

    def print(self) -> None:
        """Print the columns to console."""
        self.console.print(self.__rich__())

    @classmethod
    def from_list(
        cls,
        items: list[Any],
        equal: bool = False,
        **kwargs: Any,
    ) -> "ColumnLayout":
        """Create columns from a list of items."""
        return cls(items=items, equal=equal, **kwargs)

    @classmethod
    def from_strings(
        cls,
        strings: list[str],
        style: str | None = None,
        **kwargs: Any,
    ) -> "ColumnLayout":
        """Create columns from a list of strings with optional styling."""
        from rich.text import Text

        # Apply styling if provided
        items = [Text(s, style=style) for s in strings] if style else [Text(s) for s in strings]

        return cls(items=items, **kwargs)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        equal: bool = True,
        **kwargs: Any,
    ) -> "ColumnLayout":
        """Create columns from a dictionary (key-value pairs)."""
        from rich.text import Text

        items = []
        for key, value in data.items():
            text = Text()
            text.append(f"{key}: ", style="bold")
            text.append(str(value))
            items.append(text)

        return cls(items=items, equal=equal, **kwargs)

    @classmethod
    def grid(
        cls,
        items: list[Any],
        columns: int = 3,
        **kwargs: Any,
    ) -> "ColumnLayout":
        """Create a grid layout with fixed number of columns."""
        # Calculate equal width for grid
        return cls(items=items, equal=True, expand=True, **kwargs)
