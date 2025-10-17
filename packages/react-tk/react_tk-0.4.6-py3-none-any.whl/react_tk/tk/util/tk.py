from dataclasses import dataclass
from tkinter import Misc, Tk, Widget


@dataclass
class Before:
    what: Widget

    def to_dict(self) -> dict[str, Widget]:
        return {"before": self.what}


@dataclass
class After:
    what: Widget

    def to_dict(self) -> dict[str, Widget]:
        return {"after": self.what}


type PackPosition = Before | After


def get_root(node: Misc) -> Tk:
    while node.master:
        node = node.master
    return node  # type: ignore[return-value]


def get_in(resource: Widget | Tk) -> Widget | Tk:
    if isinstance(resource, Tk):
        return resource
    info = resource.pack_info()
    return info.get("in") or get_root(resource)  # type: ignore[return-value]


def get_pack_position(resource: Widget, at: int) -> PackPosition | None:
    packed_in = get_in(resource)
    slaves = packed_in.pack_slaves()
    if not slaves:
        if at == 0:
            return None
        raise ValueError("No packed slaves found")
    if at >= len(slaves):
        return After(slaves[-1])
    elif at <= 0:
        return Before(slaves[0])
    else:
        return After(slaves[at - 1])
