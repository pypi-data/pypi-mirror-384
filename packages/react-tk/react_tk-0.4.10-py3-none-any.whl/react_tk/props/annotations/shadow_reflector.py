from react_tk.reflect.reflector import Reflector


from collections.abc import Mapping
from typing import TypedDict


shadow_reflector = Reflector(
    inspect_up_to=(Mapping, TypedDict, "ShadowNode", object, "_HasMerge")
)
