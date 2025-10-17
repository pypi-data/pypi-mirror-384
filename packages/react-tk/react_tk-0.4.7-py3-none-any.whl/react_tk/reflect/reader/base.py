from dataclasses import dataclass, field
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from react_tk.reflect.accessor.base import KeyAccessor


if TYPE_CHECKING:
    from react_tk.reflect.reflector import Reflector


@dataclass(repr=False)
class Reader_Base:
    target: Any
    reflector: "Reflector" = field(hash=False, compare=False, repr=False)

    def __call__(self, key_accessor: type[KeyAccessor[Any]]) -> KeyAccessor[Any]:
        return self.access(key_accessor)

    def inner_equals(self, other: object) -> bool:
        if not isinstance(other, Reader_Base):
            return self.target == other
        return self.target == other.target

    @property
    @abstractmethod
    def _text(self) -> str: ...

    def __str__(self) -> str:
        return f"⟪ {self._text} ⟫".replace("typing.", "")

    def __repr__(self) -> str:
        return str(self)

    def access(self, accessor: type[KeyAccessor[Any]]) -> KeyAccessor[Any]:
        return accessor(self.target)


def unpack_reader(x: Any):
    if isinstance(x, Reader_Base):
        return x.target
    return x
