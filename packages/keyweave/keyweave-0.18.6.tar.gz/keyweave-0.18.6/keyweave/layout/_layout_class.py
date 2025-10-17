from typing import Awaitable, Callable
from keyweave.interception import HotkeyInterceptionEvent

from abc import ABC

from keyweave.bindings import Binding, BindingProducer
from keyweave.commanding import Command, CommandMeta, CommandProducer
from keyweave.layout._layout import Layout
from keyweave.scheduling import Scheduler
from keyweave._util.logging import keyweaveLogger
from keyweave.shorthand import SimpleCoroutine
from keyweave.util.reflect import get_attrs_down_to


my_logger = keyweaveLogger


class LayoutClass(ABC):
    """
    Use this to create a hotkey layout using a class. Using this mode, you declare commands and bind hotkeys.

    Commands are declared using the `command` decorator, while hotkeys are bound by using Hotkey objects as decorators.

    >>> from pykeys.layout import LayoutClass
    >>> from pykeys import key
    >>> from pykeys.commanding import command
    >>> class MyLayout(LayoutClass):
    ...     @(key.a & key.ctrl + key.shift)
    ...     @command(label="my_command")
    ...     def my_command(self, e: HotkeyEvent):
    ...         pass

    When you create an instance of `MyLayout`, you will get a `Layout` object rather than the class you defined.

    >>> layout = MyLayout()
    >>> isinstance(layout, Layout)
    True

    However, an instance of your class is still created and will be passed to the `self` parameter of command methods.

    Note that you must apply both `command` and hotkey decorators. Using just one of them is an error.

    However, you can still have helper methods that are not hotkey commands. Just don't use either decorator. These methods
    can only be accessed internally within the LayoutClass, such as by hotkey commands.

    >>> class MyLayout(LayoutClass):
    ...     def my_helper_method(self):
    ...         pass
    ...     @(key.a & key.ctrl + key.shift)
    ...     @command(label="my_command")
    ...     def my_command(self, e: HotkeyEvent):
    ...         self.my_helper_method()

    You can define an `__intercept__` method in your layout class. This lets you capture hotkey events and modify their behavior. This can be used for logging and similar:

    >>> class MyLayout(LayoutClass):
    ...     def __intercept__(self, intercepted: HotkeyInterceptionEvent):
    ...         print(intercepted)

    """

    _layout: "Layout"

    def signal_stop(self):
        if not self._layout._active_event.is_set():  # type: ignore
            self._layout._active_event.set()  # type: ignore
        else:
            raise RuntimeError("Layout is not active")

    def __post_init__(self):
        """
        Executed internally after an instance of this class is created, before a Layout is returned.
        """
        pass

    def __intercept__(
        self, intercepted: HotkeyInterceptionEvent
    ) -> None | SimpleCoroutine[None]:
        """
        The default interceptor. If overriden, intercepts all hotkey events for this layout that haven't
        configured interception.
        """
        pass

    def __new__(
        cls,
        name: str | None = None,
        scheduler: Scheduler | None = None,
        on_error: Callable[[BaseException], None] | None = None,
    ):
        """
        Always returns a Layout instance wrapping this class instance.
        """
        obj = super().__new__(cls)
        my_logger.info(f"Creating instance")
        layout = Layout(
            name=name or cls.__name__, scheduler=scheduler, on_error=on_error
        )
        obj._layout = layout
        obj.__post_init__()

        attrs = get_attrs_down_to(
            obj,
            LayoutClass,
            resolve_descriptor=lambda x: isinstance(
                x, (CommandProducer, Command, Binding, BindingProducer)
            ),
        )

        for _, value in attrs.items():
            match value:
                case Binding() as b:
                    layout.add_binding(b)
                case CommandMeta() as c:
                    my_logger.warning(
                        f"Command {c} is missing a hotkey binding decorator. It will be ignored."
                    )
                case _:
                    pass

        if hasattr(obj, "__intercept__"):
            layout = layout.intercept(obj.__intercept__)  # type: ignore
        return layout
