from typing import Annotated, Callable, NotRequired, TypedDict

from react_tk.props.annotations import prop_meta
from react_tk.tk.props.handler import CommandHandler


class ClickableProps(TypedDict):
    on_click: Annotated[NotRequired[CommandHandler | None], prop_meta(no_value=None)]
