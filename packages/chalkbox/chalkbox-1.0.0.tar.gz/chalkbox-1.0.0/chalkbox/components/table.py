from typing import Any, Literal

from rich.console import RenderableType
from rich.table import Table as RichTable

from ..core.theme import get_theme


class Table:
    """Enhanced table with auto-sizing and smart features."""

    def __init__(
        self,
        title: str | None = None,
        headers: list[str] | None = None,
        show_header: bool = True,
        show_lines: bool = False,
        row_styles: Literal["none", "alternate", "severity"] = "none",
        truncation: Literal["ellipsis", "wrap", "clip"] = "ellipsis",
        max_width: int | None = None,
        expand: bool = False,
        border_style: str | None = None,
    ):
        """Create a table."""
        self.title = title
        self.headers = headers or []
        self.show_header = show_header
        self.show_lines = show_lines
        self.row_styles = row_styles
        self.truncation = truncation
        self.max_width = max_width
        self.expand = expand
        self.border_style = border_style
        self.theme = get_theme()
        self._rows: list[list[Any]] = []
        self._row_severities: list[str | None] = []

    def add_column(self, header: str, **kwargs: Any) -> None:
        """Add a column to the table."""
        self.headers.append(header)

    def add_row(self, *values: Any, severity: str | None = None) -> None:
        """Add a row to the table."""
        cleaned_values = []
        for v in values:
            if isinstance(v, str):
                # Strip whitespace
                v = v.strip()
                # U+FE0E (text) and U+FE0F (emoji) variation selectors
                v = v.replace("\uFE0E", "").replace("\uFE0F", "")
                cleaned_values.append(v)
            else:
                cleaned_values.append(v)
        self._rows.append(cleaned_values)
        self._row_severities.append(severity)

    def add_rows(self, rows: list[list[Any]]) -> None:
        """Add multiple rows at once."""
        for row in rows:
            self.add_row(*row)

    def __rich__(self) -> RenderableType:
        """Render the table as a Rich renderable."""
        table = RichTable(
            title=self.title,
            show_header=self.show_header,
            show_lines=self.show_lines,
            expand=self.expand,
            border_style=self.border_style or self.theme.get_style("primary"),
        )

        # Add columns - let Rich handle everything
        for header in self.headers:
            # Only set overflow if not default
            col_kwargs: dict[str, Any] = {}
            if self.truncation != "ellipsis":
                overflow = {
                    "wrap": "fold",
                    "clip": "crop",
                }.get(self.truncation, "ellipsis")
                col_kwargs["overflow"] = overflow

            if self.max_width:
                col_kwargs["max_width"] = self.max_width

            table.add_column(header, **col_kwargs)

        # Add rows with styling
        for i, (row, severity) in enumerate(zip(self._rows, self._row_severities, strict=False)):
            # Determine row style
            style = None

            if severity and self.row_styles == "severity":
                style = self.theme.get_style(severity)
            elif self.row_styles == "alternate" and i % 2 == 1:
                style = self.theme.get_style("muted")

            # Pass values directly to Rich - no custom processing
            # Rich handles Unicode, emoji, and width calculations correctly
            if style:
                # Apply style if needed
                table.add_row(*row, style=style)
            else:
                table.add_row(*row)

        return table

    @classmethod
    def from_dict(cls, data: dict[str, Any], title: str | None = None, **kwargs: Any) -> "Table":
        """Create a table from a dictionary."""
        table = cls(title=title, headers=["Key", "Value"], **kwargs)

        for key, value in data.items():
            table.add_row(key, str(value))

        return table

    @classmethod
    def from_list_of_dicts(
        cls, data: list[dict[str, Any]], title: str | None = None, **kwargs: Any
    ) -> "Table":
        """Create a table from a list of dictionaries."""
        if not data:
            return cls(title=title, **kwargs)

        headers = list(data[0].keys())

        table = cls(title=title, headers=headers, **kwargs)

        # Add rows (values will be stripped in add_row)
        for item in data:
            row = [str(item.get(key, "")) for key in headers]
            table.add_row(*row)

        return table

    def live(
        self,
        update_fn: Any | None = None,
        refresh_per_second: float = 2,
        screen: bool = False,
    ) -> Any:
        """
        Return a live-updating version of this table.

        The table will automatically respond to terminal resize events
        and can optionally update its content via update_fn.

        Example:
            table = Table(headers=["Name", "Status"])
            table.add_row("Server", "Running")

            with table.live():
                time.sleep(10)  # Table stays visible and responsive to resize
        """
        from ..live.wrapper import LiveComponent

        return LiveComponent(
            component=self,
            update_fn=update_fn,
            refresh_per_second=refresh_per_second,
            screen=screen,
        )
