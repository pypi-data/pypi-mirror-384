from dataclasses import dataclass
import logging
from sre_constants import ANY
from typing import (
    Any,
    Iterable,
)

from react_tk.renderable.component import Component
from react_tk.renderable.node.prop_value_accessor import PropValuesAccessor
from react_tk.props.impl.prop import Prop
from react_tk.rendering.actions.node_reconciler import Compat
from react_tk.rendering.actions.reconcile_state import (
    PersistentReconcileState,
    TransientReconcileState,
)

from .actions import (
    Create,
    ReconcileAction,
    RenderedNode,
    Replace,
    SubAction,
    Unplace,
    Update,
    Place,
)
from react_tk.renderable.node.shadow_node import ShadowNode


from itertools import groupby, zip_longest

logger = logging.getLogger("react_tk")
type AnyNode = ShadowNode[ShadowNode[Any]]


@dataclass
class _ComputeAction:
    prev: RenderedNode[Any] | None
    next: ShadowNode[Any] | None
    old_next_rendered: RenderedNode[Any] | None
    container: AnyNode
    at: int

    def _get_compatibility(self, older: RenderedNode, newer: AnyNode) -> Compat:
        from react_tk.rendering.actions.node_reconciler import ReconcilerAccessor

        reconciler_class = ReconcilerAccessor(older.node).get()
        return reconciler_class.get_compatibility(older, newer)

    def _diff(self, prev: RenderedNode, next: ShadowNode):
        return PropValuesAccessor(prev.node).get().diff(PropValuesAccessor(next).get())

    def _get_update_or_crate(
        self, target: RenderedNode | None, next: ShadowNode[Any]
    ) -> SubAction:
        if not target or self._get_compatibility(target, next) == "switch":
            return Create(next, self.container)
        return Update(
            target,
            next,
            diff=self._diff(target, next),
        )

    def _get_inner_action(self) -> SubAction:
        assert self.next
        if self.old_next_rendered:
            return self._get_update_or_crate(self.old_next_rendered, self.next)
        return self._get_update_or_crate(self.prev, self.next)

    def _yield_replace(self, inner_action: SubAction):
        assert self.prev
        return Replace(
            self.container,
            self.prev,
            inner_action,
            self.at,
        )

    def compute(self):
        if not self.next:
            assert self.prev, "Neither prev nor next exists"
            return Unplace(self.prev)
        inner_action = self._get_inner_action()
        if not self.prev:
            return Place(
                self.container,
                self.at,
                inner_action,
            )

        match self._get_compatibility(self.prev, self.next):
            case "update" if isinstance(inner_action, Update):
                return inner_action
            case "place":
                return Place(self.container, self.at, inner_action)
            case "switch":
                return self._yield_replace(inner_action)
            case compat:
                raise ValueError(f"Unknown compatibility: {compat}")


@dataclass
class ComputeTreeActions:
    state: TransientReconcileState

    @staticmethod
    def _check_duplicates(rendering: Iterable[ShadowNode]):
        key_to_nodes = {
            key: list(group)
            for key, group in groupby(rendering, key=lambda x: x.__info__.uid)
        }
        messages = {
            key: f"Duplicates for {key} found: {group} "
            for key, group in key_to_nodes.items()
            if len(group) > 1
        }
        if messages:
            raise ValueError(messages)

    def _existing_children(self, parent: AnyNode) -> Iterable[RenderedNode[Any]]:
        existing_parent = self.state.existing_resources.get(parent.__info__.uid)
        if not existing_parent:
            return
        for child in existing_parent.node.KIDS:
            if child.__info__.uid not in self.state.being_placed:
                existing_child = self.state.existing_resources.get(child.__info__.uid)
                if existing_child:
                    yield existing_child

    def compute_actions(
        self, parent: AnyNode, is_creating_new=False
    ) -> Iterable["ReconcileAction"]:
        self._check_duplicates(parent.KIDS)
        existing_children = [*self._existing_children(parent)]
        pos = -1
        for prev, next in zip_longest(existing_children, parent.KIDS, fillvalue=None):
            if is_creating_new:
                prev = None
            pos += 1
            if not next and prev and prev.node.__info__.uid in self.state.being_placed:
                # if the prev node has gone somewhere else, it's already been unplaced
                # from its node-based position.
                continue
            if next:
                self.state.being_placed.add(next.__info__.uid)
            prev_resource = (
                self.state.existing_resources.get(prev.node.__info__.uid)
                if prev
                else None
            )
            old_next_rendered = (
                self.state.existing_resources.get(next.__info__.uid) if next else None
            )
            action = _ComputeAction(
                prev=prev_resource or prev,
                next=next,
                old_next_rendered=old_next_rendered,
                at=pos,
                container=parent,
            ).compute()
            yield action
            if next and next.KIDS:
                yield from self.compute_actions(
                    next,
                    is_creating_new=action.is_creating_new or is_creating_new,
                )
