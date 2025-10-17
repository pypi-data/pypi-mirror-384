from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from sre_constants import ANY
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    NotRequired,
    Protocol,
    Self,
    Tuple,
    TypeIs,
    overload,
)

from react_tk.renderable.node.shadow_node import NodeProps, ShadowNode
from react_tk.renderable.renderable_base import RenderableBase


type RenderElement[Node: ShadowNode[Any]] = Node | Component[Node]
type RenderResult[Node: ShadowNode[Any] = ShadowNode[Any]] = RenderElement[
    Node
] | Iterable[RenderElement[Node]]


class AbsCtx:
    def __getattr__(self, item: str) -> Any: ...
    def __setattr__(self, key: str, value: Any) -> None: ...


class AbsSink[Node: ShadowNode[Any] = ShadowNode[Any]](Protocol):
    @property
    @abstractmethod
    def ctx(self) -> AbsCtx: ...

    def run(self, node: RenderResult[Node], /) -> tuple[Node, ...]: ...


@dataclass(kw_only=True)
class Component[Node: ShadowNode[Any] = ShadowNode[Any]](RenderableBase):
    key: str = field(default="")
    ctx: AbsCtx = field(init=False)

    @abstractmethod
    def render(self, /) -> "RenderResult[Node]": ...


class is_render_element[T: ShadowNode[Any]]:  # type: ignore
    def __new__(cls, obj: Any) -> TypeIs[RenderElement[T]]:
        return isinstance(obj, (ShadowNode, Component))  # type: ignore
