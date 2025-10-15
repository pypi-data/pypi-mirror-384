from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any

import toml


@dataclass
class Theme:
    """Theme configuration with design tokens."""

    colors: dict[str, str] = field(
        default_factory=lambda: {
            "primary": "cyan",
            "secondary": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "blue",
            "muted": "dim white",
            "accent": "bright_cyan",
            "background": "default",
            "text": "default",
            "debug": "dim cyan",
            "critical": "bright_red",
        }
    )

    spacing: dict[str, int] = field(
        default_factory=lambda: {
            "xs": 0,
            "sm": 1,
            "default": 1,
            "md": 2,
            "lg": 3,
            "xl": 4,
        }
    )

    glyphs: dict[str, str] = field(
        default_factory=lambda: {
            "success": "✓",
            "error": "✖",
            "warning": "⚠",
            "info": "i",
            "debug": "▪",
            "critical": "‼",
            "arrow": "→",
            "bullet": "•",
            "check": "✓",
            "cross": "✖",
            "spinner": "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏",
            "pending": "○",
            "running": "◔",
            "complete": "●",
            "failed": "✖",
            "skipped": "⊘",
        }
    )

    borders: dict[str, str] = field(
        default_factory=lambda: {
            "style": "rounded",
            "panel": "rounded",
            "table": "rounded",
            "section": "rounded",
        }
    )

    def get(self, path: str, default: Any = None) -> Any:
        """Get a theme value by dot-notation path."""
        parts = path.split(".")
        current: Any = self.__dict__

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)

            if current is None:
                return default

        return current

    def update(self, updates: dict[str, Any]) -> None:
        """Update theme values from a dictionary."""
        for path, value in updates.items():
            parts = path.split(".")

            if len(parts) == 2:
                category, key = parts
                if hasattr(self, category):
                    attr = getattr(self, category)
                    if isinstance(attr, dict):
                        attr[key] = value

    @classmethod
    def from_file(cls, path: Path) -> "Theme":
        """Load theme from a TOML file."""
        theme = cls()

        if path.exists():
            data = toml.load(path)
            for category in ["colors", "spacing", "glyphs", "borders"]:
                if category in data:
                    setattr(theme, category, data[category])

        return theme

    @classmethod
    def from_env(cls) -> "Theme":
        """Create theme with environment variable overrides."""
        theme = cls()

        prefix = "CHALKBOX_THEME_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                path = key[len(prefix) :].lower().replace("_", ".")
                theme.update({path: value})

        return theme

    def get_style(self, level: str = "default") -> str:
        """Get Rich style string for a severity level."""
        color_map = {
            "debug": self.colors["debug"],
            "info": self.colors["info"],
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "error": self.colors["error"],
            "critical": self.colors["critical"],
            "default": self.colors["text"],
            "muted": self.colors["muted"],
            "primary": self.colors["primary"],
        }
        return color_map.get(level, self.colors["text"])


_theme: Theme | None = None


def get_theme() -> Theme:
    """Get the current theme instance."""
    global _theme
    if _theme is None:
        _theme = Theme()

        # Load from config file if exists
        config_path = Path.home() / ".chalkbox" / "theme.toml"
        if config_path.exists():
            _theme = Theme.from_file(config_path)

        # Apply environment overrides
        env_theme = Theme.from_env()
        _theme.colors.update(env_theme.colors)
        _theme.spacing.update(env_theme.spacing)
        _theme.glyphs.update(env_theme.glyphs)
        _theme.borders.update(env_theme.borders)

    return _theme


def set_theme(theme: Theme | None = None, **kwargs: Any) -> None:
    """Set the global theme."""
    global _theme

    if theme is not None:
        _theme = theme
    elif kwargs:
        if _theme is None:
            _theme = Theme()
        _theme.update(kwargs)
