from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def deep_merge(a: Mapping, b: Mapping) -> dict:
    """
    Recursively merge two mappings.
    Values from *b* overwrite or merge into *a*.
    Returns a new dict; neither input is modified.
    """
    merged = dict(a)  # shallow copy of the left operand
    for key, b_val in b.items():
        a_val = merged.get(key)
        if isinstance(a_val, Mapping) and isinstance(b_val, Mapping):
            merged[key] = deep_merge(a_val, b_val)
        else:
            merged[key] = b_val
    return merged


def deep_copy(d: Mapping) -> dict:
    result = {}
    for key, value in d.items():
        if isinstance(value, Mapping):
            result[key] = deep_copy(value)
        else:
            result[key] = value
    return result


def set_path(d: Mapping[str, Any], path: str, value: Any) -> dict:
    """
    Set a value in a nested dictionary at the specified path.
    Creates intermediate dictionaries as needed.
    Returns the modified dictionary.
    """
    keys = path.split(".")
    current = deep_copy(d)
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
    return current


def deep_diff(existing: Mapping, newer: Mapping) -> dict:
    """
    Recursively compute the difference between two mappings.
    Returns a new dict containing keys and values from *a* that are different from *b*.
    If a value is a mapping in both *a* and *b*, the difference is computed recursively.
    """
    diff = {}
    for key, existing_v in existing.items():
        newer_v = newer.get(key)
        if isinstance(existing_v, Mapping) and isinstance(newer_v, Mapping):
            nested_diff = deep_diff(existing_v, newer_v)
            if nested_diff:  # only include if there are differences
                diff[key] = nested_diff
        elif existing_v != newer_v:
            diff[key] = newer_v
    return diff


def dict_equal(a: Mapping, b: Mapping) -> bool:
    """
    Recursively compare two mappings for equality.
    """
    if a.keys() != b.keys():
        return False
    for key in a.keys():
        a_val = a[key]
        b_val = b[key]
        if isinstance(a_val, Mapping) and isinstance(b_val, Mapping):
            if not dict_equal(a_val, b_val):
                return False
        else:
            if a_val != b_val:
                return False
    return True


def get_dict_one_line(d: Mapping) -> str:
    items = []
    for key, value in d.items():
        if isinstance(value, Mapping):
            value_str = get_dict_one_line(value)
        elif value is None:
            continue
        else:
            value_str = repr(value)
        items.append(f"{key}: {value_str}")
    return "{" + ", ".join(items) + "}"
