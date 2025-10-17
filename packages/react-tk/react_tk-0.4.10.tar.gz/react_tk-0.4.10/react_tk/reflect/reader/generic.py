from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from react_tk.reflect.accessor.type import (
    ArgsAccessor,
    MetadataAccessor,
    TypeParamsAccessor,
)
from collections.abc import Iterable, Iterator
from react_tk.reflect.reader.base import Reader_Base
from itertools import zip_longest


from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Literal,
    NoDefault,
    TypeIs,
    TypeVar,
    get_origin,
)

# Import readers at module load time. `readers.py` only imports
# from `generic_reader` under TYPE_CHECKING or lazily, so this
# does not create a circular import at runtime.
if TYPE_CHECKING:
    from react_tk.reflect.reader.type import Reader_Annotation, Reader_Class
    from react_tk.reflect.reflector import Reflector


@dataclass(repr=False)
class _Base_Reader_TypeVar(Reader_Base, ABC):
    target: TypeVar
    is_undeclared: bool = field(default=False, kw_only=True)

    def is_similar_to(self, other: _Base_Reader_TypeVar) -> bool:
        if not isinstance(other, _Base_Reader_TypeVar):
            return False
        # check structural equivalence of underlying TypeVar
        return (
            self.name == other.name
            and self.is_undeclared == other.is_undeclared
            and self.lower_bound == other.lower_bound
            and self.constraints == other.constraints
            and self.default == other.default
        )

    @property
    def name(self) -> str:
        return self.target.__name__

    @property
    def lower_bound(self) -> Reader_Annotation | None:
        if self.target.__bound__ is None:
            return None
        return self.reflector.annotation(self.target.__bound__)

    @property
    def constraints(self) -> tuple[Reader_Annotation, ...]:
        return tuple(self.reflector.annotation(x) for x in self.target.__constraints__)

    @property
    def default(self) -> Reader_Annotation | None:
        if self.target.__default__ is None:
            return None
        if self.target.__default__ is NoDefault:
            return None
        return self.reflector.annotation(self.target.__default__)

    @property
    def _text(self) -> str:
        # Format: {Name}: {Bound.Name} = {Default.Name}
        name = self.name
        parts = [name]
        b = self.lower_bound

        if b is not None:
            parts.append(f": {b._text}")

        d = self.default
        if d is not None:
            parts.append(f" = {d._text}")
        return "".join(parts)


@dataclass(eq=True, unsafe_hash=True, repr=False)
class Reader_TypeVar(_Base_Reader_TypeVar):

    @property
    def value(self) -> Reader_Annotation:
        raise TypeError(f"TypeVar {self} is not bound to a value")

    def with_value(self, value: Any, *, is_defaulted=False) -> Reader_BoundTypeVar:
        return Reader_BoundTypeVar(
            target=self.target,
            reflector=self.reflector,
            value=self.reflector.annotation(value),
            is_undeclared=self.is_undeclared,
            is_defaulted=is_defaulted,
        )


@dataclass(eq=True, unsafe_hash=True, repr=False)
class Reader_BoundTypeVar(_Base_Reader_TypeVar):
    value: Reader_Annotation
    is_defaulted: bool

    def is_similar_to(self, other: _Base_Reader_TypeVar) -> bool:
        if isinstance(other, Reader_BoundTypeVar):
            return (
                super().is_similar_to(other)
                and self.value == other.value
                and self.is_defaulted == other.is_defaulted
            )
        return False

    @property
    def _text(self) -> str:
        # Use the base representation, drop everything at/after '=' and trim,
        # then denote the bound value with the ≡ symbol.
        base = super()._text
        if "=" in base:
            left = base.split("=", 1)[0].strip()
        else:
            left = base.strip()
        return f"{left} ≡ {self.value._text.strip()}"


# Union type for readers that may be bound or unbound
SomeTypeVarReader = Reader_TypeVar | Reader_BoundTypeVar


@dataclass(eq=True, unsafe_hash=True, repr=False)
class Reader_Generic(Reader_Base, Iterable[SomeTypeVarReader]):
    """Read the generic signature for a class or a parameterized generic alias.

    This reader will produce either `TypeVarReader` (unbound) or
    `BoundTypeVarReader` (bound) for each declared type-variable on the
    origin. It accepts either a plain class (no args) or a parameterized
    alias; use :attr:`is_all_bound` to check whether every type-var has a
    bound value (from args or defaults).
    """

    def __post_init__(self) -> None:
        target = self.target
        # replace the in-place reader construction with the helper call
        self._readers = self.reflector._get_generic_signature(target)
        self._by_name = {r.name: r for r in self._readers}

    def __bool__(self) -> bool:
        """Truthiness indicates whether this signature contains any type vars."""
        return bool(self._readers)

    def __iter__(self) -> Iterator[SomeTypeVarReader]:
        return iter(self._readers)

    @property
    def _text(self) -> str:
        origin_name = self.origin.name if self.origin else "?"
        return f"{origin_name}[{', '.join(r._text for r in self._readers)}]"

    @property
    def annotation(self) -> "Reader_Annotation":
        return self.reflector.annotation(self.target)

    @property
    def origin(self) -> Reader_Annotation | None:
        return self.annotation.origin

    @property
    def is_all_bound(self) -> bool:
        return all(isinstance(r, Reader_BoundTypeVar) for r in self._readers)

    def __getitem__(self, key: int | str) -> "SomeTypeVarReader":
        match key:
            case int():
                return self._readers[key]
            case str():
                return self._by_name[key]
            case _:
                raise KeyError(key) from None

    def __len__(self) -> int:
        return len(self._readers)

    def __contains__(self, key: int | str) -> bool:
        match key:
            case int():
                return 0 <= key < len(self._readers)
            case str():
                return key in self._by_name
        return False


def is_bound(tv: _Base_Reader_TypeVar) -> TypeIs[Reader_BoundTypeVar]:
    return isinstance(tv, Reader_BoundTypeVar)


def is_not_bound(tv: _Base_Reader_TypeVar) -> TypeIs[Reader_TypeVar]:
    return isinstance(tv, Reader_TypeVar)
