from abc import abstractmethod
from dataclasses import dataclass
import threading
from tkinter import Misc, Tk, Widget, Label as TkLabel
from react_tk.renderable.node.prop_value_accessor import PropValuesAccessor
from react_tk.rendering.actions.node_reconciler import Compat
from react_tk.renderable.node.shadow_node import ShadowNode
from react_tk.props.impl.prop import Prop_ComputedMapping
from react_tk.rendering.actions.actions import (
    Create,
    Place,
    ReconcileAction,
    RenderedNode,
    Replace,
    Unplace,
    Update,
)
from react_tk.rendering.actions.compute import AnyNode, logger
from react_tk.rendering.actions.reconcile_state import (
    PersistentReconcileState,
    TransientReconcileState,
)

from react_tk.rendering.actions.node_reconciler import ReconcilerBase

from typing import Any, Callable, Iterable, override

from react_tk.tk.types.font import to_tk_font
from react_tk.tk.util.tk import get_pack_position
from react_tk.tk.win32.tweaks import make_clickthrough


@dataclass
class WidgetReconciler(ReconcilerBase[Widget]):
    state: TransientReconcileState
    waiter = threading.Event()

    @classmethod
    def create(cls, state: TransientReconcileState) -> "WidgetReconciler":
        return cls(state)

    @classmethod
    @override
    def get_compatibility(cls, older: RenderedNode[Widget], newer: AnyNode) -> Compat:
        # TODO: Find a better way to determine compatibility
        if older.node.__info__.uid != newer.__info__.uid:
            return "switch"
        pack_info = older.resource.pack_info()
        in_ = pack_info.get("in", None)
        assert in_ is not None
        if in_.winfo_name() == "limbo":
            return "place"
        return "update"

    @abstractmethod
    def _create(
        self, container: Widget | Tk, node: AnyNode
    ) -> RenderedNode[Widget]: ...

    def _pack(self, resource: Widget, diff: Prop_ComputedMapping):
        resource.pack_configure(
            **diff.source.compute().values.get("Pack", {}),
        )

    def _pack_at(
        self,
        container: ShadowNode[Any],
        resource: Widget,
        at: int,
    ):
        rendered_container = self.state[container]
        pack_pos = get_pack_position(rendered_container.resource, at)
        positioning = {
            "in_": rendered_container.resource,
            **(pack_pos.to_dict() if pack_pos else {}),
        }

        resource.pack_configure(**positioning)

    def _update(self, resource: Widget, props: Prop_ComputedMapping) -> None:
        diff = props.values
        configure = diff.get("configure", {})
        if "font" in diff:
            configure["font"] = to_tk_font(diff["font"])
        resource.configure(**diff.get("configure", {}))
        resource.pack_configure(**diff.get("Pack", {}))

    def _get_some_ui_resource(self, node: ReconcileAction[Widget]) -> Widget | Tk:
        match node:
            case Update(existing) | Unplace(existing):
                return existing.resource
            case x:
                container = x.container
                return self.state.existing_resources[container.__info__.uid].resource

    def _get_root(self, node: Misc) -> Tk:
        while node.master:
            node = node.master
        return node  # type: ignore[return-value]

    def _get_master_from_container(self, container: AnyNode) -> Tk:
        master = self.state.existing_resources[container.__info__.uid].resource
        return self._get_root(master)

    def _do_create_action(self, action: Update[Widget] | Create[Widget]):
        match action:
            case Create(next, container) as c:
                master_root = self._get_master_from_container(container)
                new_resource = self._create(master_root, next)
                self._update(new_resource.resource, c.diff)
                self._register(next, new_resource.resource)
                return new_resource
            case Update(existing, next, diff):
                if diff:
                    self._update(existing.resource, diff)
                return existing.migrate(next)
            case _:
                assert False, f"Unknown action: {action}"

    def _unplace(self, rendered: RenderedNode[Widget]):
        if self.state.will_be_placed(rendered.node):
            return
        root = self._get_root(rendered.resource)
        limbo = root.nametowidget("limbo")
        rendered.resource.pack(in_=limbo)

    def _run_action_main_thread(self, action: ReconcileAction[Widget]):
        try:
            if action:
                # FIXME: This should be an externalized event
                logger.info(f"⚖️  RECONCILE {action}")
            else:
                logger.info(f"🚫 RECONCILE {action.key} ")

            match action:
                case Replace(container, replaces, with_what, at):
                    self._unplace(replaces)
                    cur = self._do_create_action(with_what)
                    self._pack_at(container, cur.resource, at)
                case Update(existing, next):
                    self._do_create_action(action)
                case Unplace(existing):
                    self._unplace(existing)
                case Place(container, at, createAction) as x:
                    cur = self._do_create_action(createAction)
                    self._pack_at(container, cur.resource, at)
                case _:
                    assert False, f"Unknown action: {action}"
        finally:
            self.waiter.set()

    def run_action(self, action: ReconcileAction[Widget], log=True):
        existing_parent = self._get_some_ui_resource(action)
        self.waiter.clear()
        existing_parent.after(0, lambda: self._run_action_main_thread(action))
        self.waiter.wait()
