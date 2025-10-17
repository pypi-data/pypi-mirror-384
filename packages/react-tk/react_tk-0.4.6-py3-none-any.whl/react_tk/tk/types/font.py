from dataclasses import dataclass, field
from typing import Annotated, NotRequired, TypedDict

from react_tk.props.annotations import prop_meta


@dataclass
class Font:
    family: str = field(default="Arial")
    size: int = field(default=12)
    style: str = field(default="normal")


def to_tk_font(font: Font | None):
    if font is None:
        return None
    return (font.family, font.size, font.style)
