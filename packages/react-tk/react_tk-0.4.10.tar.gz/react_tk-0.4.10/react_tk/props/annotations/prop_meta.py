from abc import abstractmethod
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Iterable,
    Mapping,
    Protocol,
    Self,
    overload,
)

from expression import Nothing

from react_tk.reflect.reader.type import OrigAccessor
from react_tk.props.impl.common import (
    Converter,
    DiffMode,
    KeyedValues,
)


@dataclass(kw_only=True)
class common_meta:
    metadata: Mapping[str, Any] = field(default=MappingProxyType({}))
    name: str | None = None


@dataclass(kw_only=True)
class prop_meta(common_meta):
    diff: DiffMode = "simple"
    subsection: str | None = None
    no_value: Any = field(default=Nothing)
    converter: Converter[Any] | None = None


@dataclass(kw_only=True)
class schema_meta(common_meta):
    diff: DiffMode = "recursive"


type some_meta = prop_meta | schema_meta
