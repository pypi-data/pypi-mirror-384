from typing import Mapping


def default_dicts[K, V](
    base: Mapping[K, V], *defaults: Mapping[K, V]
) -> dict[K, V]:
    """
    Create a new dictionary by merging a base dictionary with default values.

    Args:
        base (Mapping[K, V]): The base dictionary whose values take precedence.
        defaults (Mapping[K, V]): The default values to use if not present in the base.

    Returns:
        dict[K, V]: A new dictionary containing the merged values.
    """
    result = dict[K, V]()
    for d in reversed(defaults):
        for k, v in d.items():
            if v is not None:
                result[k] = v
    for k, v in base.items():
        if v is not None:
            result[k] = v
    return result


def merge_dicts[K, V](*dicts: Mapping[K, V]) -> dict[K, V]:
    """
    Merge multiple dictionaries into a single dictionary. Later dictionaries take precedence over earlier ones.

    Args:
        *dicts (Mapping[K, V]): The dictionaries to merge.

    Returns:
        dict[K, V]: A new dictionary containing the merged values.
    """
    result = dict[K, V]()
    for d in dicts:
        for k, v in d.items():
            if v is not None:
                result[k] = v
    return result
