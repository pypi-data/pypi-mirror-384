from collections import defaultdict
from dataclasses import dataclass, field
from inspect import FrameInfo
import sys
from typing import Any, Callable, ClassVar, Generator, Iterable, Optional

from react_tk.renderable.node.shadow_node import ShadowNode
from react_tk.renderable.context import Ctx

from react_tk.renderable.node.top import TopLevelNode
from react_tk.renderable.trace import RenderFrame
from react_tk.renderable.trace import RenderTrace, RenderTraceAccessor
from react_tk.rendering.actions.actions import (
    ReconcileAction,
)
from react_tk.rendering.actions.compute import (
    AnyNode,
    ComputeTreeActions,
)
from react_tk.rendering.actions.node_reconciler import (
    ReconcilerBase,
    ReconcilerAccessor,
)
from react_tk.rendering.actions.reconcile_state import (
    PersistentReconcileState,
    RenderedNode,
    TransientReconcileState,
)
from react_tk.renderable.component import Component


def _with_trace(node: ShadowNode[Any], trace: RenderTrace) -> ShadowNode[Any]:
    return RenderTraceAccessor(node).set(trace) or node


@dataclass
class RootReconciler[Node: ShadowNode[Any] = ShadowNode[Any]]:
    state: PersistentReconcileState = field(
        default_factory=lambda: PersistentReconcileState(existing_resources={})
    )

    def _compute_actions(self, transient_state: TransientReconcileState, root):
        for x in ComputeTreeActions(transient_state).compute_actions(root):
            yield x

    def reconcile(self, nodes: tuple[ShadowNode[Any], ...]):
        top_level_fake = TopLevelNode(KIDS=nodes, key="top")

        transient_state = self.state.new_transient()
        actions = [*self._compute_actions(transient_state, top_level_fake)]
        self.state.overwrite(RenderedNode(object(), top_level_fake))

        for action in actions:
            Reconciler = ReconcilerAccessor(action.node).get()
            reconciler = Reconciler.create(transient_state)
            if not reconciler:
                raise ValueError(
                    f"No reconciler found for action type {type(action.node)}"
                )
            reconciler.run_action(action)
        self.state.from_transient(transient_state)
