from react_tk.props.annotations import prop_meta


from typing import Annotated, NotRequired, TypedDict


class BackgroundProps(TypedDict):
    background: Annotated[
        NotRequired[str], prop_meta(no_value="#000001", subsection="configure")
    ]
