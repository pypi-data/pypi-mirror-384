import datetime
import json
from collections.abc import Callable
from enum import Enum
from types import NoneType, UnionType
from typing import Any, TypeVar, Union, get_args, get_origin
from uuid import UUID

import cattrs

from .attrs import BaseValidation, fields

T = TypeVar("T")
# cursed, but I don't know how else to identify annotated unions


def _is_union(tp: Any) -> bool:
    o = get_origin(tp)
    if o is Union:  # typing.Union[...]
        return True
    if o is UnionType:  # PEP 604 union (A | B)  # noqa: SIM103
        return True
    return False


def _structure_union(val: Any, tp: Any) -> Any:
    args = get_args(tp)

    # Without doing a isinstance check first, cattrs will try to coerce strings to bools for instance
    for a in args:
        if a is None and val is None:
            return None
        try:
            if isinstance(val, a):
                return val
        except TypeError:
            pass

    last_error = None
    for a in args:
        try:
            return converter.structure(val, a)
        except (cattrs.ClassValidationError, cattrs.StructureHandlerNotFoundError, AttributeError) as e:
            last_error = e
    msg = f"Could not match union type {tp} for value {val!r}"
    raise ValueError(msg) from last_error


def _is_json(tp: Any) -> bool:
    """Identifies if a type is annotated with Json.

    Used to structure and unstructure JSON strings to/from objects.
    """
    o = get_origin(tp)
    if o is Union or o is UnionType:
        for a in get_args(tp):
            if _is_json(a):
                return True
    return bool(hasattr(tp, "__metadata__") and tp.__metadata__[0].__class__.__name__ == "Json")


def _structure_json(val: Any, tp: Any) -> Any:
    if isinstance(val, str):
        val = json.loads(val)
    elif not isinstance(val, dict):
        msg = f"Expected JSON string, got {type(val)}"
        raise TypeError(msg)
    return converter.structure(val, tp.__args__[0])


def unstruct_json(val: Any) -> str:
    unwrapped = converter.unstructure(val)
    return json.dumps(unwrapped)


def tagged_union_checker(tp: UnionType, tp_name: str) -> Callable[[Any], bool]:
    def inner(v: Any) -> bool:
        if isinstance(v, UnionType):
            return v is tp
        if isinstance(v, str):
            return v == tp_name
        return False

    return inner


def struct_uuid(obj: Any, _: Any = None) -> UUID:
    if isinstance(obj, UUID):
        return obj
    if isinstance(obj, str):
        return UUID(obj)
    msg = f"Cannot convert {obj!r} to UUID"
    raise TypeError(msg)


def unstruct_uuid(obj: UUID) -> str:
    return str(obj)


def struct_datetime(obj: Any, _: Any = None) -> datetime.datetime:
    if isinstance(obj, datetime.datetime):
        return obj
    if isinstance(obj, str):
        return datetime.datetime.fromisoformat(obj)
    msg = f"Cannot convert {obj!r} to datetime"
    raise TypeError(msg)


def unstruct_datetime(obj: datetime.datetime) -> str:
    return obj.isoformat()


def struct_enum(obj: Any, enum_type: type[Enum]) -> Enum:
    return enum_type(obj)


def unstruct_enum(obj: Enum) -> str:
    return obj.value


class SubConverter(cattrs.Converter):
    @staticmethod
    def _add_original_data(new_obj: Any, old_obj: Any) -> None:
        if old_obj is None:
            return
        if isinstance(old_obj, str):
            try:
                old_obj = json.loads(old_obj)
            except json.JSONDecodeError:
                return

        if isinstance(new_obj, list):
            for a, b in zip(new_obj, old_obj, strict=False):
                SubConverter._add_original_data(a, b)
        elif isinstance(new_obj, dict):
            for k, v in old_obj.items():
                SubConverter._add_original_data(new_obj[k], v)

        elif isinstance(new_obj, BaseValidation):
            new_obj._original_data = old_obj
            for attr in fields(new_obj.__class__):
                SubConverter._add_original_data(
                    getattr(new_obj, attr.name, None),
                    old_obj.get(attr.alias, None),
                )

    def structure(self, obj: Any, cl: type[T]) -> T:
        ret = super().structure(obj, cl)
        self._add_original_data(ret, obj)
        return ret

    def unstructure(self, obj: Any, unstructure_as: Any = None) -> Any:
        if isinstance(obj, list):
            return [self.unstructure(i, unstructure_as) for i in obj]
        if isinstance(obj, dict):
            return {k: self.unstructure(v, unstructure_as) for k, v in obj.items()}

        if not hasattr(obj, "_original_data"):
            return super().unstructure(obj, unstructure_as)

        base = {}
        for attr in fields(obj.__class__):
            if attr.init is True:
                base_val = self.unstructure(getattr(obj, attr.name), unstructure_as)
                if _is_json(attr.type):
                    base_val = json.dumps(base_val)
                base[attr.alias] = base_val

        ret = {}
        try:  # TODO: make all things have a original_data
            for k in obj._original_data:
                # we should only have keys that were in the original data or are different from the default
                ret[k] = base[k]
        except:  # noqa: E722
            return base
        return ret


converter = SubConverter(forbid_extra_keys=True, use_alias=True)

converter.register_structure_hook_func(_is_union, _structure_union)
# no need to explicitly register unstructure unions

converter.register_structure_hook_func(_is_json, _structure_json)
converter.register_unstructure_hook_func(_is_json, unstruct_json)

converter.register_structure_hook(UUID, struct_uuid)
converter.register_unstructure_hook(UUID, unstruct_uuid)

converter.register_structure_hook(NoneType, lambda _v, _: None)
converter.register_unstructure_hook(NoneType, lambda _: None)

converter.register_structure_hook(datetime.datetime, struct_datetime)
converter.register_unstructure_hook(datetime.datetime, unstruct_datetime)

converter.register_structure_hook(Enum, struct_enum)
converter.register_unstructure_hook(Enum, unstruct_enum)
