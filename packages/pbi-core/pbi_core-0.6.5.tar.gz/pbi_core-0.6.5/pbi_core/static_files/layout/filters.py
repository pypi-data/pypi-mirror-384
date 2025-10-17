from enum import Enum
from typing import TYPE_CHECKING, Any, cast

import attrs
from attrs import field

from pbi_core.attrs import BaseValidation, converter, define
from pbi_core.attrs.extra import repr_exists, repr_len
from pbi_core.static_files.layout.sources.literal import LiteralSource
from pbi_core.static_files.model_references import ModelColumnReference, ModelMeasureReference

from ._base_node import LayoutNode
from .condition import AndCondition, ComparisonCondition, Condition, ConditionType, InCondition, NotCondition
from .sources import AggregationSource, ColumnSource, Entity, MeasureSource, Source
from .sources.aggregation import ScopedEvalAgg
from .visuals.properties.filter_properties import FilterObjects

if TYPE_CHECKING:
    from pbi_prototype_query_translation import TranslationResult

    from pbi_core.ssas.server import BaseTabularModel


class Direction(Enum):
    ASCENDING = 1
    DESCENDING = 2


@define()
class Orderby(LayoutNode):
    Direction: Direction
    Expression: Source


@define()
class PrototypeQueryResult(BaseValidation):
    data: list[dict[str, Any]]
    dax_query: str
    column_mapping: dict[str, str]


@define()
class InputParameter(LiteralSource):
    Name: str


@define()
class InputTableColumn(BaseValidation):
    Expression: Source
    Role: str | None = None


@define()
class InputTable(BaseValidation):
    Name: str
    Columns: list[InputTableColumn]


@define()
class TransformInput(BaseValidation):
    Parameters: list[InputParameter]
    Table: InputTable


@define()
class TransformOutput(BaseValidation):
    Table: InputTable


@define()
class TransformMeta(BaseValidation):
    Name: str
    Algorithm: str
    Input: TransformInput
    Output: TransformOutput

    def table_mapping(self) -> dict[str, str]:
        ret: list[ColumnSource | MeasureSource] = []
        for col in self.Input.Table.Columns:
            ret.extend(PrototypeQuery.unwrap_source(col.Expression))
        input_tables: set[str] = set()
        for source in ret:
            if isinstance(source, ColumnSource):
                input_tables.add(source.Column.table())
            else:
                input_tables.add(source.Measure.table())
        if len(input_tables) > 1:
            msg = f"Don't know how to handle multiple inputs: {self}"
            raise ValueError(msg)

        (input_table,) = input_tables
        return {
            self.Output.Table.Name: input_table,
        }


