from pathlib import Path
from typing import Any, Literal

from rich.console import RenderableType
from rich.markdown import Markdown as RichMarkdown

from ..core.console import get_console
from ..core.theme import get_theme


class Markdown:
    """Themed Markdown rendering for terminal."""

    def __init__(
        self,
        markdown: str,
        code_theme: str = "monokai",
        justify: Literal["default", "left", "center", "right", "full"] | None = None,
        inline_code_lexer: str | None = None,
        inline_code_theme: str | None = None,
    ):
        """Create a Markdown renderer."""
        self.markdown_text = markdown
        self.code_theme = code_theme
        self.justify = justify
        self.inline_code_lexer = inline_code_lexer
        self.inline_code_theme = inline_code_theme
        self.console = get_console()
        self.theme = get_theme()

    def __rich__(self) -> RenderableType:
        """Render the markdown as a Rich renderable."""
        return RichMarkdown(
            self.markdown_text,
            code_theme=self.code_theme,
            justify=self.justify,
            inline_code_lexer=self.inline_code_lexer,
            inline_code_theme=self.inline_code_theme,
        )

    def print(self) -> None:
        """Print the markdown to console."""
        self.console.print(self.__rich__())

    @classmethod
    def from_file(cls, file_path: str, **kwargs: Any) -> "Markdown":
        """Create Markdown from a file."""
        path = Path(file_path)

        # Fail-safe: check if file exists
        if not path.exists():
            return cls("# File not found", **kwargs)

        try:
            markdown_text = path.read_text()
        except Exception:
            # Fail-safe: return error message
            return cls("# Error reading file", **kwargs)

        return cls(markdown_text, **kwargs)

    @classmethod
    def heading(cls, text: str, level: int = 1, **kwargs: Any) -> "Markdown":
        """Create a Markdown heading."""
        # Ensure level is between 1 and 6
        level = max(1, min(6, level))
        hashes = "#" * level
        return cls(f"{hashes} {text}", **kwargs)

    @classmethod
    def from_list(cls, items: list[str], ordered: bool = False, **kwargs: Any) -> "Markdown":
        """Create a Markdown list."""
        lines = []
        for i, item in enumerate(items, 1):
            if ordered:
                lines.append(f"{i}. {item}")
            else:
                lines.append(f"- {item}")

        return cls("\n".join(lines), **kwargs)

    @classmethod
    def table(
        cls,
        headers: list[str],
        rows: list[list[str]],
        **kwargs: Any,
    ) -> "Markdown":
        """Create a Markdown table."""
        lines = []

        # Header row
        lines.append("| " + " | ".join(headers) + " |")

        # Separator row
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Data rows
        for row in rows:
            # Pad row if it's shorter than headers
            padded_row = row + [""] * (len(headers) - len(row))
            lines.append("| " + " | ".join(padded_row[: len(headers)]) + " |")

        return cls("\n".join(lines), **kwargs)

    @classmethod
    def code_block(cls, code: str, language: str = "python", **kwargs: Any) -> "Markdown":
        """Create a Markdown code block."""
        return cls(f"```{language}\n{code}\n```", **kwargs)

    @classmethod
    def quote(cls, text: str, **kwargs: Any) -> "Markdown":
        """Create a Markdown blockquote."""
        lines = text.split("\n")
        quoted_lines = [f"> {line}" for line in lines]
        return cls("\n".join(quoted_lines), **kwargs)
