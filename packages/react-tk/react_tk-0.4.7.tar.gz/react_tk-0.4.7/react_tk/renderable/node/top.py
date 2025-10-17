from typing import Any, Unpack

from react_tk.renderable.node.shadow_node import NodeProps, ShadowNode, ShadowNodeInfo
from react_tk.props.annotations.decorators import schema_setter
from react_tk.renderable.trace import RenderFrame, RenderTrace, RenderTraceAccessor
from react_tk.rendering.actions.node_reconciler import ReconcilerBase, reconciler


# does not need a reconciler since it is never diffed or updated
@reconciler(ReconcilerBase)
class TopLevelNode(ShadowNode[Any]):
    @schema_setter()
    def __init__(self, **props: Unpack[NodeProps]) -> None: ...

    def __post_init__(self):
        RenderTraceAccessor(self).set(
            RenderTrace(RenderFrame.create(self).to_sequenced(0))
        )

    @property
    def __info__(self) -> ShadowNodeInfo:
        orig = super().__info__
        return orig
