import json
from typing import Any

from rich.console import RenderableType
from rich.json import JSON

from ..core.console import get_console
from ..core.theme import get_theme


class JsonView:
    """Themed JSON display with syntax highlighting."""

    def __init__(
        self,
        data: Any,
        indent: int = 2,
        highlight: bool = True,
        skip_keys: bool = False,
        ensure_ascii: bool = False,
        sort_keys: bool = False,
        default: Any = None,
    ):
        """Create a JSON view."""
        self.data = data
        self.indent = indent
        self.highlight = highlight
        self.skip_keys = skip_keys
        self.ensure_ascii = ensure_ascii
        self.sort_keys = sort_keys
        self.default = default
        self.console = get_console()
        self.theme = get_theme()

    def _prepare_json(self) -> str:
        """Prepare data as JSON string."""
        # If data is already a string, use it directly
        if isinstance(self.data, str):
            # Validate it's valid JSON
            try:
                json.loads(self.data)
                return self.data
            except json.JSONDecodeError:
                # Fail-safe: return error JSON
                return '{"error": "Invalid JSON string"}'

        # Convert data to JSON string
        try:
            return json.dumps(
                self.data,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
                sort_keys=self.sort_keys,
                default=self.default,
            )
        except (TypeError, ValueError):
            # Fail-safe: return error JSON
            return '{"error": "Unable to serialize data to JSON"}'

    def __rich__(self) -> RenderableType:
        """Render the JSON as a Rich renderable."""
        json_text = self._prepare_json()

        return JSON(
            json_text,
            indent=self.indent,
            highlight=self.highlight,
            skip_keys=self.skip_keys,
        )

    def print(self) -> None:
        """Print the JSON to console."""
        self.console.print(self.__rich__())

    @classmethod
    def from_file(cls, file_path: str, **kwargs: Any) -> "JsonView":
        """Create JsonView from a JSON file."""
        from pathlib import Path

        path = Path(file_path)

        # Fail-safe: check if file exists
        if not path.exists():
            return cls({"error": "File not found"}, **kwargs)

        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError:
            # Fail-safe: return error
            return cls({"error": "Invalid JSON in file"}, **kwargs)
        except Exception:
            # Fail-safe: return error
            return cls({"error": "Error reading file"}, **kwargs)

        return cls(data, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any], **kwargs: Any) -> "JsonView":
        """Create JsonView from a dictionary."""
        return cls(data, **kwargs)

    @classmethod
    def from_list(cls, data: list[Any], **kwargs: Any) -> "JsonView":
        """Create JsonView from a list."""
        return cls(data, **kwargs)

    @classmethod
    def from_string(cls, json_string: str, **kwargs: Any) -> "JsonView":
        """Create JsonView from a JSON string."""
        return cls(json_string, **kwargs)

    def to_string(self) -> str:
        """Convert to formatted JSON string."""
        return self._prepare_json()

    def to_dict(self) -> dict[str, Any] | list[Any] | Any:
        """Convert to Python object."""
        if isinstance(self.data, str):
            try:
                return json.loads(self.data)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON"}
        return self.data

    @classmethod
    def pretty(cls, data: Any, **kwargs: Any) -> "JsonView":
        """Create a pretty-printed JSON view."""
        return cls(data, **{**{"indent": 4, "sort_keys": True}, **kwargs})

    @classmethod
    def compact(cls, data: Any, **kwargs: Any) -> "JsonView":
        """Create a compact JSON view."""
        return cls(data, **{**{"indent": None}, **kwargs})