@define()
class PrototypeQuery(LayoutNode):
    Version: int
    From: list["From"] = field(repr=repr_len)
    Select: list[Source] = field(factory=list, repr=repr_len)
    Where: list[Condition] = field(factory=list, repr=repr_len)
    OrderBy: list[Orderby] = field(factory=list, repr=repr_len)
    Transform: list[TransformMeta] = field(factory=list, repr=repr_len)
    Top: int | None = field(default=None, repr=repr_exists)

    def table_mapping(self) -> dict[str, str]:
        ret: dict[str, str] = {}
        for from_clause in self.From:
            ret |= from_clause.table_mapping()
        for transform in self.Transform:
            # For measures using Transform outputs, we need to point to the source of that transform table
            transform_tables = transform.table_mapping()
            ret |= {k: ret[v] for k, v in transform_tables.items()}
        return ret

    @classmethod
    def unwrap_source(cls, source: Source | ConditionType | ScopedEvalAgg) -> list[ColumnSource | MeasureSource]:
        """Identifies the root sources (measures and columns) used in this filter.

        Raises:
            TypeError: Occurs when one of the source types has not been handled by the code.
                Should not occur outside development.

        """
        if isinstance(source, ColumnSource | MeasureSource):
            return [source]
        if isinstance(source, AggregationSource):
            return cls.unwrap_source(source.Aggregation.Expression)

        if isinstance(source, InCondition):
            ret: list[ColumnSource | MeasureSource] = []
            for expr in source.In.Expressions:
                ret.extend(cls.unwrap_source(expr))
            return ret
        if isinstance(source, NotCondition):
            return cls.unwrap_source(source.Not.Expression)
        if isinstance(source, AndCondition):
            return [
                *cls.unwrap_source(source.And.Left),
                *cls.unwrap_source(source.And.Right),
            ]
        if isinstance(source, ComparisonCondition):
            # Right has no dynamic options, so it's skipped
            return cls.unwrap_source(source.Comparison.Left)
        print(source)
        breakpoint()
        raise TypeError

    def get_ssas_elements(self) -> set[ModelColumnReference | ModelMeasureReference]:
        """Returns the SSAS elements (columns and measures) this query is directly dependent on."""
        ret: set[ColumnSource | MeasureSource] = set()
        for select in self.Select:
            ret.update(self.unwrap_source(select))
        for where in self.Where:
            ret.update(self.unwrap_source(where.Condition))
        for order_by in self.OrderBy:
            ret.update(self.unwrap_source(order_by.Expression))
        for transformation in self.Transform:
            for col in transformation.Input.Table.Columns:
                ret.update(self.unwrap_source(col.Expression))
        table_mappings: dict[str, str] = self.table_mapping()
        ret2: set[ModelColumnReference | ModelMeasureReference] = set()
        for source in ret:
            if isinstance(source, ColumnSource):
                ret2.add(
                    ModelColumnReference(
                        column=source.Column.column(),
                        table=source.Column.table(table_mappings),
                    ),
                )
            else:
                ret2.add(
                    ModelMeasureReference(
                        measure=source.Measure.column(),
                        table=source.Measure.table(table_mappings),
                    ),
                )
        return ret2

    def get_dax(self, model: "BaseTabularModel") -> "TranslationResult":
        """Creates a DAX query that returns the data for a visual based on the SSAS model supplied.

        Note:
            Although generally the DAX queries generated are identical across different models,
                they can theoretically be different. If you can create a specific case of this,
                please add it to the pbi_core repo!

        Args:
            model (BaseTabularModel): The SSAS model to generate the DAX against.

        Returns:
            DataViewQueryTranslationResult: an object containing the DAX query for this visual

        """
        import pbi_prototype_query_translation  # noqa: PLC0415 # this is a heavy import

        raw_query = self.model_dump_json()
        return pbi_prototype_query_translation.prototype_query(
            raw_query,
            model.db_name,
            model.server.port,
        )

    def get_data(self, model: "BaseTabularModel") -> PrototypeQueryResult:
        dax_query = self.get_dax(model)
        data = model.server.query_dax(dax_query.dax)

        return PrototypeQueryResult(
            data=data,
            dax_query=dax_query.dax,
            column_mapping=dax_query.column_mapping,
        )


@define()
class _SubqueryHelper2(LayoutNode):
    Query: PrototypeQuery


@define()
class _SubqueryHelper(LayoutNode):
    Subquery: _SubqueryHelper2


class SubQueryType(Enum):
    NA = 2


@define()
class Subquery(LayoutNode):
    Name: str
    Expression: _SubqueryHelper
    Type: SubQueryType

    def table_mapping(self) -> dict[str, str]:
        return self.Expression.Subquery.Query.table_mapping()


From = Entity | Subquery


def unparse_from(v: From) -> dict[str, Any]:
    return converter.unstructure(v)


@converter.register_structure_hook
def get_from(v: Any, _: type | None = None) -> From:
    if "Entity" in v:
        return Entity.model_validate(v)
    if "Expression" in v:
        return Subquery.model_validate(v)
    msg = f"Unknown Filter: {v.keys()}"
    raise ValueError(msg)


attrs.resolve_types(PrototypeQuery)  # necessary for forward ref unions


class HowCreated(Enum):
    AUTO = 0
    """Created automatically when a field is used in the visual."""
    USER = 1
    """Filters created from fields not used in a visual by the user."""
    DRILL = 2
    """Created when drilling down on a data point in a visual."""
    INCLUDE = 3
    """Created by including a data point in a visual."""
    EXCLUDE = 4
    """Created by excluding a data point from a visual."""
    DRILLTHROUGH = 5
    """Created by drill context that is applied to the page when using drill-through
    action from another page."""
    NA3 = 6
    NA4 = 7


class FilterType(Enum):
    ADVANCED = "Advanced"
    CATEGORIAL = "Categorical"
    EXCLUDE = "Exclude"
    INCLUDE = "Include"
    PASSTHROUGH = "Passthrough"
    RANGE = "Range"
    RELATIVE_DATE = "RelativeDate"
    RELATIVE_TIME = "RelativeTime"
    TOP_N = "TopN"
    TUPLE = "Tuple"
    VISUAL_TOP_N = "VisualTopN"


@define()
class Scope(LayoutNode):
    scopeId: ConditionType


@define()
class CachedDisplayNames(LayoutNode):
    displayName: str
    id: Scope


