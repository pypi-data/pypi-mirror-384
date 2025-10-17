from react_tk.props.annotations import prop_meta


from typing import Annotated, NotRequired, TypedDict


class BorderProps(TypedDict):
    border_width: Annotated[
        NotRequired[int],
        prop_meta(no_value=0, subsection="configure", name="borderwidth"),
    ]
    relief: Annotated[
        NotRequired[str],
        prop_meta(no_value="solid", subsection="configure", name="relief"),
    ]
