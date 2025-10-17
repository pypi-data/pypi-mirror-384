from asyncio.constants import THREAD_JOIN_TIMEOUT
import threading
from typing import Any, Iterable, Literal, overload

from typing import Callable

from pyee import EventEmitter


from keyweave.bindings import BindingCollection
from keyweave.bindings import Binding
from keyweave.commanding import Command, CommandProducer
from keyweave.hotkey import Hotkey
from keyweave.interception import (
    FuncHotkeyInterceptor,
    HotkeyInterceptor,
)
from keyweave.key_types import Key
from keyweave._hook import KeyHook
from keyweave.print.style import style
from keyweave.scheduling import default_scheduler, Scheduler
import sys
from threading import Event


class Layout:
    """
    A Hotkey layout consisting of `Binding` objects that link Hotkey events to Commands with attached handlers.

    Creating a layout using functions:

    >>> from pykeys import key, command
    ... @command("command_1")
    ... def command_1(e: HotkeyEvent):
    ...     pass
    ...
    ... @command("command_2")
    ... def command_2(e: HotkeyEvent):
    ...     pass
    >>> layout = Layout.create("my_layout", {
    ...     key.a: command_1,
    ...     key.b: command_2,
    ... })

    To enable a layout, use a context manager:
    >>> with layout:
    ...     import time
    ...     time.sleep(10)  # keep the layout active for 10 seconds

    You can also create a layout using a class by subclassing `LayoutClass`.
    """

    _emitter: EventEmitter
    _registered: list[KeyHook]
    _map: BindingCollection
    _active: bool = False
    _active_event: Event

    def __init__(
        self,
        *,
        name: str,
        scheduler: Scheduler | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        bindings: Iterable[Binding] = (),
    ):
        super().__init__()
        self._emitter = EventEmitter()
        e = self._active_event = Event()
        e.set()

        def default_on_error(e: BaseException):
            import traceback

            # Print the full exception with traceback to stderr so the error is visible.
            traceback.print_exception(
                type(e), e, e.__traceback__, file=sys.stderr
            )

        scheduler = scheduler or default_scheduler(on_error or default_on_error)
        self.name = name
        self._scheduler = scheduler
        self._map = BindingCollection()
        for binding in bindings:
            self.add_binding(binding)

    @overload
    def on(
        self, event: Literal["enter"], cb: Callable[["Layout"], None]
    ) -> None: ...
    @overload
    def on(
        self, event: Literal["exit"], cb: Callable[["Layout"], None]
    ) -> None: ...

    def on(self, event: str, cb: Callable[..., None]) -> None:
        self._emitter.on(event, cb)

    @overload
    def once(
        self, event: Literal["enter"], cb: Callable[["Layout"], None]
    ) -> None: ...
    @overload
    def once(
        self, event: Literal["exit"], cb: Callable[["Layout"], None]
    ) -> None: ...
    def once(self, event: str, cb: Callable[..., None]) -> None:
        self._emitter.once(event, cb)  # type: ignore

    def remove_listener(self, event: str, cb: Callable[..., None]) -> None:
        self._emitter.remove_listener(event, cb)  # type: ignore

    def remove_all_listeners(self, event: str) -> None:
        self._emitter.remove_all_listeners(event)  # type: ignore

    def __iadd__(self, binding: Binding):
        self.add_binding(binding)
        return self

    @property
    def is_empty(self):
        return len(self._map) == 0

    def intercept(self, interceptor: FuncHotkeyInterceptor) -> "Layout":
        lt = Layout(
            name=self.name,
            scheduler=self._scheduler,
            bindings=[
                (
                    binding.intercept(interceptor)
                    if not binding.command.no_intercept
                    else binding
                )
                for binding in self._map.bindings
            ],
        )
        lt._emitter = self._emitter
        lt._active_event = self._active_event
        return lt

    @property
    def active(self):
        return self._active

    def add_binding(self, binding: Binding):
        self._map += binding

    def __len__(self):
        return len(self._map)

    @property
    def bindings(self):
        return self._map.bindings

    def __iter__(self):
        return iter(self._map.bindings)

    def _get_key_hooks(self):
        return [
            KeyHook(key, bindings, self._scheduler)
            for key, bindings in self._map.pairs
        ]

    def __enter__(self):
        from ._print_layout import print_entering_message

        print_entering_message(self)
        key_hooks = self._get_key_hooks()
        registered: list[KeyHook] = []
        try:
            for hook in key_hooks:
                hook.__enter__()
                registered.append(hook)
            self._emitter.emit("enter", self)
        except:
            for hook in registered:
                hook.__exit__()
            raise
        self._registered = key_hooks
        self._active_event.clear()
        return self._active_event

    def __exit__(self, *args: Any):
        for hook in self._registered:
            hook.__exit__()
        self._emitter.emit("exit", self)
        return False

    @staticmethod
    def create(
        name: str, d: dict[Hotkey | Key, Command | CommandProducer]
    ) -> "Layout":
        clean_dict = {k.__hotkey__().info: v for k, v in d.items()}
        xs = [Binding(k, v.__get__()) for k, v in clean_dict.items()]
        return Layout(name=name, bindings=xs)
