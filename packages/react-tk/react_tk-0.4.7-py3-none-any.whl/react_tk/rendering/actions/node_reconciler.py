from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Literal

from react_tk.reflect.accessor.base import KeyAccessor
from react_tk.props.impl import prop
from react_tk.renderable.node.shadow_node import ShadowNode
from react_tk.rendering.actions.actions import (
    Compat,
    Create,
    Place,
    ReconcileAction,
    Unplace,
    Update,
)
from react_tk.rendering.actions.reconcile_state import (
    PersistentReconcileState,
    RenderedNode,
    TransientReconcileState,
)

type AnyNode = ShadowNode[ShadowNode[Any]]


from typing import Callable, Iterable, Protocol

logger = getLogger("react_tk")


@dataclass
class ReconcilerBase[Res](ABC):
    state: TransientReconcileState

    def _register(self, node: AnyNode, resource: Res) -> RenderedNode[Res]:
        rendered = RenderedNode(resource, node)
        self.state.existing_resources[node.__info__.uid] = rendered
        return rendered

    @classmethod
    @abstractmethod
    def get_compatibility(cls, older: RenderedNode[Res], newer: AnyNode) -> Compat: ...

    @classmethod
    @abstractmethod
    def create(cls, state: TransientReconcileState) -> "ReconcilerBase[Res]": ...

    @abstractmethod
    def run_action(self, action: ReconcileAction[Res]) -> None: ...


class ReconcilerAccessor(KeyAccessor[type[ReconcilerBase]]):
    @property
    def key(self) -> str:
        return "_reconciler"


reconciler = ReconcilerAccessor.decorate
