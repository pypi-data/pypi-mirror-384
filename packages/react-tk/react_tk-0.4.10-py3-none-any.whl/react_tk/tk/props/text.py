from typing import NotRequired, TypedDict
from expression import Some
from typing_extensions import Annotated

from react_tk.props.annotations.prop_meta import prop_meta
from react_tk.tk.types.font import Font


class TextProps(TypedDict):
    text: Annotated[NotRequired[str], prop_meta(no_value="", subsection="configure")]
    font: Annotated[NotRequired[Font], prop_meta(diff="simple", no_value=None)]
    foreground: Annotated[
        NotRequired[str], prop_meta(no_value="#ffffff", subsection="configure")
    ]
    justify: Annotated[
        NotRequired[str], prop_meta(no_value="center", subsection="configure")
    ]
    wraplength: Annotated[
        NotRequired[int], prop_meta(no_value=None, subsection="configure")
    ]
