import inspect
from typing import Any, Callable


def get_attrs_down_to(
    target: object,
    base: type,
    *,
    resolve_descriptor: Callable[[Any], bool] = lambda _: True
):
    attrs = dict[str, object]()
    for cls in target.__class__.mro():
        if cls is base:
            break
        for key, value in cls.__dict__.items():
            if key not in attrs:
                attrs[key] = (
                    getattr(target, key) if resolve_descriptor(value) else value
                )

    return attrs


def clean_method_name(func: Callable[..., Any]) -> str:
    if hasattr(func, "__func__"):
        func = func.__func__  # type: ignore
    return func.__name__.lstrip("_")


def is_unbound_method(func: Callable[..., Any]) -> bool:
    return (
        inspect.isfunction(func)
        and "." in func.__qualname__
        and "self" in inspect.signature(func).parameters
    )


def get_self_dict_restricted(target: object, base: type) -> dict[str, Any]:
    """
    Get the __dict__ of an instance, but only including attributes defined in the instance's class and its subclasses down to (but not including) the specified base class.

    Args:
        target (object): The instance whose __dict__ is to be retrieved.
        base (type): The base class to stop at (not inclusive).

    Returns:
        dict[str, Any]: A dictionary containing the attributes of the instance.
    """
    return {
        k: v for k, v in target.__dict__.items() if k in base.__annotations__
    }
