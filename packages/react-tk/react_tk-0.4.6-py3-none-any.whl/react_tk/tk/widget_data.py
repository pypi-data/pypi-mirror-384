from dataclasses import dataclass
from typing import Any
from react_tk.reflect.accessor.base import KeyAccessor
from react_tk.renderable.node.shadow_node import ShadowNode


class WidgetNode(KeyAccessor[ShadowNode[Any]]):
    @property
    def key(self) -> str:
        return "__reactk_widget_node__"
