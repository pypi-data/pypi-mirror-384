from copy import copy
from dataclasses import dataclass
from tkinter import Tk
from typing import (
    Annotated,
    Any,
    Literal,
    NotRequired,
    Self,
    Tuple,
    Unpack,
    override,
)

from expression import Some


from react_tk.props.annotations import (
    prop_meta,
    schema_meta,
    schema_setter,
    prop_setter,
)
from react_tk.renderable.component import Component
from react_tk.renderable.node.shadow_node import (
    NodeProps,
    ShadowNode,
)
from react_tk.rendering.actions.node_reconciler import ReconcilerBase
from react_tk.tk.nodes.widget import Widget
from react_tk.tk.props.background import BackgroundProps
from react_tk.tk.reconcilers.widget_reconciler import WidgetReconciler
from react_tk.tk.reconcilers.window_reconciler import WindowReconciler
from react_tk.tk.types.geometry import Geometry
from react_tk.rendering.actions.node_reconciler import reconciler


class WindowProps(NodeProps, BackgroundProps):
    topmost: Annotated[
        NotRequired[bool], prop_meta(subsection="attributes", no_value=False)
    ]
    transparent_color: Annotated[
        NotRequired[str],
        prop_meta(
            subsection="attributes", name="transparentcolor", no_value=Some(None)
        ),
    ]
    override_redirect: Annotated[
        NotRequired[bool], prop_meta(no_value=False, name="override_redirect")
    ]
    alpha: Annotated[
        NotRequired[float], prop_meta(subsection="attributes", no_value=1.0)
    ]


@reconciler(WindowReconciler)
class Window(ShadowNode[Widget]):

    @schema_setter()
    def __init__(self, **props: Unpack[WindowProps]) -> None: ...

    @schema_setter()
    def Geometry(self, **props: Unpack[Geometry]) -> None: ...
