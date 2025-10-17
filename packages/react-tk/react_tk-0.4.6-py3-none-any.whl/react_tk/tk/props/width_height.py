from react_tk.props.annotations import prop_meta


from typing import Annotated, NotRequired, TypedDict


class WidthProps(TypedDict):
    width: Annotated[NotRequired[int], prop_meta(no_value=None)]


class HeightProps(TypedDict):
    height: Annotated[NotRequired[int], prop_meta(no_value=None)]


class WidthHeightProps(WidthProps, HeightProps):
    pass
