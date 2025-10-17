from typing import Any
from react_tk.interaction.scheduler import Scheduler
from react_tk.renderable.component import Component
from react_tk.renderable.context import Ctx, ctx_freeze
from react_tk.renderable.node.shadow_node import ShadowNode
from react_tk.rendering.actions.reconcile_state import PersistentReconcileState
from react_tk.rendering.actions.top_reconciler import RootReconciler
from react_tk.rendering.component.render_sink import RenderSink, RenderState


class RenderRoot[Node: ShadowNode[Any] = ShadowNode[Any]]:
    _reconciler: RootReconciler[Node]
    _mounted: Component[Node]

    def __init__(self, initial: Component[Node], **context_kwargs: Any) -> None:
        self._mounted = initial
        self.ctx = Ctx(**context_kwargs)
        self.ctx += lambda _: self._rerender()
        self._reconciler = RootReconciler(PersistentReconcileState())
        self._rerender()

    def __call__(self, **kwargs: Any) -> None:
        self.ctx(**kwargs)

    def _rerender(self):
        with ctx_freeze(self.ctx):
            render_state = RenderState(self.ctx)
            sink = render_state.create_empty_sink()
            render_result = sink.run(self._mounted)
        self._reconciler.reconcile(tuple(render_result))
