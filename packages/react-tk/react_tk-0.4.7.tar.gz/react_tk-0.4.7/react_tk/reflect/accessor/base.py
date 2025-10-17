from abc import abstractmethod
from typing import Any, Self, overload

from react_tk.util.missing import MISSING


class KeyAccessor[T]:
    __match_args__ = ("key",)
    type Value = T

    def __str__(self) -> str:
        return f"（ Attribute: {self.key} ）"

    def __bool__(self) -> bool:
        return self.has_key

    @classmethod
    def decorate(cls: type[Self], value: T):
        def wrapper[X](target: X) -> X:
            accessor = cls(target)
            accessor.set(value)
            return target

        return wrapper

    @property
    @abstractmethod
    def key(self) -> str: ...

    def __init__(self, target: object) -> None:
        self.target = target

    def set(self, value: T) -> None:
        try:
            setattr(self.target, self.key, value)
        except Exception:
            pass

    def set_from(self, other: object) -> None:
        match other:
            case KeyAccessor(key) as accessor:
                if accessor.key != self.key:
                    raise ValueError(
                        f"Cannot set from different key accessor {accessor.key} to {self.key}"
                    )
                self.set(accessor._get())
            case obj:
                accessor = type(self)(obj)
                if not accessor:
                    raise ValueError(
                        f"Cannot set from object without {self.key} attribute to {self.key}"
                    )
                self.set(accessor._get())

    @property
    def has_key(self) -> bool:
        return hasattr(self.target, self.key)

    def _get(self) -> T:
        return getattr(self.target, self.key)

    @overload
    def get(self, /) -> T: ...

    @overload
    def get[R](self, other: R, /) -> T | R: ...
    def get(self, other: Any = MISSING, /) -> Any:
        if not self.has_key:
            if other is MISSING:
                raise AttributeError(
                    f"{self.target.__class__.__name__} has no {self.key} attribute"
                )
            return other
        return self._get()
