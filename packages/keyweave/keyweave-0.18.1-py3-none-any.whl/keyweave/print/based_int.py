# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
from baseconv import BaseConverter

converter = BaseConverter(
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
)


class BasedInt(int):
    """Integer-like object represented in the project's custom base.

    Construction:
    - BasedInt(int_or_str)
      If given a str, it is decoded using the module-level `converter`.
      If given an int (or something int()-able), it is used as-is.

    Implementation note:
    This subclasses ``int`` so it automatically supports all standard
    integer operations. ``__str__``/``__repr__`` are overridden to emit
    the base-converted representation.
    """

    def __new__(cls, value: 'int | str | "BasedInt"' = 0) -> "BasedInt":
        # If already a BasedInt, return it unchanged
        if isinstance(value, BasedInt):
            return value

        # Parse strings via the converter (handle optional leading '-')
        if isinstance(value, str):
            s = value
            if s.startswith("-"):
                val = -int(converter.decode(s[1:]))
            else:
                val = int(converter.decode(s))
        else:
            # coerce other numeric types to int
            val = int(value)

        return int.__new__(cls, val)

    def __str__(self) -> str:  # emit converted representation
        v = int(self)
        if v < 0:
            return "-" + converter.encode(-v)
        return converter.encode(v)

    def __repr__(self) -> str:  # same as __str__, per requirement
        return self.__str__()
