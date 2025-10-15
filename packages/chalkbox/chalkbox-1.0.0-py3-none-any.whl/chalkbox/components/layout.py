from typing import Any, Literal

from rich.console import RenderableType
from rich.layout import Layout as RichLayout

from ..core.console import get_console
from ..core.theme import get_theme


class MultiPanel:
    """
    Themed multi-panel layout for dashboard-like displays.

    Provides a wrapper around Rich's Layout for creating complex
    multi-panel layouts with sections, splits, and nested panels.
    """

    def __init__(
        self,
        name: str = "root",
        size: int | None = None,
        minimum_size: int = 1,
        ratio: int = 1,
        visible: bool = True,
    ):
        """Create a multi-panel layout."""
        self.name = name
        self.console = get_console()
        self.theme = get_theme()

        # Create Rich Layout
        self._layout = RichLayout(
            name=name,
            size=size,
            minimum_size=minimum_size,
            ratio=ratio,
            visible=visible,
        )

    def split(
        self,
        *layouts: "MultiPanel",
        direction: Literal["vertical", "horizontal"] = "vertical",
    ) -> None:
        """Split this panel into multiple sections."""
        # Convert MultiPanel objects to Rich Layout objects
        rich_layouts = [layout._layout for layout in layouts]

        if direction == "vertical":
            self._layout.split_column(*rich_layouts)
        elif direction == "horizontal":
            self._layout.split_row(*rich_layouts)
        else:
            # Fail-safe: default to vertical
            self._layout.split_column(*rich_layouts)

    def split_row(self, *layouts: "MultiPanel") -> None:
        """Split into horizontal panels (left-to-right)."""
        self.split(*layouts, direction="horizontal")

    def split_column(self, *layouts: "MultiPanel") -> None:
        """Split into vertical panels (top-to-bottom)."""
        self.split(*layouts, direction="vertical")

    def update(self, renderable: RenderableType) -> None:
        """Update panel content."""
        self._layout.update(renderable)

    def __getitem__(self, name: str) -> "MultiPanel":
        """Get a child panel by name."""
        rich_layout = self._layout[name]

        # Wrap in MultiPanel
        panel = MultiPanel.__new__(MultiPanel)
        panel.name = name
        panel.console = self.console
        panel.theme = self.theme
        panel._layout = rich_layout

        return panel

    def __rich__(self) -> RenderableType:
        """Render the layout as a Rich renderable."""
        return self._layout

    def print(self) -> None:
        """Print the layout to console."""
        self.console.print(self.__rich__())

    @classmethod
    def create_sidebar(
        cls,
        sidebar_content: RenderableType,
        main_content: RenderableType,
        sidebar_width: int = 30,
        sidebar_position: Literal["left", "right"] = "left",
    ) -> "MultiPanel":
        """Create a layout with sidebar."""
        root = cls()

        sidebar = MultiPanel("sidebar", size=sidebar_width)
        sidebar.update(sidebar_content)

        main = MultiPanel("main")
        main.update(main_content)

        if sidebar_position == "left":
            root.split_row(sidebar, main)
        else:
            root.split_row(main, sidebar)

        return root

    @classmethod
    def create_header_footer(
        cls,
        header_content: RenderableType,
        main_content: RenderableType,
        footer_content: RenderableType,
        header_size: int = 3,
        footer_size: int = 3,
    ) -> "MultiPanel":
        """Create a layout with header and footer."""
        root = cls()

        header = MultiPanel("header", size=header_size)
        header.update(header_content)

        main = MultiPanel("main")
        main.update(main_content)

        footer = MultiPanel("footer", size=footer_size)
        footer.update(footer_content)

        root.split_column(header, main, footer)

        return root

    @classmethod
    def create_grid(
        cls,
        panels: dict[str, RenderableType],
        rows: int = 2,
        cols: int = 2,
    ) -> "MultiPanel":
        """Create a grid layout."""
        root = cls()

        # Create row panels
        row_panels = []
        panel_items = list(panels.items())

        for row in range(rows):
            row_panel = MultiPanel(f"row_{row}")
            col_panels = []

            for col in range(cols):
                idx = row * cols + col
                if idx < len(panel_items):
                    name, content = panel_items[idx]
                    col_panel = MultiPanel(name)
                    col_panel.update(content)
                    col_panels.append(col_panel)

            if col_panels:
                row_panel.split_row(*col_panels)
                row_panels.append(row_panel)

        if row_panels:
            root.split_column(*row_panels)

        return root

    @classmethod
    def create_dashboard(
        cls,
        header: RenderableType,
        sidebar: RenderableType,
        main: RenderableType,
        footer: RenderableType | None = None,
        header_size: int = 3,
        sidebar_width: int = 25,
        footer_size: int = 3,
    ) -> "MultiPanel":
        """Create a dashboard layout with header, sidebar, main, and optional footer."""
        root = cls()

        # Create header
        header_panel = MultiPanel("header", size=header_size)
        header_panel.update(header)

        # Create middle section (sidebar + main)
        middle = MultiPanel("middle")

        sidebar_panel = MultiPanel("sidebar", size=sidebar_width)
        sidebar_panel.update(sidebar)

        main_panel = MultiPanel("main")
        main_panel.update(main)

        middle.split_row(sidebar_panel, main_panel)

        # Create layout
        if footer is not None:
            footer_panel = MultiPanel("footer", size=footer_size)
            footer_panel.update(footer)
            root.split_column(header_panel, middle, footer_panel)
        else:
            root.split_column(header_panel, middle)

        return root

    def update_panel(self, name: str, content: RenderableType) -> None:
        """
        Update a named panels content.

        Convenience method for updating panels by name without needing
        to use the bracket notation.

        Example:
            layout = MultiPanel.create_dashboard(header, sidebar, main)
            layout.update_panel("main", new_table)
        """
        self[name].update(content)

    def live(
        self,
        update_fn: Any | None = None,
        refresh_per_second: float = 2,
        screen: bool = True,
    ) -> Any:
        """
        Return a live-updating version of this layout.

        The layout will automatically respond to terminal resize events
        and can optionally update its content via update_fn.

        Example:
            layout = MultiPanel.create_dashboard(header, sidebar, main, footer)

            with layout.live():
                time.sleep(10)  # Layout stays visible and responsive to resize
        """
        from ..live.wrapper import LiveComponent

        return LiveComponent(
            component=self,
            update_fn=update_fn,
            refresh_per_second=refresh_per_second,
            screen=screen,
        )
