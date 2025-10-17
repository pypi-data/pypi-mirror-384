from dataclasses import dataclass, field
from typing import Annotated, NotRequired, Self, TypedDict

from react_tk.props.annotations import prop_meta


@dataclass(kw_only=True)
class Padding:
    left: int = field(default=0)
    top: int = field(default=0)
    right: int = field(default=0)
    bottom: int = field(default=0)

    @staticmethod
    def uniform(value: int) -> "Padding":
        return Padding(left=value, top=value, right=value, bottom=value)

    @staticmethod
    def vert_horz(vertical: int, horizontal: int) -> "Padding":
        return Padding(left=horizontal, top=vertical, right=horizontal, bottom=vertical)
