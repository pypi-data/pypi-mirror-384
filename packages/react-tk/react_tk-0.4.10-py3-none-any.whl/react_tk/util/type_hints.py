import sys
from typing import Callable, Mapping, get_type_hints
from react_tk.util.core_reflection import get_mro_up_to, type_reference


def _collect_raw_annotations(classes: list[type]) -> dict[str, object]:
    """Collect raw __annotations__ from the given classes.

    Later classes in the list override earlier ones (so subclasses override
    bases when classes is in MRO order).
    """
    collected: dict[str, object] = {}
    for kls in reversed(classes):
        collected.update(dict(kls.__dict__.get("__annotations__", {})))
    return collected


def _build_localns(
    classes: list[type], defaults: Mapping[str, object]
) -> dict[str, object]:
    """Build a local namespace by merging class dicts in MRO order.

    This makes names defined on subclasses available and allows forward refs
    declared in class bodies to resolve against those dicts.
    """
    localns: dict[str, object] = {}
    localns.update(defaults)
    for kls in classes:
        localns.update(vars(kls))

    return localns


def _build_globalns(cls: type) -> dict[str, object]:
    """Return module globals for the module that defines cls, or empty dict."""
    module = sys.modules.get(getattr(cls, "__module__", ""), None)
    return vars(module) if module is not None else {}


def _get_fake(annotations: dict[str, object]) -> Callable[[], None]:
    def _fake() -> None: ...

    _fake.__annotations__ = annotations
    return _fake


def get_type_hints_up_to(
    cls: type, tops: tuple[type_reference, ...], **defaults: object
) -> dict[str, object]:
    """Collect and evaluate annotations declared on `cls` (optionally up to `top`).

    This function composes the smaller helpers above to assemble the raw
    annotations and namespaces before delegating to typing.get_type_hints for
    evaluation.
    """
    classes = get_mro_up_to(cls, tops)
    collected_raw = _collect_raw_annotations(classes)
    if not collected_raw:
        return {}

    globalns = _build_globalns(cls)
    localns = _build_localns(classes, defaults)

    fake = _get_fake(collected_raw)
    # Let get_type_hints raise exceptions to the caller so unresolved or
    # failing evaluations surface immediately.
    return get_type_hints(fake, globalns=globalns, localns=localns, include_extras=True)
