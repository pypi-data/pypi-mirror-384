from abc import ABC
import sys
from typing import Any

from react_tk.renderable.trace import ConstructTraceAccessor
from react_tk.util.stack import get_first_non_ctor_frame_info


class RenderableBase:

    def __new__(cls, *args: Any, **kwargs: Any):
        instance = super().__new__(cls)

        caller = get_first_non_ctor_frame_info()

        ConstructTraceAccessor(instance).set(caller)
        return instance
