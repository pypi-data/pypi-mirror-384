from collections.abc import Callable
from typing import Any

from rich.console import RenderableType
from rich.live import Live
from rich.text import Text

from ..core.console import get_console


class LiveComponent:
    """
    Make any ChalkBox component live and responsive to terminal resize.

    This wrapper takes any component that implements __rich__() and makes it
    update automatically, responding to terminal resize events.

    Example:
        table = Table(headers=["Name", "Status"])
        table.add_row("Server", "Running")

        with LiveComponent(table, update_fn=lambda: update_table(table)):
            time.sleep(10)  # Table updates automatically
    """

    def __init__(
        self,
        component: Any,
        update_fn: Callable[[], Any] | None = None,
        refresh_per_second: float = 2,
        screen: bool = False,
        transient: bool = False,
    ):
        """Initialize a live component wrapper."""
        self.component = component
        self.update_fn = update_fn
        self.refresh_per_second = refresh_per_second
        self.screen = screen
        self.transient = transient
        self.console = get_console()
        self._live: Live | None = None

    def __enter__(self) -> "LiveComponent":
        """Start the live display."""
        renderable = self._get_renderable()

        # Create and start Live display
        self._live = Live(
            renderable,
            console=self.console,
            refresh_per_second=self.refresh_per_second,
            screen=self.screen,
            transient=self.transient,
        )
        self._live.__enter__()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the live display."""
        if self._live:
            self._live.__exit__(exc_type, exc_val, exc_tb)

    def _get_renderable(self) -> RenderableType:
        """Get the current renderable from the component."""
        if self.update_fn:
            result = self.update_fn()
            if result is not None:
                self.component = result

        # Get renderable from component
        if hasattr(self.component, "__rich__"):
            renderable: RenderableType = self.component.__rich__()
            return renderable
        else:
            # Fallback to component itself (assume it's a valid renderable)
            return self.component  # type: ignore

    def update(self, component: Any | None = None) -> None:
        """Manually update the displayed component."""
        if component is not None:
            self.component = component

        if self._live and self._live.is_started:
            self._live.update(self._get_renderable())

    def refresh(self) -> None:
        """Force a refresh of the display."""
        self.update()

    @classmethod
    def wrap(
        cls,
        component: Any,
        **kwargs: Any,
    ) -> "LiveComponent":
        """Convenience factory for wrapping a component."""
        return cls(component, **kwargs)


class LiveTable:
    """Convenience wrapper for live-updating tables."""

    def __init__(
        self,
        table: Any | None = None,
        update_fn: Callable[[], Any] | None = None,
        refresh_per_second: float = 2,
        screen: bool = False,
    ):
        """Initialize a live table."""
        self.update_fn = update_fn
        self._wrapper = LiveComponent(
            component=table or self._create_empty_table(),
            update_fn=update_fn,
            refresh_per_second=refresh_per_second,
            screen=screen,
        )

    @staticmethod
    def _create_empty_table() -> Any:
        """Create an empty table as placeholder."""
        from ..components.table import Table

        return Table(headers=["Loading..."])

    def __enter__(self) -> "LiveTable":
        """Start the live display."""
        self._wrapper.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the live display."""
        self._wrapper.__exit__(exc_type, exc_val, exc_tb)

    def update(self, table: Any) -> None:
        """Update the displayed table."""
        self._wrapper.update(table)

    def refresh(self) -> None:
        """Force a refresh."""
        self._wrapper.refresh()


class LiveLayout:
    """
    Convenience wrapper for live-updating layouts/panels.

    Example:
        def build_layout():
            layout = MultiPanel.create_dashboard(header, sidebar, main, footer)
            return layout

        with LiveLayout(update_fn=build_layout):
            time.sleep(60)
    """

    def __init__(
        self,
        layout: Any | None = None,
        update_fn: Callable[[], Any] | None = None,
        refresh_per_second: float = 2,
        screen: bool = True,  # Layouts usually want fullscreen
    ):
        """Initialize a live layout."""
        self.update_fn = update_fn
        self._wrapper = LiveComponent(
            component=layout or Text("Loading..."),
            update_fn=update_fn,
            refresh_per_second=refresh_per_second,
            screen=screen,
        )

    def __enter__(self) -> "LiveLayout":
        """Start the live display."""
        self._wrapper.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the live display."""
        self._wrapper.__exit__(exc_type, exc_val, exc_tb)

    def update(self, layout: Any) -> None:
        """Update the displayed layout."""
        self._wrapper.update(layout)

    def refresh(self) -> None:
        """Force a refresh."""
        self._wrapper.refresh()
