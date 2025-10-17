from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
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
from react_tk.renderable.node.prop_value_accessor import PropValuesAccessor
from react_tk.props.annotations.prop_meta import prop_meta, schema_meta

if TYPE_CHECKING:
    from react_tk.props.impl.prop import Prop_Schema, Prop_Mapping
    from react_tk.props.impl.common import KeyedValues
    from react_tk.props.annotations.prop_meta import some_meta
    from react_tk.renderable.component import Component
    from react_tk.renderable.node.shadow_node import ShadowNode


class _HasMerge(Protocol):
    def __post_init__(self) -> None:
        pass

    def __merge__(self, other: "KeyedValues") -> Self: ...


@dataclass
class MethodSetterTransformer:
    @property
    @abstractmethod
    def self_meta(self) -> "some_meta": ...

    def _transform(self, f: Callable) -> Callable:
        def __init__(self: _HasMerge, *args, **kwargs: Any) -> None:
            result = self.__merge__(kwargs)
            PropValuesAccessor(self).set_from(result)
            self.__post_init__()

            return None

        if f.__name__ == "__init__":
            return __init__

        def wrapper(self: _HasMerge, **kwargs: Any) -> Any:
            return self.__merge__({f.__name__: kwargs})

        return wrapper

    @overload
    def __call__[**P, R: _HasMerge](
        self, f: Callable[Concatenate[R, P], None]
    ) -> Callable[Concatenate[R, P], R]: ...

    @overload
    def __call__[**P, R: _HasMerge](
        self,
    ) -> Callable[
        [Callable[Concatenate[R, P], Any]], Callable[Concatenate[R, P], R]
    ]: ...

    def __call__(self, f: Callable[..., Any] | None = None) -> Any:

        def apply(f: Callable) -> Any:
            transformed = self._transform(f)
            # perform runtime imports here to avoid circular imports at module import time
            from react_tk.reflect.reader.type import OrigAccessor
            from react_tk.props.annotations.create_props import MetaAccessor

            OrigAccessor(transformed).set(f)
            MetaAccessor(f).set(self.self_meta)
            return transformed

        return apply(f) if f else apply


@dataclass(kw_only=True)
class schema_setter(MethodSetterTransformer, schema_meta):
    @property
    def self_meta(self) -> Any:
        return self


@dataclass(kw_only=True)
class prop_setter(MethodSetterTransformer, prop_meta):
    @property
    def self_meta(self) -> Any:
        return self


@dataclass
class _getter[X]:
    prop_name: str

    def __get__(self, instance: Any, owner) -> X:
        if instance is None:
            return self  # type: ignore
        v = instance.__PROP_VALUES__[self.prop_name].compute()
        return v  # type: ignore


@dataclass
class prop_getter:
    name: str | None = field(default=None)

    def __call__[R](self, f: Callable[[Any], R]):
        prop_name = self.name or f.__name__

        return _getter[R](prop_name)


class HasChildren[Kids: "ShadowNode[Any]"](_HasMerge):

    def __getitem__(
        self, children: "Kids | Component[Kids] | tuple[Kids | Component[Kids], ...]"
    ) -> Self:
        return self.__merge__({"KIDS": children})
