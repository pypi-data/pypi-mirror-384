import os
import re
from typing import Any, override
from yaml import Dumper, SafeDumper, dump, safe_dump
from yaml.nodes import ScalarNode as ScalarNode

from keyweave.print.escape import UnicodeEncoder

encoder = UnicodeEncoder()


type NestedStrDict = dict[str, str | NestedStrDict]


class BlockStrDumper(Dumper):
    @override
    def represent_scalar(
        self, tag: str, value: Any, style: str | None = None
    ) -> ScalarNode:
        if isinstance(value, str) and value.startswith("_NL_"):
            value = value.replace("_NL_", "", 1)
            if len(value) > 35 and not value.endswith("\n"):
                style = ">"
                value += "\n"
        return super().represent_scalar(tag, value, style)  # type: ignore[return-value]


def _print_pure_yaml(target: NestedStrDict) -> str:
    return dump(
        target,
        width=45,
        sort_keys=False,
        indent=2,
        allow_unicode=True,
        Dumper=BlockStrDumper,
    )


def _escape_dict_values(d: NestedStrDict) -> NestedStrDict:
    result: NestedStrDict = {}
    for k, v in d.items():
        k = encoder.to_(k)
        if isinstance(v, dict):
            result[k] = _escape_dict_values(v)
        else:
            result[k] = encoder.to_(v)
    return result


def _unescape_yaml_text(s: str) -> str:
    return encoder.from_(s)


def render_yaml(target: NestedStrDict) -> str:
    target = _escape_dict_values(target)
    printed = _print_pure_yaml(target)
    printed = _unescape_yaml_text(printed)
    return printed
