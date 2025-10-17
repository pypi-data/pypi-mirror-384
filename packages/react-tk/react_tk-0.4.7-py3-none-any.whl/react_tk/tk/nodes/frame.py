from react_tk.props.annotations import schema_setter
from react_tk.rendering.actions.compute import AnyNode
from react_tk.rendering.actions.node_reconciler import reconciler
from react_tk.rendering.actions.reconcile_state import RenderedNode
from react_tk.tk.nodes.widget import Widget
from react_tk.tk.reconcilers.widget_reconciler import WidgetReconciler
from react_tk.renderable.node.shadow_node import NodeProps
from react_tk.tk.props.background import BackgroundProps
from react_tk.tk.props.border import BorderProps
from react_tk.tk.props.width_height import WidthHeightProps
from typing import Any, Unpack
import tkinter


class FrameProps(NodeProps, WidthHeightProps, BorderProps, BackgroundProps):
    pass


class FrameReconciler(WidgetReconciler):

    def _create(
        self, container: "tkinter.Misc", node: AnyNode
    ) -> RenderedNode["tkinter.Widget"]:
        return RenderedNode(
            tkinter.Frame(container),
            node,
        )


@reconciler(FrameReconciler)
class Frame(Widget[Widget[Any]]):
    @schema_setter()
    def __init__(self, **props: Unpack[FrameProps]) -> None: ...
