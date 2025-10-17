from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Protocol

from keyweave.commanding import FuncHotkeyHandler
from keyweave.hotkey import HotkeyEvent
from keyweave.shorthand import SimpleCoroutine
from keyweave.util.event_loop import norm_maybe_async

if TYPE_CHECKING:
    from keyweave.layout._layout_class import LayoutClass


@dataclass(init=False)
class HotkeyInterceptionEvent(HotkeyEvent):
    """
    Represents an intercepted `HotkeyEvent`. Used in the layout hotkey interception API.
    """

    def __str__(self):
        return super().__str__() + " (intercepted)"

    _handled: bool = False

    def __init__(self, event: HotkeyEvent, handler: FuncHotkeyHandler):
        HotkeyEvent.__init__(self, event.binding, event.event)
        self._handler = handler

    def next(self):
        self._handled = True
        result = self._handler(self)
        return result

    def end(self):
        self._handled = True

    @property
    def handled(self):
        return self._handled


class HotkeyInterceptor(Protocol):
    """
    A function that can intercept a hotkey event.
    """

    def __call__(
        self, action: HotkeyInterceptionEvent
    ) -> None | SimpleCoroutine[None]: ...


class FuncHotkeyInterceptor(Protocol):
    """
    A function that can intercept a hotkey event.
    """

    def __call__(
        self, action: HotkeyInterceptionEvent, /
    ) -> None | SimpleCoroutine[None]: ...


class MethodHotkeyInterceptor(Protocol):
    """
    A method that can intercept a hotkey event.
    """

    def __call__(
        self, instance: Any, action: HotkeyInterceptionEvent, /
    ) -> None | SimpleCoroutine[None]: ...


type AnyHotkeyInterceptor = (FuncHotkeyInterceptor | MethodHotkeyInterceptor)
