from abc import ABC, abstractclassmethod, abstractmethod
from collections.abc import Mapping
from typing import Any, ClassVar, Iterable, Iterator, Optional, Self, Tuple, TypeVar


class VMappingBase[K, V](ABC, Iterable[V]):
    type Input = Iterable[V] | Mapping[K, V]
    """A mapping-like container that is iterable over its value objects.

    - Does NOT subclass collections.abc.Mapping on purpose.
    - Values are expected to carry the key as an attribute named by `_KEY_ATTR`.
    - Subclasses must set `_KEY_ATTR` via `__init_subclass__(key_attr=...)`.

    The constructor accepts either an iterable of V or another VMapping[K, V].
    Internally values are stored in a plain dict mapping keys to values.
    """

    @abstractmethod
    def __iter__(self) -> Iterator[V]: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def __getitem__(self, key: K) -> V: ...

    @abstractmethod
    def _get_key(self, value: V) -> K: ...

    def _to_dict(self, values: Input) -> dict[K, V]:
        """Convert an iterable of values or a mapping to a plain mapping."""
        match values:
            case Mapping() as m:
                return dict(m)  # type: ignore[return-value]
            case _:
                return {self._get_key(v): v for v in values}

    def __contains__(self, key: Any) -> bool:
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> Iterable[K]:
        for x in self:
            yield self._get_key(x)

    def items(self) -> Iterable[Tuple[K, V]]:
        for x in self:
            yield self._get_key(x), x

    def values(self) -> Iterable[V]:
        return iter(self)

    def __repr__(self) -> str:  # pragma: no cover - simple convenience
        cls = type(self).__name__
        return f"{cls}({list(self)!r})"
