import threading
from typing import Any
from keyweave.bindings import KeyBindingCollection
from keyweave.hotkey import InputEvent
from keyweave.key_types import Key, KeyInputState, KeySet
from keyboard import KeyboardEvent, hook_key, is_pressed, unhook

from keyweave._util.logging import keyweaveLogger

from keyweave.scheduling import Scheduler
from keyweave.util.input import get_keyboard_hook_id, is_key_pressed

keyweaveHookLogger = keyweaveLogger


class KeyHook:
    _internal_handler: Any
    _lock = threading.Lock()

    @property
    def _logger(self):
        return keyweaveHookLogger

    def __init__(
        self,
        key: Key,
        collection: KeyBindingCollection,
        scheduler: Scheduler,
    ):
        self.trigger = key
        self._collection = collection
        self._scheduler = scheduler
        self.manufactured_handler = self._get_handler()

    def __enter__(self):
        self._logger.info("Installing hook for %s", self.trigger)
        self._internal_handler = hook_key(
            get_keyboard_hook_id(self.trigger.id),
            self.manufactured_handler,
            suppress=True,
        )
        return self

    def __exit__(self):
        unhook(self._internal_handler)
        return self

    def _get_handler(self):
        def get_best_binding(event: KeyboardEvent):
            only_matching = [
                binding
                for binding in self._collection
                if binding.hotkey.trigger.key.is_numpad == event.is_keypad
                and _is_key_set_active(binding.hotkey.modifiers)
                and event.event_type == binding.hotkey.trigger.state
            ]

            by_specificity = sorted(
                only_matching,
                key=lambda binding: binding.hotkey.specificity,
                reverse=True,
            )
            return by_specificity[0] if by_specificity else None

        def handler(info: KeyboardEvent):
            binding = get_best_binding(info)
            event_state = _state_from_event(info)
            if not binding:
                return True
            self._logger.debug(f"RECEIVED {event_state}; MATCHED {binding}")

            def binding_invoker():
                return binding(InputEvent(info.time))

            self._scheduler(binding_invoker)
            return False

        return handler


def _is_state_active(state: KeyInputState):
    match state.state:
        case "down":
            return is_key_pressed(state.key.id)
        case "up":
            return not is_key_pressed(state.key.id)
        case _:
            raise ValueError(f"Unknown key state: {state.state}")


def _is_key_set_active(key_set: KeySet):
    return all(_is_state_active(key_state) for key_state in key_set)


def _state_from_event(event: KeyboardEvent) -> KeyInputState:
    return KeyInputState(
        key=Key(event.name or ""), state=event.event_type or "down"
    )
