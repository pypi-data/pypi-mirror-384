from operator import is_
from typing import Any
from keyboard import is_pressed as kb_is_pressed


def _get_windows_id_for_mouse_key(key_id: str) -> int:
    return int(key_id.replace("mouse:", ""))


def _get_mouse_id_for_mouse_key(key_id: str) -> str:
    from mouse import LEFT, RIGHT, X, X2, MIDDLE  # type: ignore

    match key_id:
        case "mouse:1":
            return LEFT
        case "mouse:2":
            return RIGHT
        case "mouse:3":
            return MIDDLE
        case "mouse:4":
            return X
        case "mouse:5":
            return X2
        case _:
            raise ValueError("Key is not a recognized mouse key")


def _is_mouse_pressed_win32(key_id: str):
    from win32api import GetAsyncKeyState  # type: ignore

    id = _get_windows_id_for_mouse_key(key_id)
    pr: Any = GetAsyncKeyState(id) & 0x8000
    return pr


def _is_mouse_pressed_mouse(key_id: str):
    from mouse import is_pressed  # type: ignore

    mouse_id = _get_mouse_id_for_mouse_key(key_id)
    return is_pressed(mouse_id)


def _is_mouse_pressed(key_id: str):
    try:
        return _is_mouse_pressed_win32(key_id)
    except ImportError:
        return _is_mouse_pressed_mouse(key_id)


def _is_keyboard_pressed(key_id: str):
    hook_id = get_keyboard_hook_id(key_id)
    return kb_is_pressed(hook_id)


def is_key_pressed(key: str):
    if key.startswith("mouse:"):
        return _is_mouse_pressed(key)
    else:
        return _is_keyboard_pressed(key)


def get_keyboard_hook_id(key_id: str) -> str:
    match key_id:
        case "num:enter":
            return "enter"
        case "num:dot" | "num:.":
            return "."
        case "num:star" | "num:*" | "num:multiply":
            return "*"
        case "num:plus" | "num:+":
            return "+"
        case "num:minus" | "num:-":
            return "-"
        case "num:slash" | "num:/":
            return "/"
        case "mouse:1":
            return "left"
        case "mouse:2":
            return "right"
        case "mouse:3":
            return "middlemouse"
        case "mouse:4":
            return "x"
        case "mouse:5":
            return "x2"
        case _:
            return key_id.replace("num:", "num ")
