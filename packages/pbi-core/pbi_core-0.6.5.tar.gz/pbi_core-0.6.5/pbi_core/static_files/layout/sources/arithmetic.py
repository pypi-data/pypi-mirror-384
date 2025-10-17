from enum import Enum
from typing import Any

from pbi_core.attrs import converter, define
from pbi_core.static_files.layout._base_node import LayoutNode

from .aggregation import AggregationSource, DataSource, get_data_source_type

Expression = DataSource | AggregationSource


@converter.register_structure_hook
def get_expression_type(v: dict[str, Any], _: type | None = None) -> Expression:
    if "Aggregation" in v:
        return AggregationSource.model_validate(v)
    if any(c in v for c in ("Column", "Measure", "HierarchyLevel")):
        return get_data_source_type(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_expression_type(v: Expression) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class AllRolesRef(LayoutNode):
    AllRolesRef: bool = True  # no values have been seen in this field


@define()
class ScopedEval2(LayoutNode):
    Expression: Expression
    Scope: list[AllRolesRef]


# TODO: merge with ScopedEvalAgg
@define()
class ScopedEvalArith(LayoutNode):
    ScopedEval: ScopedEval2


class ArithmeticOperator(Enum):
    DIVIDE = 3


@define()
class _ArithmeticSourceHelper(LayoutNode):
    Left: Expression
    Right: ScopedEvalArith
    Operator: ArithmeticOperator


@define()
class ArithmeticSource(LayoutNode):
    Arithmetic: _ArithmeticSourceHelper
    Name: str | None = None

    def get_sources(self) -> list[DataSource]:
        left = self.Arithmetic.Left
        if isinstance(left, AggregationSource):
            return left.get_sources()
        return [left]
