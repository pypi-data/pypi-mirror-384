from react_tk.props.annotations import prop_meta


from typing import Annotated, Literal, NotRequired, TypedDict


class PackProps(TypedDict):
    ipadx: Annotated[NotRequired[int], prop_meta(no_value=0)]
    ipady: Annotated[NotRequired[int], prop_meta(no_value=0)]
    fill: Annotated[
        NotRequired[Literal["both", "x", "y", "none"]], prop_meta(no_value="none")
    ]
    side: Annotated[
        NotRequired[Literal["top", "bottom", "left", "right"]],
        prop_meta(no_value="top"),
    ]
    expand: Annotated[NotRequired[bool], prop_meta(no_value=False)]
    anchor: Annotated[
        NotRequired[Literal["n", "s", "e", "w", "ne", "nw", "se", "sw"]],
        prop_meta(no_value="n"),
    ]
