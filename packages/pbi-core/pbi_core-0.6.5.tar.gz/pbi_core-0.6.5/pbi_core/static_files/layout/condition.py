from enum import Enum
from typing import Any

from attrs import field

from pbi_core.attrs import converter, define

from ._base_node import LayoutNode
from .sources import DataSource, LiteralSource, Source, SourceRef, TransformOutputRoleRef
from .sources.aggregation import AggregationSource, ScopedEvalExpression, SelectRef
from .sources.arithmetic import ArithmeticSource, ScopedEvalArith
from .sources.column import ColumnSource
from .sources.group import GroupSource
from .sources.proto import ProtoSourceRef


class ExpressionVersion(Enum):
    VERSION_1 = 1
    VERSION_2 = 2


@define()
class _AnyValueHelper(LayoutNode):
    DefaultValueOverridesAncestors: bool


@define()
class AnyValue(LayoutNode):
    AnyValue: _AnyValueHelper


class QueryConditionType(Enum):
    """Names defined by myself, but based on query outputs from the query tester."""

    STANDARD = 0
    TOP_N = 2
    MEASURE = 3


class ComparisonKind(Enum):
    IS_EQUAL = 0
    IS_GREATER_THAN = 1
    IS_GREATER_THAN_OR_EQUAL_TO = 2
    IS_LESS_THAN = 3
    IS_LESS_THAN_OR_EQUAL_TO = 4

    def get_operator(self) -> str:
        OPERATOR_MAPPING = {  # noqa: N806
            ComparisonKind.IS_EQUAL: "=",
            ComparisonKind.IS_GREATER_THAN: ">",
            ComparisonKind.IS_GREATER_THAN_OR_EQUAL_TO: ">=",
            ComparisonKind.IS_LESS_THAN: "<",
            ComparisonKind.IS_LESS_THAN_OR_EQUAL_TO: "<=",
        }
        if self not in OPERATOR_MAPPING:
            msg = f"No operator is defined for: {self}"
            raise ValueError(msg)
        return OPERATOR_MAPPING[self]


@define()
class ContainsCondition(LayoutNode):
    @define()
    class _ComparisonHelper(LayoutNode):
        Left: DataSource
        Right: LiteralSource

    Contains: _ComparisonHelper

    def natural_language(self) -> str:
        """Returns a natural language representation of the condition."""
        left = natural_language_source(self.Contains.Left)
        right = natural_language_source(self.Contains.Right)
        return f"{left} CONTAINS {right}"

    def get_sources(self) -> list[DataSource]:
        """Returns the sources used in the condition."""
        if isinstance(self.Contains.Right, LiteralSource):
            return [self.Contains.Left]
        return [self.Contains.Left, self.Contains.Right]


@define()
class Expression:
    template: str
    source: str
    data: dict[str, str] = field(factory=dict)
    expr_type: str = ""

    def to_text(self) -> str:
        if self.data:
            return self.template.format(**self.data)
        return self.template


@define()
class InExpressionHelper(LayoutNode):
    Expressions: list[DataSource]
    Values: list[list[LiteralSource]]

    def vals(self) -> list[str]:
        return [str(y.value()) for x in self.Values for y in x]

    def __repr__(self) -> str:
        source = self.Expressions[0].__repr__()
        return f"In({source}, {', '.join(self.vals())})"

    def get_sources(self) -> list[DataSource]:
        return self.Expressions


@define()
class InTopNExpressionHelper(LayoutNode):
    """Internal representation of the Top N option."""

    Expressions: list[DataSource]
    Table: SourceRef

    def get_sources(self) -> list[DataSource]:
        return self.Expressions


InUnion = InExpressionHelper | InTopNExpressionHelper


