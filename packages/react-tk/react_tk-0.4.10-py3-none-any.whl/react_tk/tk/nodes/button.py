from typing import Any, Unpack
from react_tk.props.annotations.create_props import MetaAccessor
from react_tk.props.annotations.decorators import schema_setter
from react_tk.props.impl.prop import Prop_ComputedMapping
from react_tk.renderable.node.shadow_node import NodeProps
from react_tk.rendering.actions.compute import AnyNode
from react_tk.rendering.actions.reconcile_state import RenderedNode
from react_tk.tk.nodes.widget import Widget
from react_tk.tk.props.background import BackgroundProps
from react_tk.tk.props.border import BorderProps
from react_tk.tk.props.clickable import ClickableProps
from react_tk.tk.props.padding import PaddingProps
from react_tk.tk.props.text import TextProps
from react_tk.tk.props.width_height import WidthProps
from react_tk.rendering.actions.node_reconciler import reconciler
from react_tk.tk.reconcilers.widget_reconciler import WidgetReconciler
import tkinter


class ButtonProps(
    NodeProps, TextProps, BackgroundProps, BorderProps, WidthProps, ClickableProps
):
    pass


class ButtonReconciler(WidgetReconciler):

    def _create(
        self, container: "tkinter.Misc", node: AnyNode
    ) -> RenderedNode["tkinter.Widget"]:
        b = tkinter.Button(container)
        return RenderedNode(
            b,
            node,
        )

    def _update(self, resource: tkinter.Widget, props: Prop_ComputedMapping) -> None:
        super()._update(resource, props)

        if "on_click" in props.values:
            if props["on_click"] is None:
                resource.configure(command=None)  # type: ignore[arg-type]
            else:
                resource.configure(command=props["on_click"])  # type: ignore[arg-type]


@reconciler(ButtonReconciler)
class Button(Widget[Widget[Any]]):
    @schema_setter()
    def __init__(self, **props: Unpack[ButtonProps]) -> None: ...
