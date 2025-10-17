from dataclasses import dataclass, field
from logging import getLogger
import threading
import asyncio
from typing import Any, Callable, Self

from expression import Nothing

from react_tk.interaction.scheduler import ScheduleInfo, Scheduler, _bind_schedule
from react_tk.renderable.component import AbsCtx
from react_tk.util.core_reflection import get_attr_skip_hook, has_attr_skip_hook
from react_tk.util.async_loop import create_event_loop

logger = getLogger("react_tk")


@dataclass
class CtxLock:
    _parent: "Ctx"

    def __enter__(self):
        self._parent._frozen = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._parent._frozen = False


# FIXME: Multiple issues, including:
# - Weird mutability
# - No type hints (can it be fixed?)
# - Should have consistent ID
# - Consider coolass API for schedule, like ctx(lambda x: x + 1, 10)
# - Probably do away with setattr and leave getattr
# - Improve context equality mechanism
class Ctx(Scheduler, AbsCtx):
    _listeners: list[Callable[[Self], None]] = []
    _map: dict[str, Any] = {}
    _frozen: bool = False

    def __copy__(self) -> "Ctx":
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        result._map = self._map.copy()
        return result

    def __init__(self, **attrs: Any):
        super().__init__("CtxScheduler")
        self._map = dict[str, Any](attrs)
        self._listeners = []

    def __getattr__(self, name: str) -> Any:
        attr = get_attr_skip_hook(self, name, run_get=name == "scheduler")
        if attr is Nothing:
            return self._map.get(name, None)
        return attr.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Ctx):
            return False
        return self._map == other._map

    def __iadd__(self, listener: Callable[[Self], Any]) -> Self:
        self._listeners.append(listener)
        return self

    def _notify(self) -> None:
        for listener in self._listeners:
            listener(self)

    def _try_set(self, key: str, value: Any) -> None:
        if has_attr_skip_hook(self, key):
            return super().__setattr__(key, value)

        self._map[key] = value

    def __call__(self, *args: Any, **kwargs: Any) -> Self:
        if args and kwargs:
            raise ValueError("Ctx can be called with either args or kwargs, not both")
        for k, v in kwargs.items():
            self._try_set(k, v)
        self._notify()
        return self

    def __setattr__(self, key: str, value: Any) -> None:
        if has_attr_skip_hook(self, key):
            object.__setattr__(self, key, value)
            return

        self._try_set(key, value)
        self._notify()


def ctx_snapshot(ctx: "Ctx") -> "Ctx":
    return Ctx(**ctx._map.copy())


def ctx_freeze(ctx: "Ctx") -> "CtxLock":
    return CtxLock(ctx)