@converter.register_structure_hook
def get_in_union_type(v: dict[str, Any], _: type | None = None) -> InUnion:
    if "Table" in v:
        return InTopNExpressionHelper.model_validate(v)
    if "Values" in v:
        return InExpressionHelper.model_validate(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_in_union_type(v: InUnion) -> dict[str, Any]:
    return converter.unstructure(v)


def natural_language_source(d: Source | SourceRef | ScopedEvalExpression) -> str:
    if isinstance(d, ColumnSource):
        return d.Column.Property
    breakpoint()
    msg = f"Unsupported data source type: {d.__class__.__name__}"
    raise TypeError(msg)


@define()
class InCondition(LayoutNode):
    """In is how "is" and "is not" are internally represented."""

    In: InUnion

    def __repr__(self) -> str:
        return self.In.__repr__()

    def natural_language(self) -> str:
        expr = natural_language_source(self.In.Expressions[0])
        if isinstance(self.In, InTopNExpressionHelper):
            table = natural_language_source(self.In.Table)
            return f"{expr} IN TOP N {table}"
        return f"{expr} IN ({', '.join(str(x[0].value()) for x in self.In.Values)})"

    def get_sources(self) -> list[DataSource]:
        return self.In.get_sources()


class TimeUnit(Enum):
    SECOND = 1
    MINUTE = 2
    HOUR = 3
    DAY = 4
    WEEK = 5
    MONTH = 6
    QUARTER = 7
    YEAR = 8


@define()
class _NowHelper(LayoutNode):
    Now: dict[str, str]  # actually an empty string


def get_date_span_union_type(v: object | dict[str, Any]) -> str:
    if isinstance(v, dict):
        if "Literal" in v:
            return "LiteralSource"
        if "Now" in v:
            return "_NowHelper"
        raise TypeError(v)
    return v.__class__.__name__


DateSpanUnion = LiteralSource | _NowHelper


@converter.register_structure_hook
def get_bookmark_type(v: dict[str, Any], _: type | None = None) -> DateSpanUnion:
    if "Literal" in v:
        return LiteralSource.model_validate(v)
    if "Now" in v:
        return _NowHelper.model_validate(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_bookmark_type(v: DateSpanUnion) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class _DateSpanHelper(LayoutNode):
    Expression: DateSpanUnion
    TimeUnit: TimeUnit


@define()
class DateSpan(LayoutNode):
    DateSpan: _DateSpanHelper


@define()
class RangePercentHelper(LayoutNode):
    Min: ScopedEvalArith
    Max: ScopedEvalArith
    Percent: float


@define()
class RangePercent(LayoutNode):
    RangePercent: RangePercentHelper


ComparisonRightUnion = LiteralSource | AnyValue | DateSpan | RangePercent


@converter.register_structure_hook
def get_comparison_right_union_type(v: dict[str, Any], _: type | None = None) -> ComparisonRightUnion:
    if "Literal" in v:
        return LiteralSource.model_validate(v)
    if "AnyValue" in v:
        return AnyValue.model_validate(v)
    if "DateSpan" in v:
        return DateSpan.model_validate(v)
    if "RangePercent" in v:
        return RangePercent.model_validate(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_comparison_right_union_type(v: ComparisonRightUnion) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class ComparisonConditionHelper(LayoutNode):
    ComparisonKind: ComparisonKind
    Left: ScopedEvalExpression
    Right: ComparisonRightUnion


@define()
class ComparisonCondition(LayoutNode):
    Comparison: ComparisonConditionHelper

    def natural_language(self) -> str:
        """Returns a natural language representation of the condition."""
        left = natural_language_source(self.Comparison.Left)
        right = (
            self.Comparison.Right.value()
            if isinstance(self.Comparison.Right, LiteralSource)
            else str(self.Comparison.Right)
        )
        operator = self.Comparison.ComparisonKind.get_operator()
        return f"{left} {operator} {right}"

    def get_sources(self) -> list[DataSource]:
        left = self.Comparison.Left
        if isinstance(left, AggregationSource):
            return left.get_sources()
        if isinstance(left, SelectRef):
            return []
        return [left]


@define()
class NotConditionHelper(LayoutNode):
    Expression: "ConditionType"


@define()
class NotCondition(LayoutNode):
    Not: NotConditionHelper

    def __repr__(self) -> str:
        return f"Not({self.Not.Expression.__repr__()})"

    def natural_language(self) -> str:
        """Returns a natural language representation of the condition."""
        return f"NOT {self.Not.Expression.natural_language()}"

    def get_sources(self) -> list[DataSource]:
        return self.Not.Expression.get_sources()


@define()
class ExistsConditionHelper(LayoutNode):
    Expression: Source  # cannot be DataSource, might only be a ProtoSourceRef?


@define()
class ExistsCondition(LayoutNode):
    Exists: ExistsConditionHelper

    def natural_language(self) -> str:
        """Returns a natural language representation of the condition."""
        return f"Exists({natural_language_source(self.Exists.Expression)})"

    def get_sources(self) -> list[DataSource]:
        expr = self.Exists.Expression
        if isinstance(expr, (AggregationSource, ArithmeticSource, GroupSource)):
            return expr.get_sources()
        if isinstance(expr, (ProtoSourceRef, SelectRef, LiteralSource, TransformOutputRoleRef)):
            return []
        return [
            expr,
        ]


@define()
class CompositeConditionHelper(LayoutNode):
    Left: "ConditionType"
    Right: "ConditionType"


@define()
class AndCondition(LayoutNode):
    And: CompositeConditionHelper

    def natural_language(self) -> str:
        """Returns a natural language representation of the condition."""
        return f"({self.And.Left.natural_language()} AND {self.And.Right.natural_language()})"

    def get_sources(self) -> list[DataSource]:
        return [*self.And.Left.get_sources(), *self.And.Right.get_sources()]


@define()
class OrCondition(LayoutNode):
    Or: CompositeConditionHelper

    def natural_language(self) -> str:
        """Returns a natural language representation of the condition."""
        return f"({self.Or.Left.natural_language()} OR {self.Or.Right.natural_language()})"

    def get_sources(self) -> list[DataSource]:
        return [
            *self.Or.Left.get_sources(),
            *self.Or.Right.get_sources(),
        ]


ConditionType = (
    AndCondition | OrCondition | InCondition | NotCondition | ContainsCondition | ComparisonCondition | ExistsCondition
)


@converter.register_structure_hook
def get_condition_type(src: Any, _: type | None = None) -> ConditionType:
    if not isinstance(src, dict):
        raise TypeError(src)
    condition_mapper = {
        "And": AndCondition,
        "Or": OrCondition,
        "In": InCondition,
        "Not": NotCondition,
        "Contains": ContainsCondition,
        "Comparison": ComparisonCondition,
        "Exists": ExistsCondition,
    }
    for k, v in condition_mapper.items():
        if k in src:
            return v.model_validate(src)
    raise TypeError(src)


@converter.register_unstructure_hook
def unparse_condition_type(src: ConditionType) -> dict[str, Any]:
    return converter.unstructure(src)


@define()
class Condition(LayoutNode):
    Condition: ConditionType
    Target: list[Source] | None = None

    def __repr__(self) -> str:
        return f"Condition({self.Condition.__repr__()})"

    def natural_language(self) -> str:
        """Returns a natural language representation of the condition."""
        return self.Condition.natural_language()

    def get_sources(self) -> list[DataSource]:
        """Returns the sources used in the condition.

        Note: The left source must come first, since the
            order is used by PowerBI and this library
            to identify the default display name of filters
        """
        return self.Condition.get_sources()
