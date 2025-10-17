import re
from dataclasses import dataclass, field
from types import FrameType
from typing import TYPE_CHECKING, Any, Literal
from inspect import getframeinfo, stack, FrameInfo, currentframe

from react_tk.reflect.accessor.base import KeyAccessor
from react_tk.util.stack import ReactTkFrameInfo
from react_tk.util.str import format_subscript

if TYPE_CHECKING:
    from react_tk.renderable.component import Component, RenderElement, RenderResult
    from react_tk.renderable.node.shadow_node import ShadowNode

replace_chars_in_key = re.compile(r"[^a-zA-Z0-9_]+")
starts_with_non_breaking = re.compile(r"^[^a-zA-Z0-9_]")
render_delim = "."

type Display = Literal["log", "safe", "id", "short-id"]


@dataclass(eq=True, unsafe_hash=True)
class RenderFrame:
    type_name: str
    lineno: int
    col_no: int
    key: str
    filename: str = field(default="")

    @classmethod
    def create(cls, rendered: "RenderElement") -> "RenderFrame":
        frame_info = ConstructTraceAccessor(rendered).get(None)

        if not frame_info:
            raise RuntimeError(
                f"Expected {rendered.__class__} to have a construct trace, but it was missing"
            )
        return cls(
            type_name=type(rendered).__name__,
            key=rendered.key,
            lineno=frame_info.line,
            col_no=frame_info.column,
            filename=frame_info.filename or "",
        )

    def to_sequenced(self, seq_id: int) -> "SequencedRenderFrame":
        return SequencedRenderFrame(based_on=self, seq_id=seq_id)


class SequencedRenderFrame(RenderFrame):
    def __init__(self, based_on: RenderFrame, seq_id: int):

        super().__init__(
            type_name=based_on.type_name,
            lineno=based_on.lineno,
            col_no=based_on.col_no,
            key=based_on.key,
            filename=based_on.filename,
        )
        self.seq_id = seq_id

    def to_string(self, display: Display) -> str:
        if display == "safe":

            if not self.key:
                result = f"{self.seq_id}+{self.lineno}_{self.type_name}"
            else:
                result = self.key

            return replace_chars_in_key.sub("_", result).lower()

        seq_id_part = (
            f"{format_subscript(self.seq_id)}" if self.seq_id is not None else ""
        )
        pos_part = f":{self.lineno}{seq_id_part}〉"
        key_part = f"{self.key}" if self.key else f"{pos_part}{self.type_name}"
        return key_part

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, SequencedRenderFrame):
            return False
        return super().__eq__(value) and self.seq_id == value.seq_id

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.seq_id))


class RenderTrace:
    frames: tuple[SequencedRenderFrame, ...]

    def __init__(self, *frames: SequencedRenderFrame):
        self.frames = frames

    def __add__(self, other: "RenderTrace | SequencedRenderFrame") -> "RenderTrace":
        if isinstance(other, RenderFrame):
            return RenderTrace(*self.frames, other)
        return RenderTrace(*self.frames, *other.frames)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RenderTrace):
            return NotImplemented
        return self.frames == value.frames

    def __hash__(self) -> int:
        return hash(self.frames)

    @property
    def top(self) -> RenderFrame | None:
        if not self.frames:
            return None
        return self.frames[-1]

    def to_string(self, display: Display) -> str:
        frames = self.frames
        if display == "short-id":
            frames = self.frames[-1:]
            display = "id"
        parts = [frame.to_string(display) for frame in frames]
        result = ""
        for part in parts:
            if result and not starts_with_non_breaking.search(part):
                result += render_delim if display != "safe" else "__"

            result += part

        return result


class RenderTraceAccessor(KeyAccessor[RenderTrace]):
    @property
    def key(self) -> str:
        return "_TRACE"


class ConstructTraceAccessor(KeyAccessor[ReactTkFrameInfo]):
    @property
    def key(self) -> str:
        return "_CONSTRUCT_TRACE"
