from typing import Any

from rich.prompt import (
    Confirm as RichConfirm,
    FloatPrompt as RichFloatPrompt,
    IntPrompt as RichIntPrompt,
    InvalidResponse,
    Prompt as RichPrompt,
)

from ..core.console import get_console
from ..core.theme import get_theme


class Input:
    """Themed text input prompt with validation."""

    def __init__(
        self,
        prompt: str = "Enter value",
        default: str | None = None,
        choices: list[str] | None = None,
        password: bool = False,
        case_sensitive: bool = True,
        show_default: bool = True,
        show_choices: bool = True,
    ):
        """Initialize input prompt."""
        self.prompt = prompt
        self.default = default
        self.choices = choices
        self.password = password
        self.case_sensitive = case_sensitive
        self.show_default = show_default
        self.show_choices = show_choices
        self.console = get_console()
        self.theme = get_theme()

    def ask(self) -> str:
        """Display prompt and get user input."""
        try:
            # Apply theme to prompt text
            styled_prompt = f"[{self.theme.get_style('primary')}]{self.prompt}[/]"

            # Use empty string as default if None to ensure we return string
            default_value = self.default if self.default is not None else ""

            result = RichPrompt.ask(
                styled_prompt,
                console=self.console,
                default=default_value,
                choices=self.choices,
                password=self.password,
                case_sensitive=self.case_sensitive,
                show_default=self.show_default,
                show_choices=self.show_choices,
            )
            return result
        except (KeyboardInterrupt, EOFError):
            # Fail-safe: return default or empty string
            return self.default if self.default is not None else ""

    @classmethod
    def ask_once(
        cls,
        prompt: str,
        default: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Quick one-off input prompt."""
        input_prompt = cls(prompt, default=default, **kwargs)
        return input_prompt.ask()


class Confirm:
    """Themed yes/no confirmation prompt."""

    def __init__(
        self,
        prompt: str = "Continue?",
        default: bool = False,
        show_default: bool = True,
    ):
        """Initialize confirmation prompt."""
        self.prompt = prompt
        self.default = default
        self.show_default = show_default
        self.console = get_console()
        self.theme = get_theme()

    def ask(self) -> bool:
        """Display confirmation and get user response."""
        try:
            # Apply theme to prompt text
            styled_prompt = f"[{self.theme.get_style('warning')}]{self.prompt}[/]"

            result = RichConfirm.ask(
                styled_prompt,
                console=self.console,
                default=self.default,
                show_default=self.show_default,
            )
            return result
        except (KeyboardInterrupt, EOFError):
            # Fail-safe: return default
            return self.default

    @classmethod
    def ask_once(
        cls,
        prompt: str,
        default: bool = False,
        **kwargs: Any,
    ) -> bool:
        """Quick one-off confirmation prompt."""
        confirm_prompt = cls(prompt, default=default, **kwargs)
        return confirm_prompt.ask()


class Select:
    """Themed choice selection prompt."""

    def __init__(
        self,
        prompt: str,
        choices: list[str],
        default: str | None = None,
        case_sensitive: bool = False,
    ):
        """Initialize selection prompt."""
        if not choices:
            raise ValueError("Select requires at least one choice")

        self.prompt = prompt
        self.choices = choices
        self.default = default or choices[0]
        self.case_sensitive = case_sensitive
        self.console = get_console()
        self.theme = get_theme()

    def ask(self) -> str:
        """Display selection and get user choice."""
        try:
            # Apply theme to prompt text and choices
            styled_prompt = f"[{self.theme.get_style('primary')}]{self.prompt}[/]"

            result = RichPrompt.ask(
                styled_prompt,
                console=self.console,
                choices=self.choices,
                default=self.default,
                case_sensitive=self.case_sensitive,
                show_choices=True,
                show_default=True,
            )
            return result
        except (KeyboardInterrupt, EOFError):
            # Fail-safe: return default
            return self.default

    @classmethod
    def ask_once(
        cls,
        prompt: str,
        choices: list[str],
        default: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Quick one-off selection prompt."""
        select_prompt = cls(prompt, choices, default=default, **kwargs)
        return select_prompt.ask()


class NumberInput:
    """Themed numeric input prompt with validation."""

    def __init__(
        self,
        prompt: str = "Enter number",
        default: int | float | None = None,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        integer_only: bool = False,
    ):
        """Initialize number input prompt."""
        self.prompt = prompt
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
        self.console = get_console()
        self.theme = get_theme()

    def _validate(self, value: int | float) -> bool:
        """Validate numeric input against constraints."""
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def ask(self) -> None | int | float:
        """Display prompt and get numeric input."""
        try:
            # Apply theme to prompt text
            styled_prompt = f"[{self.theme.get_style('primary')}]{self.prompt}[/]"

            # Add range hint to prompt if constraints exist
            if self.min_value is not None or self.max_value is not None:
                range_hint = []
                if self.min_value is not None:
                    range_hint.append(f"min: {self.min_value}")
                if self.max_value is not None:
                    range_hint.append(f"max: {self.max_value}")
                styled_prompt += f" [{self.theme.get_style('muted')}]({', '.join(range_hint)})[/]"

            # Choose appropriate prompt type
            prompt_class = RichIntPrompt if self.integer_only else RichFloatPrompt

            while True:
                try:
                    # Ensure we have a valid default for the prompt
                    default_value: int | float = (
                        self.default
                        if self.default is not None
                        else (0 if self.integer_only else 0.0)
                    )

                    result: int | float = prompt_class.ask(
                        styled_prompt,
                        console=self.console,
                        default=default_value,
                    )

                    # Validate against constraints
                    if self._validate(result):
                        return result
                    else:
                        # Show validation error
                        error_msg = f"[{self.theme.get_style('error')}]Value must be"
                        if self.min_value is not None and self.max_value is not None:
                            error_msg += f" between {self.min_value} and {self.max_value}"
                        elif self.min_value is not None:
                            error_msg += f" >= {self.min_value}"
                        elif self.max_value is not None:
                            error_msg += f" <= {self.max_value}"
                        error_msg += "[/]"
                        self.console.print(error_msg)
                except InvalidResponse:
                    # Continue loop on invalid input
                    continue

        except (KeyboardInterrupt, EOFError):
            # Fail-safe: return default or 0
            fallback_value: int | float = 0 if self.integer_only else 0.0
            return self.default if self.default is not None else fallback_value

    @classmethod
    def ask_once(
        cls,
        prompt: str,
        default: int | float | None = None,
        **kwargs: Any,
    ) -> int | float | None:
        """Quick one-off number input prompt."""
        number_prompt = cls(prompt, default=default, **kwargs)
        return number_prompt.ask()


class IntInput(NumberInput):
    """Convenience class for integer-only input."""

    def __init__(
        self,
        prompt: str = "Enter integer",
        default: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
    ):
        """Initialize integer input prompt."""
        super().__init__(
            prompt=prompt,
            default=default,
            min_value=min_value,
            max_value=max_value,
            integer_only=True,
        )


class FloatInput(NumberInput):
    """Convenience class for float input."""

    def __init__(
        self,
        prompt: str = "Enter number",
        default: float | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
    ):
        """Initialize float input prompt."""
        super().__init__(
            prompt=prompt,
            default=default,
            min_value=min_value,
            max_value=max_value,
            integer_only=False,
        )
