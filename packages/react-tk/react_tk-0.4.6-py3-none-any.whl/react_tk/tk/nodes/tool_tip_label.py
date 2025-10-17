import tkinter
from react_tk.rendering.actions.compute import AnyNode
from react_tk.rendering.actions.node_reconciler import reconciler
from react_tk.rendering.actions.reconcile_state import RenderedNode
from react_tk.tk.nodes.label import Label, LabelReconciler

from react_tk.tk.win32.tweaks import make_clickthrough


class ToolTipLabelReconciler(LabelReconciler):

    def _create(
        self, container: "tkinter.Misc", node: AnyNode
    ) -> RenderedNode["tkinter.Widget"]:
        label = super()._create(container, node)
        try:
            make_clickthrough(label.resource)
        except ImportError:
            return LabelReconciler._create(self, container, node)
        return label


@reconciler(ToolTipLabelReconciler)
class ToolTipLabel(Label):
    pass
