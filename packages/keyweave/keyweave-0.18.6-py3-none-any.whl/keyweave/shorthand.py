from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, overload
from termcolor import COLORS, colored

type SimpleCoroutine[R] = Coroutine[Any, Any, R]
