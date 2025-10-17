import json
from typing import TYPE_CHECKING, Self, dataclass_transform

from attrs import Attribute, field
from attrs import define as _define
from attrs import fields as _fields

if TYPE_CHECKING:
    from collections.abc import Callable

    from attrs import _C


def fields(cls: type) -> tuple[Attribute]:
    """Returns a tuple of attrs Attributes for the class.

    Note:
        This is a thin wrapper around `attrs.fields` to avoid name conflicts and simplify imports.

    """
    return _fields(cls)


@dataclass_transform(kw_only_default=True, order_default=True, eq_default=True)
def define(  # noqa: PLR0913
    *,
    kw_only: bool = True,
    eq: bool = True,
    hash: bool = True,  # noqa: A002
    slots: bool = False,
    init: bool = True,
    order: bool = True,
    repr: bool = False,  # noqa: A002
    str: bool = False,  # noqa: A002
) -> "Callable[[_C], _C]":
    return _define(slots=slots, kw_only=kw_only, hash=hash, eq=eq, init=init, order=order, str=str, repr=repr)


class BaseValidation:
    _original_data: Self | None = field(default=None, init=False, repr=False, eq=False)
    """Holds the data of the SSAS/Layout entity as it was in the SSAS instance of Layout file when it was pulled."""

    @classmethod
    def model_validate(cls, data: dict) -> Self:
        from .cattrs import converter  # noqa: PLC0415

        return converter.structure(data, cls)

    @classmethod
    def model_validate_json(cls, data: str) -> Self:
        return cls.model_validate(json.loads(data))

    def model_dump(self) -> dict:
        from .cattrs import converter  # noqa: PLC0415

        return converter.unstructure(self)

    def model_dump_json(self, indent: int = 4) -> str:
        return json.dumps(self.model_dump(), indent=indent)
