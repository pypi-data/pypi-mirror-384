import os
from typing import Any, ClassVar

from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text

from ..core.theme import get_theme


class KeyValue:
    """Key-value list with alignment and masking."""

    DEFAULT_SECRET_KEYS: ClassVar[set[str]] = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "private_key",
        "privatekey",
        "auth",
        "authorization",
        "credential",
        "credentials",
        "cert",
        "certificate",
        "key",
    }

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        title: str | None = None,
        mask_secrets: bool = True,
        secret_keys: set[str] | None = None,
        reveal: bool = False,
        key_style: str | None = None,
        value_style: str | None = None,
        separator: str = ":",
        align: bool = True,
    ):
        """Create a key-value list."""
        self.data = data or {}
        self.title = title
        self.mask_secrets = mask_secrets and not reveal
        self.secret_keys = secret_keys or set()
        self.secret_keys.update(self.DEFAULT_SECRET_KEYS)
        self.key_style = key_style
        self.value_style = value_style
        self.separator = separator
        self.align = align
        self.theme = get_theme()
        self._items: list[tuple[str, Any]] = []

    def add(self, key: str, value: Any) -> None:
        """Add a key-value pair."""
        self._items.append((key, value))

    def add_many(self, items: dict[str, Any]) -> None:
        """Add multiple key-value pairs."""
        for key, value in items.items():
            self.add(key, value)

    def _should_mask(self, key: str) -> bool:
        """Check if a key should be masked."""
        if not self.mask_secrets:
            return False

        key_lower = key.lower()
        return any(secret in key_lower for secret in self.secret_keys)

    def _format_value(self, key: str, value: Any) -> str:
        """Format a value, applying masking if needed."""
        if self._should_mask(key):
            if value:
                # Show partial value for debugging
                str_value = str(value)
                if len(str_value) > 4:
                    return f"{str_value[:2]}{'*' * 6}{str_value[-2:]}"
                else:
                    return "*" * 8
            else:
                return "(empty)"

        # Format based on type
        if value is None:
            return "(empty)"
        elif isinstance(value, bool):
            return "✓" if value else "✖"
        elif isinstance(value, list | tuple):
            if len(value) == 0:
                return "(empty list)"
            elif len(value) <= 3:
                return ", ".join(str(v) for v in value)
            else:
                return f"{', '.join(str(v) for v in value[:3])}, ... ({len(value)} items)"
        elif isinstance(value, dict):
            return f"(dict with {len(value)} keys)"
        else:
            return str(value)

    def __rich__(self) -> RenderableType:
        """Render the key-value list as a Rich renderable."""
        all_items = list(self.data.items()) + self._items

        if not all_items:
            return Text("(no data)", style=self.theme.get_style("muted"))

        if self.align:
            # Use a table for alignment
            table = Table(
                show_header=False,
                show_edge=False,
                show_lines=False,
                box=None,
                padding=(0, 1),
                title=self.title,
            )

            # Add columns
            table.add_column(
                "Key",
                style=self.key_style or self.theme.get_style("primary"),
                no_wrap=True,
            )
            table.add_column(
                "Sep",
                style=self.theme.get_style("muted"),
                width=len(self.separator),
            )
            table.add_column(
                "Value",
                style=self.value_style or self.theme.get_style("text"),
            )

            # Add rows
            for key, value in all_items:
                formatted_value = self._format_value(key, value)
                table.add_row(key, self.separator, formatted_value)

            return table
        else:
            # Simple text output
            lines = []

            if self.title:
                lines.append(Text(self.title, style=self.theme.get_style("primary")))
                lines.append(Text(""))

            for key, value in all_items:
                formatted_value = self._format_value(key, value)
                key_text = Text(key, style=self.key_style or self.theme.get_style("primary"))
                sep_text = Text(f"{self.separator} ", style=self.theme.get_style("muted"))
                value_text = Text(
                    formatted_value, style=self.value_style or self.theme.get_style("text")
                )

                line = Text()
                line.append(key_text)
                line.append(sep_text)
                line.append(value_text)
                lines.append(line)

            return Group(*lines)

    @classmethod
    def from_config(cls, config: dict[str, Any], **kwargs: Any) -> "KeyValue":
        """Create a key-value list from a configuration dictionary."""
        return cls(data=config, title="Configuration", **kwargs)

    @classmethod
    def from_environment(cls, prefix: str | None = None, **kwargs: Any) -> "KeyValue":
        """Create a key-value list from environment variables."""
        env_vars = {}
        for key, value in os.environ.items():
            if prefix is None or key.startswith(prefix):
                env_vars[key] = value

        title = f"Environment Variables ({prefix}*)" if prefix else "Environment Variables"
        return cls(data=env_vars, title=title, **kwargs)
