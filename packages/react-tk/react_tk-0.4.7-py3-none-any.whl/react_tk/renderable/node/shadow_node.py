from abc import ABC, abstractmethod
from collections.abc import Mapping
from copy import copy
from dataclasses import dataclass, is_dataclass
from inspect import isabstract
from pyclbr import Class
import sys
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Iterable,
    Never,
    NotRequired,
    Protocol,
    Required,
    Self,
    TypedDict,
    Unpack,
)

from expression import Some
from react_tk.props.impl import prop
from react_tk.renderable.node.prop_value_accessor import (
    PropValuesAccessor,
    PropsAccessor,
)
from react_tk.renderable.renderable_base import RenderableBase
from react_tk.renderable.trace import (
    ConstructTraceAccessor,
    RenderFrame,
    RenderTrace,
    RenderTraceAccessor,
)
from react_tk.props.annotations.prop_meta import prop_meta
from react_tk.props.annotations.decorators import HasChildren, prop_getter
from react_tk.props.annotations.create_props import (
    read_props_from_top_class,
)
from react_tk.props.impl.common import KeyedValues
from react_tk.props.impl.prop import Prop_Mapping
from react_tk.util.stack import ReactTkFrameInfo

if TYPE_CHECKING:
    from react_tk.rendering.actions.node_reconciler import ReconcilerBase


class HasPropsSchema:

    def __init_subclass__(cls) -> None:
        if isabstract(cls):
            return

        props_block = read_props_from_top_class(cls)
        PropsAccessor(cls).set(props_block)

    def __merge__(self, input_values: KeyedValues = {}, **kwargs: Any) -> Self:
        input_values = {
            **input_values,
            **kwargs,
        }
        schema = PropsAccessor(self).get()
        values = PropValuesAccessor(self)
        if not values:
            pbv = Prop_Mapping(prop=schema, value=input_values, old=None)
            values = pbv
        else:
            values = values.get().merge(input_values)
        clone = copy(self)
        PropValuesAccessor(clone).set(values)
        return clone


class NodeProps(TypedDict):
    key: Annotated[NotRequired[str], prop_meta(no_value=Some(None))]
    KIDS: Annotated[NotRequired[Iterable[Any]], prop_meta(no_value=(), diff="never")]


@dataclass
class ShadowNodeInfo:
    class_name: str
    reconciler_name: str
    custom_key: str
    trace: RenderTrace
    ctor_trace: ReactTkFrameInfo

    @property
    def short_id(self) -> str:
        return self.trace.to_string("short-id")

    @property
    def uid(self) -> str:
        return self.trace.to_string("id")

    @classmethod
    def from_node(cls, node: "ShadowNode[Any]") -> "ShadowNodeInfo":
        from react_tk.rendering.actions.node_reconciler import ReconcilerAccessor

        trace = RenderTraceAccessor(node).get()
        ctor_trace = ConstructTraceAccessor(node).get()
        reconciler = ReconcilerAccessor(node).get()
        return cls(
            class_name=node.__class__.__name__,
            reconciler_name=reconciler.__name__,
            custom_key=node.key or "",
            ctor_trace=ctor_trace,
            trace=trace,
        )


class ShadowNode[Kids: ShadowNode[Any] = Never](
    RenderableBase, HasPropsSchema, HasChildren[Kids], ABC
):
    def __repr__(self) -> str:
        return str(self)

    @property
    def PROPS(self) -> Prop_Mapping:
        return PropValuesAccessor(self).get()

    @PROPS.setter
    def PROPS(self, value: Prop_Mapping) -> None:
        PropValuesAccessor(self).set(value)

    @prop_getter()
    def KIDS(self) -> Iterable["ShadowNode[Any]"]: ...

    @prop_getter()
    def key(self) -> str: ...

    @property
    def __info__(self) -> ShadowNodeInfo:
        return ShadowNodeInfo.from_node(self)

    def __str__(self) -> str:
        info = ShadowNodeInfo.from_node(self)
        return f"{info.short_id}"