@define()
class Filter(LayoutNode):
    name: str | None = None
    type: FilterType = FilterType.CATEGORIAL
    howCreated: HowCreated = HowCreated.AUTO
    expression: Source | None = None
    """Holds a single expression and associated metadata.
    Name, NativeReferenceName, and Annotations may be specified for any expression.
    Each other property represents a specific type of expression and exactly one of these other properties must be
    specified.

    Definition: https://developer.microsoft.com/json-schemas/fabric/item/report/definition/semanticQuery/1.3.0/schema.json#/definitions/QueryExpressionContainer
    """
    isLockedInViewMode: bool = False
    isHiddenInViewMode: bool = False
    objects: FilterObjects | None = None
    filter: PrototypeQuery | None = None
    """Defines a filter element as a partial query structure"""
    displayName: str | None = None
    ordinal: int = 0
    isLinkedAsAggregation: bool = False
    cachedDisplayNames: list[CachedDisplayNames] | None = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.displayName or self.name})"

    def __str__(self) -> str:
        return super().__str__()

    def get_display_name(self) -> str:
        if self.displayName is not None:
            return self.displayName
        if self.filter is None:
            msg = "Unknown default display name"
            raise ValueError(msg)
        default_name_source = self.filter.Where[0].get_sources()[0]
        if isinstance(default_name_source, ColumnSource):
            return default_name_source.Column.Property
        if isinstance(default_name_source, MeasureSource):
            return default_name_source.Measure.Property
        return "--"

    def get_ssas_elements(self) -> set[ModelColumnReference | ModelMeasureReference]:
        """Returns the SSAS elements (columns and measures) this filter is directly dependent on."""
        if self.filter is None:
            return set()
        return self.filter.get_ssas_elements()


@define()
class VisualFilterExpression(LayoutNode):
    Version: int | None = None
    From: list["From"] | None = None
    Where: list[Condition]


# TODO: Filter specialization, only done to create better type completion.
# TODO: visual needs extra fields because it allows measure sources I think


@define()
class HighlightScope(LayoutNode):
    scopeId: ConditionType


@define()
class CachedValueItems(LayoutNode):
    identities: list[HighlightScope]
    valueMap: dict[str, str] | list[str]


@define()
class FilterExpressionMetadata(LayoutNode):
    expressions: list[Source]
    cachedValueItems: list[CachedValueItems]


@define()
class JsonFilter(LayoutNode):
    filterType: FilterType
    """Type of json filter."""


@define()
class DecomposedIdentities(LayoutNode):
    values: list[list[dict[int, Source]]]
    """`values` have 3 levels
    outermost level:
      - for SelectorsByColumn[], it's the number of selectors in this array
      - for FilterExpressionMetadata, it's the number of cachedValueItems.
    second level:
      - for SelectorsByColumn, it is the number of scopedIdentities in the particular SelectorsByColumn
      - for FilterExpressionMetadata, it is the number of identities in a cachedValueItem
    innermost level:
      - the key is the index of the column structure of scopedIdentity in `columns` list;
      - the the value is the expressions list in one identity"""
    columns: list[Source]
    """Defines the set of group-on key columns."""


@define()
class DecomposedFilterExpressionMetadata(LayoutNode):
    decomposedIdentities: DecomposedIdentities
    """Defines the group-on key fields and the filters applied on them."""
    expressions: list[Source]
    """Original fields (which have group-on keys) used in the filter."""
    valueMap: list[dict[int, str]] | None = None
    """Matches the index in decomposedIdentities with the queryRef for an expression."""
    jsonFilter: JsonFilter | None = None
    """Json filter metadata."""


FilterExpression = FilterExpressionMetadata | DecomposedFilterExpressionMetadata


@converter.register_structure_hook
def get_filter_expression_type(v: dict[str, Any], _: type | None = None) -> FilterExpression:
    if "decomposedIdentities" in v:
        return DecomposedFilterExpressionMetadata.model_validate(v)
    if "cachedValueItems" in v:
        return FilterExpressionMetadata.model_validate(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_filter_expression_layout(v: FilterExpression) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class VisualFilter(Filter):
    restatement: str | None = None
    filterExpressionMetadata: FilterExpression | None = None

    def to_bookmark(self) -> "BookmarkFilter":
        return cast("BookmarkFilter", self)


@define()
class BookmarkFilter(VisualFilter):
    """Meaning of properties is same as Filters defined outside the bookmark."""

    isTransient: bool = False


@define()
class PageFilter(Filter):
    """Structurally identical to Filter, but used for find/find_all."""


@define()
class GlobalFilter(Filter):
    """Structurally identical to Filter, but used for find/find_all."""
