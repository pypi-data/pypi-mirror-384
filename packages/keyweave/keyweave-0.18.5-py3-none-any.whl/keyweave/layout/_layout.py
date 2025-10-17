from typing import Any, Iterable

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


class Layout(EventEmitter):
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

    _registered: list[KeyHook]
    _map: BindingCollection
    _active: bool = False

    def __init__(
        self,
        *,
        name: str,
        scheduler: Scheduler | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        bindings: Iterable[Binding] = (),
    ):
        super().__init__()

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

    def __iadd__(self, binding: Binding):
        self.add_binding(binding)
        return self

    @property
    def is_empty(self):
        return len(self._map) == 0

    def intercept(self, interceptor: FuncHotkeyInterceptor) -> "Layout":
        return Layout(
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
            self.emit("enter", self)
        except:
            for hook in registered:
                hook.__exit__()
            raise
        self._registered = key_hooks

    def __exit__(self, *args: Any):
        for hook in self._registered:
            hook.__exit__()
        self.emit("exit", self)
        return False

    @staticmethod
    def create(
        name: str, d: dict[Hotkey | Key, Command | CommandProducer]
    ) -> "Layout":
        clean_dict = {k.__hotkey__().info: v for k, v in d.items()}
        xs = [Binding(k, v.__get__()) for k, v in clean_dict.items()]
        return Layout(name=name, bindings=xs)
