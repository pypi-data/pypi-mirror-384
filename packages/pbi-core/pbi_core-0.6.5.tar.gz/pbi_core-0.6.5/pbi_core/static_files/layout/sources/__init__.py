from typing import Any

from pbi_core.attrs import BaseValidation, converter, define

from .aggregation import AggregationSource, DataSource, SelectRef
from .arithmetic import ArithmeticSource
from .base import Entity, SourceRef
from .column import ColumnSource
from .group import GroupSource
from .hierarchy import HierarchyLevelSource
from .literal import LiteralSource
from .measure import MeasureSource
from .proto import ProtoSourceRef


@define()
class RoleRef(BaseValidation):
    Role: str


@define()
class TransformOutputRoleRef(BaseValidation):
    TransformOutputRoleRef: RoleRef
    Name: str | None = None


Source = (
    HierarchyLevelSource
    | ColumnSource
    | GroupSource
    | AggregationSource
    | MeasureSource
    | ArithmeticSource
    | ProtoSourceRef
    | TransformOutputRoleRef
    | LiteralSource
    | SelectRef
)


@converter.register_structure_hook
def get_bookmark_type(v: dict[str, Any], _: type | None = None) -> Source:
    mapper = {
        "Column": ColumnSource,
        "HierarchyLevel": HierarchyLevelSource,
        "GroupRef": GroupSource,
        "Aggregation": AggregationSource,
        "Measure": MeasureSource,
        "Arithmetic": ArithmeticSource,
        "SourceRef": ProtoSourceRef,
        "TransformOutputRoleRef": TransformOutputRoleRef,
        "Literal": LiteralSource,
        "SelectRef": SelectRef,
    }
    for key in v:
        if key in mapper:
            return mapper[key].model_validate(v)
    msg = f"Unknown Filter: {v.keys()}"
    raise TypeError(msg)


@converter.register_unstructure_hook
def unparse_bookmark_type(v: Source) -> dict[str, Any]:
    return converter.unstructure(v)


__all__ = [
    "AggregationSource",
    "ArithmeticSource",
    "ColumnSource",
    "DataSource",
    "Entity",
    "GroupSource",
    "HierarchyLevelSource",
    "LiteralSource",
    "MeasureSource",
    "Source",
    "SourceRef",
    "define",
]
