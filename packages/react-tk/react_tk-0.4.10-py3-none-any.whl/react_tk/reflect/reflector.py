import builtins
from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from react_tk.reflect.reader.base import unpack_reader
from react_tk.reflect.reader.generic import Reader_BoundTypeVar
from react_tk.util.core_reflection import none_match_ref

if TYPE_CHECKING:
    from react_tk.util.type_hints import type_reference
    from react_tk.reflect.reader.generic import SomeTypeVarReader


@dataclass
class Reflector:
    inspect_up_to: "type_reference | tuple[type_reference, ...]" = field(default=object)
    localns: Mapping[str, object] = field(default_factory=dict)
    is_supported: Callable[[type], bool] = field(
        init=False, repr=False, hash=False, compare=False
    )

    def __post_init__(self) -> None:
        inspect_up_to = (
            self.inspect_up_to
            if isinstance(self.inspect_up_to, tuple)
            else (self.inspect_up_to,)
        )
        self.is_supported = none_match_ref(*inspect_up_to)

    def type(self, target: type):
        from react_tk.reflect.reader.type import Reader_Class

        return Reader_Class(target=unpack_reader(target), reflector=self)

    def annotation(self, target: object):
        from react_tk.reflect.reader.type import Reader_Annotation

        return Reader_Annotation(target=unpack_reader(target), reflector=self)

    def _get_generic_signature(self, t: Any) -> tuple["SomeTypeVarReader", ...]:
        from react_tk.reflect.reader.generic import (
            TypeParamsAccessor,
            ArgsAccessor,
        )

        target = self.annotation(t)
        origin = target.origin
        if origin is None:
            raise ValueError(f"Type {t} has no origin")
        # declared type parameters on the origin
        params = origin(TypeParamsAccessor).get(())
        # runtime args on the supplied target (may be absent)
        ta = target(ArgsAccessor)
        args: tuple = ()
        if ta.has_key:
            args = ta.get(())

        readers: list[SomeTypeVarReader] = []
        for idx, (param, arg) in enumerate(zip_longest(params, args, fillvalue=None)):
            if param is None:
                param_reader = self.type_var(TypeVar(f"_{idx}"), is_undeclared=True)
            else:
                param_reader = self.type_var(param)

            # normal handling when a declared type-variable exists
            param_default = param_reader.default

            # supplied arg wins
            if arg is not None:
                readers.append(
                    self.type_arg(
                        param_reader.target,
                        arg,
                        is_undeclared=param_reader.is_undeclared,
                    )
                )
            # fallback to TypeVar default if present
            elif param_default is not None:
                readers.append(
                    self.type_arg(
                        target=param_reader.target,
                        value=param_default.target,
                        is_undeclared=param_reader.is_undeclared,
                        is_defaulted=True,
                    )
                )
            else:
                # param_reader is already an unbound TypeVar reader
                readers.append(param_reader)

        return tuple(readers)

    def get_type_hints(
        self, cls: builtins.type, **defaults: builtins.type
    ) -> dict[str, object]:
        from react_tk.util.type_hints import get_type_hints_up_to

        inspect_up_to = (
            self.inspect_up_to
            if isinstance(self.inspect_up_to, tuple)
            else (self.inspect_up_to,)
        )
        return get_type_hints_up_to(cls, inspect_up_to, **defaults, **self.localns)

    def method(self, target: Callable[..., Any]):
        from react_tk.reflect.reader.type import Reader_Method

        return Reader_Method(target=unpack_reader(target), reflector=self)

    def generic(self, target: Any):
        """Create a Reader_Generic for the given target using this reflector."""
        from react_tk.reflect.reader.generic import Reader_Generic

        return Reader_Generic(target=unpack_reader(target), reflector=self)

    def type_var(self, target: TypeVar, *, is_undeclared=False):
        from react_tk.reflect.reader.generic import Reader_TypeVar

        return Reader_TypeVar(
            target=unpack_reader(target), reflector=self, is_undeclared=is_undeclared
        )

    def type_arg(
        self, target: TypeVar, value: Any, *, is_undeclared=False, is_defaulted=False
    ):
        from react_tk.reflect.reader.generic import Reader_BoundTypeVar

        return Reader_BoundTypeVar(
            target=unpack_reader(target),
            reflector=self,
            is_undeclared=is_undeclared,
            value=self.annotation(value),
            is_defaulted=is_defaulted,
        )
