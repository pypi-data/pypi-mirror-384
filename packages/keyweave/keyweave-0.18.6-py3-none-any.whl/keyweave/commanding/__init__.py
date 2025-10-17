from dataclasses import dataclass, field
from functools import partial
import inspect
from types import MethodType
from typing import (
    Any,
    Awaitable,
    Callable,
    Literal,
    NotRequired,
    Protocol,
    TYPE_CHECKING,
    TypedDict,
    Unpack,
)


from keyweave.shorthand import SimpleCoroutine
from keyweave.util.dict import default_dicts, merge_dicts
from keyweave.util.reflect import (
    clean_method_name,
    get_self_dict_restricted,
    is_unbound_method,
)


if TYPE_CHECKING:
    from keyweave.hotkey import Hotkey, HotkeyEvent
    from keyweave.layout._layout_class import LayoutClass
    from keyweave.interception import (
        FuncHotkeyInterceptor,
        AnyHotkeyInterceptor,
        HotkeyInterceptor,
        MethodHotkeyInterceptor,
    )


class CommandMetaProperties(TypedDict):
    label: NotRequired[str | None]
    description: NotRequired[str | None]
    emoji: NotRequired[str | None]


@dataclass(kw_only=True)
class CommandMeta:
    """
    Metadata about a command. Used for debugging and user feedback.
    """

    label: str | None = field(default=None)
    description: str | None = field(default=None)
    emoji: str | None = field(default=None)
    metadata: Any | None = field(default=None)

    def __str__(self):
        text = list[str]()
        if self.emoji:
            text.append(self.emoji)
        if self.label:
            text.append(self.label)
        return " ".join(text) if text else "<unnamed command>"

    def with_defaults(self, **kwargs: Unpack[CommandMetaProperties]):
        attrs = default_dicts(
            get_self_dict_restricted(self, CommandMeta), kwargs
        )
        return CommandMeta(**attrs)

    def with_changes(
        self,
        **kwargs: Unpack[CommandMetaProperties],
    ) -> "CommandMeta":
        attrs = merge_dicts(get_self_dict_restricted(self, CommandMeta), kwargs)
        return CommandMeta(**attrs)  # type: ignore[argument]


@dataclass
class Command:
    """
    Represents a command that can be triggered by a hotkey, with an attached handler.
    """

    info: CommandMeta
    handler: "FuncHotkeyHandler"
    no_intercept: bool

    def __get__(
        self, instance: object | None = None, owner: type | None = None
    ) -> "Command":
        return self

    def __str__(self):
        return f"{self.info.emoji} {self.info.label}"

    def bind(self, hotkey: "Hotkey"):
        from ..bindings import Binding

        return Binding(hotkey.info, self)

    def intercept(self, *interceptors: "FuncHotkeyInterceptor"):
        if self.no_intercept:
            return self
        handler = self.handler
        for interceptor in interceptors:
            handler = _wrap_interceptor(interceptor, handler)
        return Command(
            info=self.info, handler=handler, no_intercept=self.no_intercept
        )


class FuncHotkeyHandler(Protocol):
    """
    Represents a non-instance function that handles a hotkey event.
    """

    def __call__(self, event: "HotkeyEvent", /) -> Any: ...


class MethodHotkeyHandler(Protocol):
    """
    Represents an instance method that handles a hotkey event.
    """

    def __call__(self, instance: Any, event: "HotkeyEvent", /) -> Any: ...


type HotkeyHandler = FuncHotkeyHandler | MethodHotkeyHandler


class CommandProducer:
    """
    Represents an object that produces a command with an attached handler. When applied to a method,
    requires additional context to function properly.
    """

    def __str__(self):
        return str(self.cmd)

    def __init__(
        self,
        func: HotkeyHandler,
        cmd: CommandMeta,
        interceptor: "AnyHotkeyInterceptor | bool",
    ):
        self.func = func
        self.cmd = cmd
        self.interceptor = interceptor

    def _make(self, instance: object | None = None):
        def wrapper(event: "HotkeyEvent", /) -> Any:
            arg_count = len(inspect.signature(self.func).parameters)
            match arg_count:
                case 1:
                    return self.func(event)  # type: ignore
                case 2:
                    return self.func.__get__(instance)(event)  # type: ignore
                case _:
                    raise ValueError("Invalid number of arguments")

        existing_interceptor = self.interceptor
        cmd = self.cmd
        if callable(existing_interceptor) and is_unbound_method(
            existing_interceptor
        ):
            wrapper = _wrap_interceptor(
                partial(existing_interceptor, instance), wrapper
            )

        return Command(
            info=cmd, handler=wrapper, no_intercept=self.interceptor is not True
        )

    def __get__(
        self, instance: object | None, owner: type | None = None
    ) -> Command:
        """
        May bind an instance to a command handler so it can be invoked as an instance method.
        """
        return self._make(instance)


type CommandOrProducer = Command | CommandProducer


@dataclass(kw_only=True)
class command(CommandMeta):
    interceptor: "AnyHotkeyInterceptor | bool" = field(default=True)

    """
    Use this decorator on a method or function to turn it into a Command.
    """

    def __call__(self, handler: HotkeyHandler) -> "CommandProducer":
        cmd = self.with_defaults(label=clean_method_name(handler))
        return CommandProducer(handler, cmd=cmd, interceptor=self.interceptor)


def _wrap_interceptor(
    interceptor: "FuncHotkeyInterceptor", handler: FuncHotkeyHandler
) -> FuncHotkeyHandler:
    from keyweave.interception import HotkeyInterceptionEvent

    async def _handler(e: "HotkeyEvent"):
        interception = HotkeyInterceptionEvent(e, handler)
        result = interceptor(interception)
        if isinstance(result, Awaitable):
            await result
        if not interception.handled:
            raise ValueError(f"Interceptor {interceptor} did not handle {e}")
        return result

    return _handler
