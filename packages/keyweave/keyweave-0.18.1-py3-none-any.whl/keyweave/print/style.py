from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, overload

from termcolor import colored

from keyweave.print.escape import UnicodeEncoder

type _ColorName = Literal[
    "grey",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "light_grey",
    "light_red",
    "light_green",
    "light_yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "dark_grey",
    "black",
]

type _AnsiStyle = Literal[
    "bold",
    "dark",
    "underline",
    "blink",
    "reverse",
    "concealed",
    "strike",
]

type _Unset = Literal["unset"]
type _CharStyle = Literal[
    "uppercase",
    "lowercase",
]


def _alter_value[X](my_value: X | None, input: X | _Unset | None) -> X | None:
    if input == "unset":
        return None
    if input is not None:
        return input
    return my_value


@dataclass
class style:
    color: _ColorName | None = field(default=None)
    on_color: _ColorName | None = field(default=None)
    styles: Iterable[_AnsiStyle] | None = field(default=None)
    char_style: _CharStyle | None = field(default=None)
    padding: int = field(default=0)

    @property
    def _real_on_color(self) -> str | None:
        return f"on_{self.on_color}" if self.on_color else None

    def _apply_char_transform(self, text: str) -> str:
        if self.padding > 0:
            text = " " * self.padding + text + " " * self.padding
        match self.char_style:
            case "uppercase":
                text = text.upper()
            case "lowercase":
                text = text.lower()
            case None:
                pass
            case str:  # type: ignore[unreachable]
                raise NotImplementedError(str)

        return text

    def altered(
        self,
        *,
        color: _ColorName | None | _Unset = None,
        on_color: _ColorName | None | _Unset = None,
        styles: Iterable[_AnsiStyle] | None = None,
        char_style: _CharStyle | None | _Unset = None,
        padding: int | None = None,
    ) -> "style":
        return style(
            color=_alter_value(self.color, color),
            on_color=_alter_value(self.on_color, on_color),
            styles=_alter_value(self.styles, styles),
            char_style=_alter_value(self.char_style, char_style),
            padding=padding if padding is not None else self.padding,
        )

    def _apply_to_string(self, text: str) -> str:
        if text == "":
            return ""
        x = colored(
            text=self._apply_char_transform(text),
            color=self.color,
            on_color=self._real_on_color,
            attrs=list(self.styles) if self.styles else None,
        )

        return x

    @overload
    def __call__(self, text: str, /) -> str: ...

    @overload
    def __call__[**P](
        self, text_function: Callable[P, str], /
    ) -> Callable[P, str]: ...

    def __call__(
        self, text_or_function: str | Callable[..., str], /
    ) -> str | Callable[..., str]:

        if isinstance(text_or_function, str):
            return self._apply_to_string(text_or_function)
        elif callable(text_or_function):

            def wrapper(*args: Any, **kwargs: Any) -> str:
                return self._apply_to_string(text_or_function(*args, **kwargs))

            return wrapper
        else:
            raise ValueError(
                f"Expected a string or a callable, got {type(text_or_function)}"
            )
