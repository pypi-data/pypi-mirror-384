from collections.abc import Mapping
from typing import Any, Callable, Literal


type Converter[T] = Callable[[T], Any]


type DiffMode = Literal["simple", "recursive", "never", "always"]


type KeyedValues = Mapping[str, Any]
