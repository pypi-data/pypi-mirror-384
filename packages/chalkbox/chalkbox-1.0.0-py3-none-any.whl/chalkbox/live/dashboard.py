from collections.abc import Callable
from typing import Literal

from rich.console import RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from ..core.console import get_console
from .wrapper import LiveComponent

DashboardLayout = Literal["default", "sidebar_left", "sidebar_right", "header_footer", "full"]


class DashboardSection:
    """Represents a section in a dashboard that can be updated."""

    def __init__(self, name: str, content: RenderableType | None = None):
        """Initialize a dashboard section."""
        self.name = name
        self.content = content or Text("(empty)", style="dim")

    def update(self, content: RenderableType) -> None:
        """Update section content."""
        self.content = content


class Dashboard:
    """
    High-level dashboard builder with live updates and responsive layouts.

    Provides common dashboard patterns with automatic live updates.
    """

    def __init__(self, layout_type: DashboardLayout = "default"):
        """Initialize dashboard."""
        self.layout_type = layout_type
        self.console = get_console()

        self.sections: dict[str, DashboardSection] = {}
        self.update_functions: dict[str, Callable] = {}

        self._init_sections()

    def _init_sections(self) -> None:
        """Initialize sections based on layout type."""
        if self.layout_type in ["default", "sidebar_left", "sidebar_right", "full"]:
            self.sections["header"] = DashboardSection("header")
            self.sections["sidebar"] = DashboardSection("sidebar")
            self.sections["main"] = DashboardSection("main")
            self.sections["footer"] = DashboardSection("footer")
        elif self.layout_type == "header_footer":
            self.sections["header"] = DashboardSection("header")
            self.sections["main"] = DashboardSection("main")
            self.sections["footer"] = DashboardSection("footer")

    def set_header(
        self,
        content: RenderableType | str,
        update_fn: Callable[[], RenderableType] | None = None,
    ) -> None:
        """Set header content."""
        if isinstance(content, str):
            content = Panel(content, border_style="cyan")

        self.sections["header"].content = content

        if update_fn:
            self.update_functions["header"] = update_fn

    def set_sidebar(
        self,
        content: RenderableType,
        update_fn: Callable[[], RenderableType] | None = None,
    ) -> None:
        """Set sidebar content."""
        if "sidebar" not in self.sections:
            raise ValueError(f"Sidebar not available in {self.layout_type} layout")

        self.sections["sidebar"].content = content

        if update_fn:
            self.update_functions["sidebar"] = update_fn

    def set_main(
        self,
        content: RenderableType | None = None,
        update_fn: Callable[[], RenderableType] | None = None,
    ) -> None:
        """Set main content area."""
        if content is not None:
            self.sections["main"].content = content

        if update_fn:
            self.update_functions["main"] = update_fn

    def set_footer(
        self,
        content: RenderableType | str,
        update_fn: Callable[[], RenderableType] | None = None,
    ) -> None:
        """Set footer content."""
        if isinstance(content, str):
            content = Panel(content, border_style="blue")

        if "footer" not in self.sections:
            raise ValueError(f"Footer not available in {self.layout_type} layout")

        self.sections["footer"].content = content

        if update_fn:
            self.update_functions["footer"] = update_fn

    def _build_layout(self) -> Layout:
        """Build the Rich Layout based on configured sections."""
        for section_name, update_fn in self.update_functions.items():
            if section_name in self.sections:
                new_content = update_fn()
                self.sections[section_name].content = new_content

        layout = Layout()

        if self.layout_type == "default":
            # Simple main content only
            layout.update(self.sections["main"].content)

        elif self.layout_type == "sidebar_left":
            # Header / (Sidebar + Main) / Footer
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3),
            )

            layout["body"].split_row(
                Layout(name="sidebar", size=30),
                Layout(name="main"),
            )

            layout["header"].update(self.sections["header"].content)
            layout["body"]["sidebar"].update(self.sections["sidebar"].content)
            layout["body"]["main"].update(self.sections["main"].content)
            layout["footer"].update(self.sections["footer"].content)

        elif self.layout_type == "sidebar_right":
            # Same as sidebar_left but reversed
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3),
            )

            layout["body"].split_row(
                Layout(name="main"),
                Layout(name="sidebar", size=30),
            )

            layout["header"].update(self.sections["header"].content)
            layout["body"]["main"].update(self.sections["main"].content)
            layout["body"]["sidebar"].update(self.sections["sidebar"].content)
            layout["footer"].update(self.sections["footer"].content)

        elif self.layout_type == "header_footer":
            # Header / Main / Footer
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="footer", size=3),
            )

            layout["header"].update(self.sections["header"].content)
            layout["main"].update(self.sections["main"].content)
            layout["footer"].update(self.sections["footer"].content)

        elif self.layout_type == "full":
            # Full dashboard: Header / (Sidebar + Main) / Footer
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3),
            )

            layout["body"].split_row(
                Layout(name="sidebar", size=25),
                Layout(name="main"),
            )

            layout["header"].update(self.sections["header"].content)
            layout["body"]["sidebar"].update(self.sections["sidebar"].content)
            layout["body"]["main"].update(self.sections["main"].content)
            layout["footer"].update(self.sections["footer"].content)

        return layout

    def run(
        self,
        refresh_per_second: float = 2,
        duration: float | None = None,
    ) -> None:
        """Start the live dashboard display."""

        def update_dashboard() -> Layout:
            return self._build_layout()

        wrapper = LiveComponent(
            component=update_dashboard(),
            update_fn=update_dashboard,
            refresh_per_second=refresh_per_second,
            screen=True,
        )

        try:
            with wrapper:
                if duration:
                    import time

                    time.sleep(duration)
                else:
                    # Run indefinitely until Ctrl+C
                    import time

                    while True:
                        time.sleep(1)
        except KeyboardInterrupt:
            # Clean exit on Ctrl+C
            pass

    def run_once(self) -> None:
        """Render the dashboard once (non-live mode)."""
        layout = self._build_layout()
        self.console.print(layout)

    @classmethod
    def create(cls, layout: DashboardLayout = "default") -> "Dashboard":
        """Factory method to create a dashboard."""
        return cls(layout_type=layout)

    @classmethod
    def quick_monitor(
        cls,
        title: str,
        metrics_fn: Callable[[], RenderableType],
        sidebar_fn: Callable[[], RenderableType] | None = None,
        refresh_per_second: float = 2,
    ) -> None:
        """Quick monitoring dashboard."""
        dashboard = cls.create("sidebar_left" if sidebar_fn else "header_footer")

        dashboard.set_header(f"[bold cyan]{title}[/bold cyan]")
        dashboard.set_main(update_fn=metrics_fn)

        if sidebar_fn:
            dashboard.set_sidebar(Text(""), update_fn=sidebar_fn)

        from datetime import datetime

        def footer_fn() -> Panel:
            return Panel(
                f"[dim]Last updated: {datetime.now().strftime('%H:%M:%S')} | Press Ctrl+C to exit[/dim]",
                border_style="blue",
            )

        dashboard.set_footer(Text(""), update_fn=footer_fn)

        dashboard.run(refresh_per_second=refresh_per_second)
