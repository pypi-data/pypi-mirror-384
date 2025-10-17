from enum import Enum
from typing import Any

from attrs import field

from pbi_core.attrs import converter, define
from pbi_core.static_files.layout._base_node import LayoutNode

from .column import ColumnSource
from .hierarchy import HierarchyLevelSource
from .measure import MeasureSource


@define()
class ExpressionName(LayoutNode):
    ExpressionName: str


@define()
class SelectRef(LayoutNode):
    SelectRef: ExpressionName


@define()
class AllRolesRef(LayoutNode):
    AllRolesRef: dict[str, bool] = field(factory=dict)  # no values have been seen in this field


@define()
class ScopedEval2(LayoutNode):
    Expression: "ScopedEvalExpression"
    Scope: list[AllRolesRef]


# TODO: merge with ScopedEvalArith
@define()
class ScopedEvalAgg(LayoutNode):  # copied from arithmetic.py to avoid circular dependencies
    ScopedEval: ScopedEval2


DataSource = ColumnSource | MeasureSource | HierarchyLevelSource | ScopedEvalAgg


@converter.register_structure_hook
def get_data_source_type(v: dict[str, Any], _: type | None = None) -> DataSource:
    if "Column" in v:
        return ColumnSource.model_validate(v)
    if "Measure" in v:
        return MeasureSource.model_validate(v)
    if "HierarchyLevel" in v:
        return HierarchyLevelSource.model_validate(v)
    if "ScopedEval" in v:  # Consider subclassing? This only happens for color gradient properties IME
        return ScopedEvalAgg.model_validate(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_data_source_type(v: DataSource) -> dict[str, Any]:
    return converter.unstructure(v)


class AggregationFunction(Enum):
    SUM = 0
    AVERAGE = 1
    COUNT = 2
    MIN = 3
    MAX = 4
    DISTINCT_COUNT = 5
    MEDIAN = 6
    STD_DEV_P = 7
    VAR_P = 8


@define()
class _AggregationSourceHelper(LayoutNode):
    Expression: DataSource
    Function: AggregationFunction


@define()
class AggregationSource(LayoutNode):
    Aggregation: _AggregationSourceHelper
    Name: str | None = None
    NativeReferenceName: str | None = None  # only for Layout.Visual.Query

    def get_sources(self) -> list[DataSource]:
        return [self.Aggregation.Expression]


ScopedEvalExpression = DataSource | AggregationSource | SelectRef


@converter.register_structure_hook
def get_scoped_eval_type(v: dict[str, Any], _: type | None = None) -> ScopedEvalExpression:
    if "Aggregation" in v:
        return AggregationSource.model_validate(v)
    if any(c in v for c in ("Column", "Measure", "HierarchyLevel")):
        return get_data_source_type(v)
    if "SelectRef" in v:
        return SelectRef.model_validate(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_scoped_eval_type(v: ScopedEvalExpression) -> dict[str, Any]:
    return converter.unstructure(v)
