from asyncio import AbstractEventLoop
from collections.abc import Callable
from copy import copy
from dataclasses import dataclass, field
from logging import getLogger
from operator import methodcaller
from typing import Any, Callable, TypeVar, ParamSpec
from react_tk.util.async_loop import create_event_loop

logger = getLogger("react_tk")


class _bind_schedule(type):

    def __get__(
        self, instance: "Scheduler | None", owner: "type[Scheduler]"
    ) -> "type[_schedule]":
        if not instance:
            return self  # type: ignore[return-value]

        class bound_schedule(_schedule):
            parent = instance

        return bound_schedule


@dataclass(kw_only=True)
class ScheduleInfo:
    delay: float
    always_run: bool = False
    name: str | None = None


@dataclass(kw_only=True)
class _schedule(ScheduleInfo, metaclass=_bind_schedule):
    parent: "Scheduler" = field(
        init=False,
        repr=False,
    )

    def fqn(self, f: Callable) -> str:
        schedule_name = self.name or "schedule"
        return f"{schedule_name}({f.__name__})"

    def __call__[**P](
        self, func: Callable[P, None], *args: P.args, **kwargs: P.kwargs
    ) -> Callable[[], None]:
        orig_state = copy(self.parent)
        fqn = self.fqn(func)

        def _wrapped():
            if orig_state == self.parent:
                logger.debug("Running [%s]", fqn)
                return func(*args, **kwargs)
            elif self.always_run:
                logger.warning("Force running [%s] in spite of context change", fqn)
                return func(*args, **kwargs)
            else:
                logger.debug("Skipping [%s] due to context change", fqn)

        self.parent._loop.call_soon_threadsafe(
            self.parent._loop.call_later, self.delay, _wrapped
        )
        return _wrapped


class Scheduler:
    _loop: AbstractEventLoop

    def __init__(self, trace_name: str) -> None:
        self._loop = create_event_loop(trace_name)

    class schedule(_schedule):
        pass
