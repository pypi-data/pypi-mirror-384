from ast import List
from collections import defaultdict
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
import sys
from typing import Any, Iterable, overload
from react_tk.props.impl import prop
from react_tk.renderable.component import (
    AbsCtx,
    AbsSink,
    Component,
    RenderElement,
    RenderResult,
    is_render_element,
)
from react_tk.renderable.context import Ctx
from react_tk.renderable.node.shadow_node import ShadowNode
from react_tk.renderable.trace import (
    ConstructTraceAccessor,
    RenderFrame,
    RenderTrace,
    RenderTraceAccessor,
    SequencedRenderFrame,
)
import funcy


class RenderState:
    _next_render_trace_seq_id: dict[tuple[RenderTrace, RenderFrame], int]

    def __init__(self, ctx: AbsCtx) -> None:
        self._next_render_trace_seq_id = defaultdict(lambda: 0)
        self.ctx = ctx

    def create_empty_sink(self) -> "RenderSink":
        return RenderSink(state=self, trace_root=RenderTrace())

    def produce_sequenced(
        self, trace: RenderTrace, frame: RenderFrame
    ) -> SequencedRenderFrame:
        free_seq_id = self._next_render_trace_seq_id[(trace, frame)]
        self._next_render_trace_seq_id[(trace, frame)] += 1
        return frame.to_sequenced(free_seq_id)


@dataclass
class RenderSink[Node: ShadowNode[Any] = ShadowNode[Any]](AbsSink[Node]):
    state: RenderState
    trace_root: RenderTrace

    @property
    def ctx(self) -> AbsCtx:
        return self.state.ctx

    def _child_sink(self, trace: RenderTrace) -> "RenderSink[Node]":
        return RenderSink(
            state=self.state,
            trace_root=trace,
        )

    def _render_one(self, node: RenderElement[Node]) -> RenderResult[Node]:
        frame_base = RenderFrame.create(node)
        sequenced = self.state.produce_sequenced(self.trace_root, frame_base)
        new_trace = self.trace_root + sequenced
        RenderTraceAccessor(node).set(new_trace)
        new_sink = self._child_sink(new_trace)
        match node:
            case ShadowNode():
                node = node.__merge__(KIDS=new_sink.run(node.KIDS))
                node.PROPS.assert_valid()
                return node
            case Component():
                return new_sink._run_component_render(node)
            case _:
                raise TypeError(
                    f"Expected node to be ShadowNode or Component, but got {type(node)}"
                )

    def run(self, node: RenderResult[Node], /) -> tuple[Node, ...]:
        rendered = []
        nodes = list(node) if isinstance(node, Iterable) else [node]
        for node in funcy.flatten(nodes):
            result = self._render_one(node)
            if isinstance(result, Iterable):
                rendered.extend(funcy.flatten(result))
            else:
                rendered.append(result)
        return tuple(rendered)

    def _run_component_render(self, component: Component[Node]) -> RenderResult[Node]:
        component.ctx = self.ctx
        results = component.render()
        return self.run(results)
