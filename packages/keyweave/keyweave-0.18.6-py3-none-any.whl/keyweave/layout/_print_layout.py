# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownArgumentType=false
from collections.abc import Iterable
from itertools import groupby
import re
from typing import Any
from yaml import Dumper, dump

from keyweave.bindings import Binding
from keyweave.commanding import CommandMeta
from keyweave.key_types import KeyInputState, KeySet
from keyweave.layout._layout import Layout
from termcolor import colored

from textwrap import indent

from keyweave.print.style import style
from keyweave.print.yaml import render_yaml


def _build_dict_from_bindings(bindings: Iterable[Binding]) -> dict[str, Any]:
    result = {}

    @style(color="light_green", styles=["underline", "bold"])
    def trigger_block(key_state: KeyInputState):
        return f"{str(key_state)} &"

    @style(color="light_cyan", styles=["bold"])
    def modifiers_block_key(modifiers: KeySet):
        return f"{' + '.join(str(m) for m in modifiers)}" if modifiers else ""

    @style(color="light_green")
    def command_short(command: CommandMeta):
        return str(command.label)

    @style(color="light_magenta")
    def command_desc(command: CommandMeta):
        parts = []
        if command.emoji:
            parts.append(command.emoji + " ")
        parts.append(command.description or "—")
        return "".join(parts)

    def command_and_description(command: CommandMeta):
        return {command_short(command): f"_NL_{command_desc(command)}"}

    by_trigger = groupby(bindings, lambda b: b.hotkey.trigger)
    result = {}
    for trigger, group in by_trigger:
        trigger_dict = {}
        for binding in group:
            mod_key = modifiers_block_key(binding.hotkey.modifiers)
            cmd_desc = command_and_description(binding.command.info)
            if mod_key:
                trigger_dict[mod_key] = cmd_desc
            else:
                trigger_dict.update(cmd_desc)
        result[trigger_block(trigger)] = trigger_dict
    return result


def print_layout(layout: Layout) -> str:
    layout_dict = _build_dict_from_bindings(layout)
    return render_yaml(layout_dict)


def print_entering_message(layout: Layout) -> None:

    base_style = style(
        color="white",
        styles=[],
        char_style="uppercase",
        on_color="light_green",
    )

    @base_style
    def entering_layout():
        return "➡️  Entering layout: "

    @base_style.altered(char_style="unset", on_color="light_blue")
    def layout_name():
        return f"{layout.name}"

    def get_header():
        return f"{entering_layout()}{layout_name()}"

    heading = get_header()
    layout_str = print_layout(layout)
    layout_str_indented = indent(layout_str, "  ")
    print(heading)
    print(layout_str_indented)
