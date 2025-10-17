from typing import Any, TypeVar

from react_tk.reflect.accessor.base import KeyAccessor


class ArgsAccessor(KeyAccessor[tuple]):
    """Accessor for the private __args__ attribute used by typing.

    This accessor raises an AttributeError if the attribute is missing to
    make callers handle the absence explicitly (per new API requirement).
    """

    @property
    def key(self) -> str:
        return "__args__"


class TypeParamsAccessor(KeyAccessor[tuple[TypeVar, ...]]):
    """Accessor for the private __type_params__ attribute.

    Returns a tuple of TypeVar objects when present, or an empty tuple if
    the attribute is absent. The return type is annotated as
    tuple[TypeVar, ...].
    """

    @property
    def key(self) -> str:
        return "__type_params__"


class MetadataAccessor(KeyAccessor[tuple]):
    """Accessor for the private __metadata__ attribute used by typing.Annotated.

    This accessor raises an AttributeError if the attribute is missing to
    make callers handle the absence explicitly (per new API requirement).
    """

    @property
    def key(self) -> str:
        return "__metadata__"


class UnderscoreNameAccessor(KeyAccessor[str]):
    """Accessor for the private __name__ attribute.

    This accessor raises an AttributeError if the attribute is missing to
    make callers handle the absence explicitly (per new API requirement).
    """

    @property
    def key(self) -> str:
        return "_name"


class BasesAccessor(KeyAccessor[tuple[type, ...]]):
    """Accessor for the private __bases__ attribute.

    This accessor raises an AttributeError if the attribute is missing to
    make callers handle the absence explicitly (per new API requirement).
    """

    @property
    def key(self) -> str:
        return "__bases__"


class OrigBasesAccessor(KeyAccessor[tuple[type, ...]]):
    """Accessor for the private __orig_bases__ attribute.

    This accessor raises an AttributeError if the attribute is missing to
    make callers handle the absence explicitly (per new API requirement).
    """

    @property
    def key(self) -> str:
        return "__orig_bases__"
