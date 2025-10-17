from collections.abc import Callable
from dataclasses import dataclass
import logging
import threading
from tkinter import Tk
from tkinter.ttk import Frame
from typing import Any
from react_tk.rendering.actions.node_reconciler import Compat
from react_tk.renderable.node.shadow_node import ShadowNode
from react_tk.props.impl.prop import Prop_ComputedMapping
from react_tk.rendering.actions.actions import (
    Create,
    ReconcileAction,
    RenderedNode,
    Replace,
    Unplace,
    Update,
    Place,
)
from react_tk.rendering.actions.node_reconciler import ReconcilerBase
from react_tk.rendering.actions.reconcile_state import (
    PersistentReconcileState,
    TransientReconcileState,
)
from react_tk.tk.types.geometry import Geometry
from react_tk.tk.reconcilers.widget_reconciler import WidgetReconciler

logger = logging.getLogger("react_tk")


@dataclass
class WindowReconciler(ReconcilerBase[Tk]):

    @classmethod
    def create(cls, state: TransientReconcileState) -> "WindowReconciler":
        return cls(state)

    @classmethod
    def get_compatibility(
        cls, older: RenderedNode[Tk], newer: ShadowNode[Any]
    ) -> Compat:
        return "update"

    def _schedule_and_wait(self, resource: Tk, func: Callable[[], Any]) -> Any:
        result = [None]
        event = threading.Event()

        def wrapper():
            result[0] = func()
            event.set()

        resource.after(0, wrapper)
        event.wait()
        return result[0]

    def _normalize_geo(self, existing: Tk, geo: Geometry) -> str:
        x, y, width, height = (geo[k] for k in ("x", "y", "width", "height"))
        if x < 0:
            x = existing.winfo_screenwidth() + x
        if y < 0:
            y = existing.winfo_screenheight() + y
        match geo["anchor_point"]:
            case "lt":
                pass
            case "rt":
                x -= width
            case "lb":
                y -= height
            case "rb":
                x -= width
                y -= height

        return f"{width}x{height}+{x}+{y}"

    def _place(self, pair: RenderedNode[Tk]) -> None:
        def do_place():
            resource = pair.resource
            resource.deiconify()

        self._schedule_and_wait(pair.resource, do_place)

    def _replace(
        self, existing: RenderedNode[Tk], replacement: RenderedNode[Tk]
    ) -> None:
        self._unplace(existing)

        def do_replace():
            replacement.resource.deiconify()

        self._schedule_and_wait(replacement.resource, do_replace)

    def _update(self, rendered: RenderedNode[Tk], props: Prop_ComputedMapping) -> None:
        def do_update():
            resource = rendered.resource
            if attrs := props.values.get("attributes"):
                attributes = [
                    item for k, v in attrs.items() for item in (f"-{k}", v) if v
                ]
                resource.attributes(*attributes)
            if geometry := props.values.get("Geometry"):
                normed = self._normalize_geo(resource, geometry)
                resource.geometry(normed)
            if configure := props.values.get("configure"):
                resource.configure(**configure)
            if (override_redirect := props.values.get("override_redirect")) is not None:
                resource.overrideredirect(override_redirect)

        self._schedule_and_wait(rendered.resource, do_update)

    def _unplace(self, resource: RenderedNode[Tk]) -> None:
        if self.state.will_be_placed(resource.node):
            # already unplaced by virtue of being placed somewhere else.
            return

        def do_unplace():
            resource.resource.withdraw()

        self._schedule_and_wait(resource.resource, do_unplace)

    def _create_window(self, node: ShadowNode[Any]) -> "RenderedNode[Tk]":
        waiter = threading.Event()
        tk: Tk = None  # type: ignore

        def ui_thread():
            nonlocal tk
            tk = Tk()
            Frame(tk, name="limbo")

            waiter.set()
            tk.mainloop()

        thread = threading.Thread(target=ui_thread)
        thread.start()
        waiter.wait()

        return RenderedNode(tk, node)

    def _destroy(self, resource: Tk) -> None:
        def do_destroy():
            resource.destroy()

        self._schedule_and_wait(resource, do_destroy)

    def _do_create_action(self, action: Update[Tk] | Create[Tk]):
        match action:

            case Create(next, container) as c:
                new_resource = self._create_window(next)
                self._update(new_resource, c.diff)
                self._register(next, new_resource.resource)
                return new_resource
            case Update(existing, next, diff):
                if diff:
                    self._update(existing, diff)
                return existing.migrate(next)
            case _:
                assert False, f"Unknown action: {action}"

    def run_action(self, action: ReconcileAction[Tk]) -> None:
        if action:
            # FIXME: This should be an externalized event
            logger.info(f"⚖️  RECONCILE {action}")
        else:
            logger.info(f"🚫 RECONCILE {action.key} ")

        match action:
            case Replace(container, replaces, with_what, at):
                cur = self._do_create_action(with_what)
                self._unplace(replaces)
                self._place(cur)
            case Update(existing, next, diff):
                self._do_create_action(action)
            case Unplace(existing):
                self._unplace(existing)
            case Place(container, at, createAction) as x:
                cur = self._do_create_action(createAction)
                self._place(cur)
            case _:
                assert False, f"Unknown action: {action}"
