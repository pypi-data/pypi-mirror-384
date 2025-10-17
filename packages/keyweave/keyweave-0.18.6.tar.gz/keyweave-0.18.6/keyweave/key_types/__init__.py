from functools import total_ordering
from typing import TYPE_CHECKING, Iterable, Literal

if TYPE_CHECKING:
    from keyweave.commanding import Command, CommandProducer


@total_ordering
class Key:
    """
    Represents a single keyboard, mouse, or controller key input. You can access a preset list of
    these events via the `pykeys.key` import, for example:

    >>> from pykeys import key
    >>> key.a # represents the "a" key

    Otherwise, you can use this class to reference keys using a string:

    >>> Key("a") # also represents the "a" key

    - For mouse keys, use `Key("mouse:1")` through `Key("mouse:5")` for buttons 1-5.
    - For numpad keys, use `Key("num:0")` through `Key("num:9")` for keys 0-9.

    For symbol keys, use:

    >>> Key("+") # the + key
    >>> Key("num:+") # the + key on the numpad

    Key objects are comparable, hashable, and equatable.
    """

    id: str

    def __init__(self, input: "str | Key"):
        self.id = input if isinstance(input, str) else input.id

    @property
    def label(self):
        return self.id

    @property
    def is_numpad(self):
        return self.id.startswith("num:")

    def __hash__(self) -> int:
        return hash(self.id)

    def __keystate__(self):
        return self.down

    def __hotkey__(self):
        return self.down.__hotkey__()

    def __invert__(self):
        return KeyInputState(self, "up")

    @property
    def is_mouse(self):
        """
        Whether this key is a mouse key.
        """
        return self.id.startswith("mouse:")

    def __call__(self, cmd: "Command | CommandProducer"):
        """
        Binds a command or command producer to the hotkey. Typically used as a decorator.
        """
        from ..bindings import BindingProducer

        return BindingProducer(cmd, self.down.modifiers([]))

    @property
    def is_keyboard(self):
        """
        Whether this key is a keyboard key.
        """
        return not self.is_mouse

    def __lt__(self, other: "Key") -> bool:
        return self.id < other.id

    @property
    def specificity(self):
        return 1

    def __getitem__(self, other: "tuple[KeysInput, ...] | KeysInput"):
        return self & flatten_getitem_args(other)

    def __and__(self, other: "KeysInput"):
        """
        Creates a Hotkey using the left key as a trigger (down event) and the right keys as modifiers.

        >>> from pykeys import key
        >>> hotkey = key.a & key.ctrl + key.shift
        >>> hotkey2 = key.a & [key.ctrl, key.shift]
        >>> hotkey3 = key.a & key.ctrl
        """
        return self.down.modifiers(other)

    @property
    def down(self) -> "KeyInputState":

        return KeyInputState(self, "down")

    @property
    def up(self):
        return KeyInputState(self, "up")

    def __repr__(self) -> str:
        return f"{self.id}"

    def __str__(self) -> str:
        return repr(self)


type KeyStateName = Literal["down", "up"]


@total_ordering
class KeyInputState:
    """
    Represents key up or key down states.
    """

    __match_args__ = ("key", "state")

    @property
    def hotkey(self):
        return self.__hotkey__()

    def __str__(self) -> str:
        """
        A label for the Hotkey's trigger key.
        """
        return f"{self.state_char}{self.key}"

    def __repr__(self) -> str:
        return str(self)

    def __keystate__(self):
        return self

    def __hotkey__(self):
        from ..hotkey import Hotkey, HotkeyInfo

        return Hotkey(
            HotkeyInfo(trigger=self, modifiers=KeySet(), passthrough=False)
        )

    def __invert__(self):
        return KeyInputState(self.key, "up" if self.is_down else "down")

    def __init__(self, key: Key, state: KeyStateName):
        self.key = key
        self.state = state

    def __hash__(self) -> int:
        return hash(self.key) ^ hash(self.state)

    def modifiers(self, modifiers: "KeysInput"):
        from ..hotkey import Hotkey, HotkeyInfo

        """
        Adds modifiers to a Hotkey.
        """
        return Hotkey(
            HotkeyInfo(
                trigger=self,
                modifiers=KeySet(modifiers),
                passthrough=False,
            )
        )

    def __getitem__(self, other: "tuple[KeysInput, ...] | KeysInput"):
        return self & flatten_getitem_args(other)

    def __and__(self, other: "KeysInput"):
        return self.modifiers(other)

    @property
    def state_char(self) -> str:
        return "↓" if self.state == "down" else "↑"

    def __lt__(self, other: "KeyInputState") -> bool:
        return self.key < other.key and self.state < other.state

    @property
    def specificity(self) -> int:
        return self.key.specificity

    @property
    def is_down(self) -> bool:
        return self.state == "down"

    @property
    def is_up(self) -> bool:
        return self.state == "up"


type KeyInput = "str | Key"

type KeysInput = KeySet | Iterable[Key | KeyInputState] | Key | KeyInputState


def flatten_getitem_args(
    inputs: tuple[KeysInput, ...] | KeysInput,
) -> list[Key | KeyInputState]:
    inputs = inputs if isinstance(inputs, tuple) else (inputs,)
    return [
        y
        for x in inputs
        for y in ([x] if isinstance(x, (Key, KeyInputState)) else x)
    ]


@total_ordering
class KeySet:
    """
    An unordered collection of `KeyInputState` objects, used as a set of modifiers.
    """

    __match_args__ = ("set",)
    _mapping: dict[Key, KeyInputState]

    def __invert__(self):
        return KeySet(key.__invert__() for key in self._mapping)

    def __init__(self, input: KeysInput = {}):
        match input:
            case KeyInputState() | Key():
                self._mapping = KeySet(input)._mapping
            case KeySet():
                self._mapping = input._mapping
            case _:
                self._mapping = {
                    key.__keystate__().key: key.__keystate__() for key in input
                }

    def __hash__(self) -> int:
        return hash((x, y) for x, y in self._mapping.items())

    def __add__(
        self,
        other: "KeyInputState | Key | Iterable[Key | KeyInputState] | KeySet",
    ):
        """
        Combines two keys into a `KeySet`, an unordered collection of keys.
        """
        from keyweave.key_types import KeySet

        match other:
            case KeyInputState():
                return KeySet(self._mapping | {other.key: other})
            case KeySet():
                return KeySet(self._mapping | other._mapping)
            case _:
                raise TypeError(f"Invalid key input: {other}")

    def __bool__(self) -> bool:
        return bool(self._mapping)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, KeySet) and self._mapping == other._mapping

    def __lt__(self, other: "KeySet") -> bool:
        if self._mapping.keys() != other._mapping.keys():
            return self._mapping.keys() < other._mapping.keys()
        ordered_keys = sorted(self._mapping.keys())
        for key in ordered_keys:
            if self._mapping[key] != other._mapping[key]:
                return self._mapping[key] < other._mapping[key]
        return False

    @property
    def specificity(self) -> int:
        return sum(key.specificity for key in self._mapping)

    def __iter__(self):
        return iter(self._mapping.values())

    def __contains__(self, key: Key | KeyInputState) -> bool:
        return self._mapping[key.__keystate__().key] == key.__keystate__()

    def __len__(self) -> int:
        return len(self._mapping)

    def __repr__(self) -> str:
        if not self._mapping:
            return ""
        joined = " + ".join(repr(key) for key in self._mapping)
        return joined

    def __str__(self) -> str:
        if not self._mapping:
            return "[]"
        joined = ", ".join(str(key) for key in self._mapping.values())
        return f"{{{joined}}}"
