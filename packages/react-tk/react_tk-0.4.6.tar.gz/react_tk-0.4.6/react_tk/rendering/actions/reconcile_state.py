from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from react_tk.renderable.node.prop_value_accessor import PropValuesAccessor
from react_tk.renderable.node.shadow_node import ShadowNode, ShadowNodeInfo
from react_tk.renderable.trace import RenderTrace, RenderTraceAccessor
from react_tk.tk.widget_data import WidgetNode

if TYPE_CHECKING:
    from react_tk.rendering.actions.compute import AnyNode


@dataclass
class RenderedNode[Res]:
    resource: Res
    node: ShadowNode[Any]

    def __post_init__(self):
        WidgetNode(self.resource).set(self.node)

    def __str__(self) -> str:
        return f"®️ {str(self.node)}"

    def __repr__(self) -> str:
        return str(self)

    @property
    def TRACE(self) -> RenderTrace:
        return RenderTraceAccessor(self.node).get()

    def migrate(self, node: "AnyNode"):
        self.node = node
        WidgetNode(self.resource).set(node)
        return self


@dataclass
class PersistentReconcileState:
    existing_resources: dict[str, RenderedNode] = field(default_factory=dict)
    placed_last: set[str] = field(default_factory=set)

    def overwrite(self, rendered: RenderedNode) -> None:
        self.existing_resources[rendered.node.__info__.uid] = rendered
        self.placed_last.add(rendered.node.__info__.uid)

    def was_last_placed(self, node: ShadowNode[Any]) -> bool:
        return node.__info__.uid in self.placed_last

    def new_transient(self) -> "TransientReconcileState":
        return TransientReconcileState(
            existing_resources=self.existing_resources,
            placed_last=self.placed_last,
        )

    def from_transient(self, transient: "TransientReconcileState") -> None:
        self.existing_resources = transient.existing_resources
        self.placed_last = transient.being_placed

    def __getitem__(self, node: ShadowNode[Any]) -> RenderedNode:
        return self.existing_resources[node.__info__.uid]

    def get(self, node: ShadowNode[Any]) -> RenderedNode | None:
        return self.existing_resources.get(node.__info__.uid, None)


@dataclass
class TransientReconcileState(PersistentReconcileState):
    being_placed: set[str] = field(default_factory=set)

    def will_be_placed(self, node: ShadowNode[Any]) -> bool:
        return node.__info__.uid in self.being_placed
