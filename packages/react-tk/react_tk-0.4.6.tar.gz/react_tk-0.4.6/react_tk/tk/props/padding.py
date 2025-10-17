from typing import Annotated, NotRequired, TypedDict

from react_tk.props.annotations import prop_meta
from react_tk.tk.types.padding import Padding


class PaddingProps(TypedDict):
    padding: Annotated[NotRequired[Padding], prop_meta(no_value=Padding.uniform(0))]
