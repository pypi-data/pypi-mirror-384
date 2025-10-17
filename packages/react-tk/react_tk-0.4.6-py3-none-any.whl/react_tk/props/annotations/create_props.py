from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Annotated, Any, Required, is_typeddict
from react_tk.props.annotations.shadow_reflector import shadow_reflector
from react_tk.util.core_reflection import get_attrs_downto
from typing import TYPE_CHECKING
from expression import Nothing, Some, Option

from react_tk.util.maybe import maybe_normalize

if TYPE_CHECKING:
    from react_tk.renderable.trace import RenderTrace
from react_tk.reflect.reader.type import (
    Reader_Annotation,
    Reader_Class,
    Reader_Method,
)
from react_tk.reflect.accessor.base import KeyAccessor
from react_tk.props.annotations.prop_meta import prop_meta, schema_meta, some_meta
from react_tk.props.impl.prop import Prop_Any
import funcy

from react_tk.props.impl.v_mapping import VMappingBase

from react_tk.props.impl.prop import Prop, Prop_Schema


class MetaAccessor(KeyAccessor[some_meta]):
    @property
    def key(self) -> str:
        return "__react_tk_meta__"


def _create_prop(
    path: tuple[str, ...], name: str, annotation: Reader_Annotation, meta: prop_meta
):
    from react_tk.props.impl.prop import Prop

    x: Any = annotation.inner_type
    return Prop[x](
        name=name,
        diff=meta.diff,
        no_value=maybe_normalize(meta.no_value),
        converter=meta.converter,
        computed_name=meta.name,
        subsection=meta.subsection,
        metadata=meta.metadata,
        value_type=x,
        path=(*path,),
    )


def _create_schema(
    path: tuple[str, ...], name: str, annotation: Reader_Annotation, meta: schema_meta
):
    from react_tk.props.impl.prop import Prop_Schema

    return Prop_Schema(
        path=path,
        name=name,
        computed_name=meta.name,
        props=_read_props_from_class(path + (name,), annotation.inner_type),
        diff=meta.diff,
        metadata=meta.metadata,
    )


def _create(
    path: tuple[str, ...], name: str, annotation: Reader_Annotation, meta: some_meta
) -> Prop_Any:
    match meta:
        case prop_meta() as p_m:
            return _create_prop(path, name, annotation, p_m)
        case schema_meta() as s_m:
            return _create_schema(path, name, annotation, s_m)
        case _:
            raise TypeError(f"Unknown meta type {type(meta)} for key {name}")


def _get_meta_for_prop(
    annotation: Reader_Annotation,
) -> some_meta | None:
    first_meta = funcy.first(annotation.metadata_of_type(prop_meta, schema_meta))
    if first_meta:
        return first_meta.target
    if annotation.name.startswith("_"):
        return None
    match annotation.target:
        case x if (
            isinstance(x, type) and issubclass(x, (Mapping, VMappingBase))
        ) or is_typeddict(x):
            return schema_meta(diff="recursive")
        case _:
            return prop_meta(
                no_value=Nothing, converter=None, diff="recursive", metadata={}
            )


def _attrs_to_props(
    path: tuple[str, ...], meta: Mapping[str, Reader_Annotation]
) -> "Iterable[Prop_Any]":
    for k, v in meta.items():
        meta_for_prop = _get_meta_for_prop(v)
        if not meta_for_prop:
            continue
        yield _create(path, k, v, meta_for_prop)


def _method_to_prop(path: tuple[str, ...], method: Reader_Method) -> "Prop_Any | None":
    meta = method.access(MetaAccessor)
    if not meta:
        return None
    annotation = method.arg(0)

    return _create(path, method.name, annotation, meta.get())


def _methods_to_props(path: tuple[str, ...], cls: type):
    methods = get_attrs_downto(cls, stop_at={object, Mapping})
    for k, v in methods.items():
        if not callable(v):
            continue
        if k.startswith("_") and k != "__init__":
            continue
        p = _method_to_prop(path, shadow_reflector.method(v))
        if not p:
            continue
        if k == "__init__":
            if not isinstance(p, Prop_Schema):
                raise TypeError(
                    f"__init__ method must be annotated with schema_meta, got {type(p)}"
                )
        yield p


def _read_props_from_class(path: tuple[str, ...], cls: type):
    if not shadow_reflector.is_supported(cls):
        return ()
    reader = shadow_reflector.type(cls)

    normal_props = _attrs_to_props(path, reader.annotations)
    method_props = _methods_to_props(path, cls)
    all_props = (
        *normal_props,
        *method_props,
    )
    return all_props


def read_props_from_top_class(cls: type) -> "Prop_Schema":
    name = cls.__name__
    props = [*_read_props_from_class((name,), cls)]
    init_block = funcy.first(x for x in props if x.name == "__init__")
    diff = "recursive"
    metadata = {}
    if init_block:
        props.remove(init_block)
        props.extend(init_block.values())  # type: ignore
        diff = init_block.diff
        metadata = init_block.metadata
    return Prop_Schema(path=(), name=name, props=props, diff=diff, metadata=metadata)
