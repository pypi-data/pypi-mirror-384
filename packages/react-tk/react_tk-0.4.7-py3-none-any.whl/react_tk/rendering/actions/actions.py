from dataclasses import dataclass, field
from re import sub
from tkinter import Misc
from typing import TYPE_CHECKING, Any, ClassVar, Iterable, Iterator
from typing_extensions import Literal

from funcy import first


from react_tk.renderable.node.prop_value_accessor import PropValuesAccessor
from react_tk.props.impl.prop import Prop_ComputedMapping
from react_tk.rendering.actions.reconcile_state import RenderedNode
from react_tk.util.dict import get_dict_one_line

if TYPE_CHECKING:
    from react_tk.rendering.actions.compute import AnyNode


class ConstructiveAction:
    pass


def sub_action_to_string[T](
    self: "SubAction[T]", format_spec: Literal["top", "nested"]
):
    one_line = get_dict_one_line(self.diff.values)
    parts = [f"{self.emoji}"]

    match format_spec:
        case "top":
            parts.append(f"{self.node.__info__.short_id}")
            parts.append(one_line)
        case "nested":
            parts.append(one_line)
        case _:
            return self.__repr__()

    return " ".join(parts)


def outer_action_to_string[T](self: "Place[T] | Replace[T]"):
    parts = [f"{self.emoji}"]
    parts.append(
        f"{sub_action_to_string(self.target_prep, "nested")} {self.node.__info__.short_id}"
    )
    return " ".join(parts)


@dataclass
class Create[Res](ConstructiveAction):
    emoji: ClassVar[str] = "🆕"
    next: "AnyNode"
    container: "AnyNode"

    @property
    def node(self) -> "AnyNode":
        return self.next

    def __post_init__(self):
        self.diff = PropValuesAccessor(self.next).get().compute()

    def __repr__(self) -> str:
        return sub_action_to_string(self, "top")

    @property
    def key(self) -> Any:
        return self.next.__info__.uid

    @property
    def is_creating_new(self) -> bool:
        return True


@dataclass
class Update[Res = Misc](ConstructiveAction):
    emoji: ClassVar[str] = "📝"
    existing: RenderedNode[Res]
    next: "AnyNode"
    diff: Prop_ComputedMapping

    @property
    def node(self) -> "AnyNode":
        return self.next

    def __bool__(self):
        return bool(self.diff)

    def __repr__(self) -> str:
        return sub_action_to_string(self, "top")

    @property
    def key(self) -> Any:
        return self.next.__info__.uid

    @property
    def is_creating_new(self) -> bool:
        return False


@dataclass
class Place[Res = Misc](ConstructiveAction):
    emoji: ClassVar[str] = "👇"
    container: "AnyNode"
    at: int
    target_prep: Update[Res] | Create[Res]

    @property
    def node(self) -> "AnyNode":
        return self.target_prep.next

    @property
    def diff(self) -> Prop_ComputedMapping:
        return self.target_prep.diff

    def __repr__(self) -> str:
        parts = [f"{self.emoji}"]
        parts.append(
            f"{self.node.__info__.short_id} @ {self.container.__info__.short_id}[{self.at}] ::"
        )
        parts.append(f"{sub_action_to_string(self.target_prep, 'nested')}")
        return " ".join(parts)

    @property
    def uid(self) -> Any:
        return self.target_prep.key

    @property
    def is_creating_new(self) -> bool:
        return self.target_prep.is_creating_new


@dataclass
class Unplace[Res = Misc]:
    emoji: ClassVar[str] = "🙈"
    what: RenderedNode[Res]

    @property
    def node(self) -> "AnyNode":
        return self.what.node

    @property
    def is_creating_new(self) -> bool:
        return False

    def __repr__(self) -> str:
        parts = [f"{self.emoji}"]
        parts.append(f"{self.what.node.__info__.short_id}")
        return " ".join(parts)

    @property
    def uid(self) -> Any:
        return self.what.node.__info__.uid


@dataclass
class Replace[Res = Misc]:
    emoji: ClassVar[str] = "🔄"
    container: "AnyNode"
    replaces: RenderedNode[Res]
    target_prep: Update[Res] | Create[Res]
    at: int

    def __repr__(self) -> str:
        parts = [f"{self.emoji}"]
        parts.append(
            f"{self.node.__info__.short_id} / {self.replaces.node.__info__.short_id} @ {self.container.__info__.short_id}[{self.at}] ::"
        )
        parts.append(f"{sub_action_to_string(self.target_prep, 'nested')}")
        return " ".join(parts)

    @property
    def node(self) -> "AnyNode":
        return self.target_prep.next

    @property
    def is_creating_new(self) -> bool:
        return self.target_prep.is_creating_new

    @property
    def diff(self) -> Prop_ComputedMapping:
        return self.target_prep.diff

    @property
    def uid(self) -> Any:
        return self.replaces.node.__info__.uid


type ReconcileAction[Res = Misc] = Place[Res] | Unplace[Res] | Update[Res] | Replace[
    Res
]

type SubAction[Res = Misc] = Create[Res] | Update[Res]
type Compat = Literal["update", "switch", "place"]
