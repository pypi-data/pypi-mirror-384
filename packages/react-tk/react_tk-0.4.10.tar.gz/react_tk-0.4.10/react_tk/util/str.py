from itertools import islice
from typing import Iterable, List, TypeVar, Any
from inspect import signature, _empty
from typing import Callable, get_type_hints


def join_truncate[T](iterable: Iterable[T], n: int, marker: Any = "…") -> str:
    """Return up to n items from iterable as a list. If the iterable contains
    more than n items, append `marker` as the last element.

    Examples:
      truncate([1,2,3,4], 3) -> [1,2,3,"…"]
      truncate(range(2), 5) -> [0,1]
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    it = iter(iterable)
    result: Any = list(islice(it, n))
    # attempt to pull one more item to detect truncation
    try:
        next(it)
    except StopIteration:
        pass
    return ", ".join(result + [marker])


def _type_name(ann: Any) -> str:
    """Return a short readable name for an annotation."""
    if ann is _empty:
        return "Any"
    if ann is Any:
        return "Any"
    if ann is None or ann is type(None):
        return "None"
    if isinstance(ann, str):
        return ann
    # For normal classes/types use their __name__ when available
    if hasattr(ann, "__name__"):
        return getattr(ann, "__name__")
    # Fallback to str() for typing constructs like List[int], Optional[str], etc.
    try:
        return str(ann)
    except Exception:
        return repr(ann)


def format_signature(func: Callable[..., Any]) -> str:
    """Return a string like:
    NAME(arg1: t, arg2: t) -> return_t
    """
    name = getattr(func, "__name__", repr(func))
    hints = get_type_hints(func, include_extras=True)
    sig = signature(func)
    parts = []
    for param in sig.parameters.values():
        pname = param.name
        ann = hints.get(pname, param.annotation)
        ann_str = _type_name(ann if ann is not _empty else Any)
        if param.kind == param.VAR_POSITIONAL:
            pname = "*" + pname
        elif param.kind == param.VAR_KEYWORD:
            pname = "**" + pname
        parts.append(f"{pname}: {ann_str}")

    ret_ann = hints.get("return", sig.return_annotation)
    ret_str = _type_name(ret_ann if ret_ann is not _empty else Any)
    return f"{name}({', '.join(parts)}) -> {ret_str}"


def format_subscript(value: int) -> str:
    subscript_map = {
        "0": "₀",
        "1": "₁",
        "2": "₂",
        "3": "₃",
        "4": "₄",
        "5": "₅",
        "6": "₆",
        "7": "₇",
        "8": "₈",
        "9": "₉",
        "-": "₋",
    }
    strified = str(value)
    result = ""
    for c in strified:
        result += subscript_map[c]
    return result


def format_superscript(value: int) -> str:
    superscript_map = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "-": "⁻",
    }
    strified = str(value)
    result = ""
    for c in strified:
        result += superscript_map[c]
    return result
