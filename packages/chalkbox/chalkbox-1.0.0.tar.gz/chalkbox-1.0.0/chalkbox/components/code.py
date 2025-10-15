from typing import Any

from rich.console import RenderableType
from rich.syntax import Syntax

from ..core.console import get_console
from ..core.theme import get_theme


class CodeBlock:
    """Themed syntax-highlighted code display."""

    def __init__(
        self,
        code: str,
        language: str = "python",
        theme: str = "monokai",
        line_numbers: bool = True,
        line_range: tuple[int, int] | None = None,
        highlight_lines: set[int] | None = None,
        code_width: int | None = None,
        tab_size: int = 4,
        word_wrap: bool = False,
        background_color: str | None = None,
        indent_guides: bool = False,
    ):
        """Create a code block with syntax highlighting."""
        self.code = code
        self.language = language
        self.theme_name = theme
        self.line_numbers = line_numbers
        self.line_range = line_range
        self.highlight_lines = highlight_lines
        self.code_width = code_width
        self.tab_size = tab_size
        self.word_wrap = word_wrap
        self.background_color = background_color
        self.indent_guides = indent_guides
        self.console = get_console()
        self.theme = get_theme()

    def __rich__(self) -> RenderableType:
        """Render the code block as a Rich renderable."""
        return Syntax(
            self.code,
            self.language,
            theme=self.theme_name,
            line_numbers=self.line_numbers,
            line_range=self.line_range,
            highlight_lines=self.highlight_lines,
            code_width=self.code_width,
            tab_size=self.tab_size,
            word_wrap=self.word_wrap,
            background_color=self.background_color,
            indent_guides=self.indent_guides,
        )

    def print(self) -> None:
        """Print the code block to console."""
        self.console.print(self.__rich__())

    @classmethod
    def from_file(
        cls,
        file_path: str,
        language: str | None = None,
        **kwargs: Any,
    ) -> "CodeBlock":
        """Create a code block from a file."""
        from pathlib import Path

        path = Path(file_path)

        # Fail-safe: check if file exists
        if not path.exists():
            return cls("# File not found", language="text", **kwargs)

        try:
            code = path.read_text()
        except Exception:
            # Fail-safe: return error message
            return cls("# Error reading file", language="text", **kwargs)

        # Auto-detect language from extension if not provided
        if language is None:
            ext_to_lang = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "jsx",
                ".tsx": "tsx",
                ".java": "java",
                ".c": "c",
                ".cpp": "cpp",
                ".h": "c",
                ".hpp": "cpp",
                ".rs": "rust",
                ".go": "go",
                ".rb": "ruby",
                ".php": "php",
                ".swift": "swift",
                ".kt": "kotlin",
                ".cs": "csharp",
                ".html": "html",
                ".css": "css",
                ".scss": "scss",
                ".json": "json",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".toml": "toml",
                ".xml": "xml",
                ".md": "markdown",
                ".sh": "bash",
                ".bash": "bash",
                ".zsh": "zsh",
                ".fish": "fish",
                ".sql": "sql",
            }
            language = ext_to_lang.get(path.suffix.lower(), "text")

        return cls(code, language=language, **kwargs)

    @classmethod
    def python(cls, code: str, **kwargs: Any) -> "CodeBlock":
        """Create a Python code block."""
        return cls(code, language="python", **kwargs)

    @classmethod
    def javascript(cls, code: str, **kwargs: Any) -> "CodeBlock":
        """Create a JavaScript code block."""
        return cls(code, language="javascript", **kwargs)

    @classmethod
    def json(cls, code: str, **kwargs: Any) -> "CodeBlock":
        """Create a JSON code block."""
        return cls(code, language="json", **kwargs)

    @classmethod
    def bash(cls, code: str, **kwargs: Any) -> "CodeBlock":
        """Create a Bash code block."""
        return cls(code, language="bash", **kwargs)

    @classmethod
    def sql(cls, code: str, **kwargs: Any) -> "CodeBlock":
        """Create a SQL code block."""
        return cls(code, language="sql", **kwargs)

    @classmethod
    def yaml(cls, code: str, **kwargs: Any) -> "CodeBlock":
        """Create a YAML code block."""
        return cls(code, language="yaml", **kwargs)

    @classmethod
    def markdown(cls, code: str, **kwargs: Any) -> "CodeBlock":
        """Create a Markdown code block."""
        return cls(code, language="markdown", **kwargs)

    @classmethod
    def diff(cls, code: str, **kwargs: Any) -> "CodeBlock":
        """Create a diff code block."""
        return cls(code, language="diff", **kwargs)
