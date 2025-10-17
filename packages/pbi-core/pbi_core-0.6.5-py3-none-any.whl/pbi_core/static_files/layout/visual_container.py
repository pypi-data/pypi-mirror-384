from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from attrs import field

from pbi_core.attrs import Json, converter, define
from pbi_core.attrs.extra import repr_exists, repr_len
from pbi_core.lineage.main import LineageNode
from pbi_core.ssas.trace import NoQueryError, Performance, get_performance
from pbi_core.static_files.model_references import ModelColumnReference, ModelMeasureReference

from ._base_node import LayoutNode
from .condition import Condition
from .expansion_state import ExpansionState
from .filters import From as FromType
from .filters import PrototypeQuery, PrototypeQueryResult, VisualFilter
from .selector import Selector
from .sources import Source
from .visuals.base import FilterSortOrder, ProjectionConfig, PropertyDef
from .visuals.main import Visual
from .visuals.properties.base import Expression

if TYPE_CHECKING:
    from pbi_core.ssas.server import BaseTabularModel

    from .section import Section
    from .visuals.base import BaseVisual


@define()
class BackgroundProperties(LayoutNode):
    show: Expression | None = None
    transparency: Expression | None = None


@define()
class Background(LayoutNode):
    properties: BackgroundProperties


@define()
class SingleVisualGroupProperties(LayoutNode):
    background: list[Background] | None = None


@define()
class SingleVisualGroup(LayoutNode):
    displayName: str
    groupMode: int
    objects: SingleVisualGroupProperties | None = None
    isHidden: bool = False


class VisualHowCreated(Enum):
    INSERT_VISUAL_BUTTON = "InsertVisualButton"


@define()
class VisualLayoutInfoPosition(LayoutNode):
    x: float
    y: float
    z: float = 0.0  # z is not always present, default to 0
    width: float
    height: float
    tabOrder: int | None = None

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z}, {self.width}, {self.height})"


@define()
class VisualLayoutInfo(LayoutNode):
    id: int
    position: VisualLayoutInfoPosition


@define()
class VisualConfig(LayoutNode):
    _name_field = "name"

    layouts: list[VisualLayoutInfo] | None = None
    name: str | None = None
    parentGroupName: str | None = None
    singleVisualGroup: SingleVisualGroup | None = None
    singleVisual: Visual | None = None  # split classes to handle the other cases
    howCreated: VisualHowCreated | None = None


class ExecutionMetricsKindEnum(Enum):
    NA = 1
    NA3 = 3


class EntityType(Enum):
    TABLE = 0


@define()
class FromEntity(LayoutNode):
    Name: str
    Entity: str
    Type: EntityType = EntityType.TABLE


@define()
class PrimaryProjections(LayoutNode):
    Projections: list[int]
    SuppressedProjections: list[int] | None = None
    Subtotal: int | None = None
    Aggregates: list["QueryBindingAggregates"] | None = None
    ShowItemsWithNoData: list[int] | None = None


@define()
class Level(LayoutNode):
    Expressions: list[Source]
    Default: int


@define()
class InstanceChild(LayoutNode):
    Values: list[Source]
    Children: list["InstanceChild"] | None = None
    WindowExpansionInstanceWindowValue: list[int] | None = None  # never seen the element


@define()
class Instance(LayoutNode):
    Children: list[InstanceChild]
    WindowExpansionInstanceWindowValue: list[int] | None = None  # never seen the element
    Values: list[Source] | None = None


@define()
class BindingExpansion(LayoutNode):
    From: list[FromEntity]
    Levels: list[Level]
    Instances: Instance


@define()
class Synch(LayoutNode):
    Groupings: list[int]


@define()
class BindingPrimary(LayoutNode):
    Groupings: list[PrimaryProjections]
    Expansion: BindingExpansion | None = None
    Synchronization: list[Synch] | None = None


class DataVolume(Enum):
    NA1 = 1
    NA2 = 2
    NA3 = 3
    NA = 4
    NA5 = 5
    NA6 = 6


@define()
class SampleDataReduction(LayoutNode):
    Sample: dict[str, int]


@define()
class WindowDataReduction(LayoutNode):
    Window: dict[str, int]


@define()
class TopDataReduction(LayoutNode):
    Top: dict[str, int]


@define()
class BottomDataReduction(LayoutNode):
    Bottom: dict[str, int]


@define()
class OverlappingPointsSample(LayoutNode):
    X: dict[str, int] = field(factory=dict)
    Y: dict[str, int] = field(factory=dict)


@define()
class OverlappingPointReduction(LayoutNode):
    OverlappingPointsSample: OverlappingPointsSample


@define()
class WindowExpansionType(LayoutNode):
    From: list[FromEntity]
    Levels: list[Level]
    WindowInstances: Instance

    def __str__(self) -> str:
        return f"WindowExpansionType(From={self.From}, Levels={self.Levels}, WindowInstances={self.WindowInstances})"


@define()
class TopNPerLevelDataReduction(LayoutNode):
    @define()
    class _TopNPerLevelDataReductionHelper(LayoutNode):
        Count: int
        WindowExpansion: WindowExpansionType

    TopNPerLevel: _TopNPerLevelDataReductionHelper


@define()
class BinnedLineSample(LayoutNode):
    @define()
    class _BinnedLineSampleHelper(LayoutNode):
        PrimaryScalarKey: int | None = None
        Count: int | None = None
        WarningCount: int | None = None

    BinnedLineSample: _BinnedLineSampleHelper


PrimaryDataReduction = (
    SampleDataReduction
    | WindowDataReduction
    | TopDataReduction
    | BottomDataReduction
    | OverlappingPointReduction
    | TopNPerLevelDataReduction
    | BinnedLineSample
)


@converter.register_structure_hook
def get_reduction_type(v: dict[str, Any], _: type | None = None) -> PrimaryDataReduction:
    mapper: dict[str, type[PrimaryDataReduction]] = {
        "Sample": SampleDataReduction,
        "Window": WindowDataReduction,
        "Top": TopDataReduction,
        "Bottom": BottomDataReduction,
        "OverlappingPointsSample": OverlappingPointReduction,
        "TopNPerLevel": TopNPerLevelDataReduction,
        "BinnedLineSample": BinnedLineSample,
    }

    for key in v:
        if key in mapper:
            return mapper[key].model_validate(v)
    msg = f"Unknown Filter: {v.keys()}"
    raise ValueError(msg)


@converter.register_unstructure_hook
def unparse_reduction_type(v: PrimaryDataReduction) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class VisualScope(LayoutNode):
    Algorithm: PrimaryDataReduction
    Scope: dict[str, list[int]]


@define()
class DataReductionType(LayoutNode):
    DataVolume: DataVolume
    Primary: PrimaryDataReduction | None = None
    Secondary: PrimaryDataReduction | None = None
    Intersection: PrimaryDataReduction | None = None
    Scoped: list[VisualScope] | None = None


@define()
class AggregateSourceScope(LayoutNode):
    PrimaryDepth: int


@define()
class AggregateSources2(LayoutNode):  # stupid name, but needs to be different from AggregateSources
    # This is a workaround for the fact that AggregateSources is already used in the QueryBindingAggregates class
    Min: dict[str, int] | None = None
    Max: dict[str, int] | None = None
    Scope: AggregateSourceScope | None = None
    RespectInstanceFilters: bool = False


@define()
class AggregateSources(LayoutNode):
    min: dict[str, int] | None = None
    max: dict[str, int] | None = None


@define()
class QueryBindingAggregates(LayoutNode):
    Aggregations: list[AggregateSources2]
    Select: int


@define()
class Highlight(LayoutNode):
    # TODO: merge with VisualFilterExpression. For some reason,
    # pydantic thinks From should be None when using the visal filter expression
    Version: int | None = None
    From: list[FromType] | None = None
    Where: list[Condition]


@define()
class QueryBinding(LayoutNode):
    IncludeEmptyGroups: bool = False
    Primary: BindingPrimary
    Secondary: BindingPrimary | None = None
    Projections: list[int] = field(factory=list)
    DataReduction: DataReductionType | None = None
    Aggregates: list[QueryBindingAggregates] | None = None
    SuppressedJoinPredicates: list[int] | None = None
    Highlights: list[Highlight] | None = None
    Version: int


@define()
class QueryCommand1(LayoutNode):
    ExecutionMetricsKind: ExecutionMetricsKindEnum = ExecutionMetricsKindEnum.NA
    Query: PrototypeQuery
    Binding: QueryBinding | None = None


@define()
class QueryCommand2(LayoutNode):
    SemanticQueryDataShapeCommand: QueryCommand1


QueryCommand = QueryCommand1 | QueryCommand2


@converter.register_structure_hook
def get_query_command_type(v: dict[str, Any], _: type | None = None) -> QueryCommand:
    if "SemanticQueryDataShapeCommand" in v:
        return QueryCommand2.model_validate(v)
    if "ExecutionMetricsKind" in v:
        return QueryCommand1.model_validate(v)
    msg = f"Unknown Filter: {v.keys()}"
    raise ValueError(msg)


@converter.register_unstructure_hook
def unparse_query_command(v: QueryCommand) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class Query(LayoutNode):
    Commands: list[QueryCommand]

    def get_ssas_elements(self) -> set[ModelColumnReference | ModelMeasureReference]:
        """Returns the SSAS elements (columns and measures) this query is directly dependent on."""
        ret: set[ModelColumnReference | ModelMeasureReference] = set()
        for command in self.Commands:
            if isinstance(command, QueryCommand1):
                ret.update(command.Query.get_ssas_elements())
            elif isinstance(command, QueryCommand2):
                ret.update(command.SemanticQueryDataShapeCommand.Query.get_ssas_elements())
        return ret

    def get_prototype_queries(self) -> list[PrototypeQuery]:
        ret: list[PrototypeQuery] = []
        for command in self.Commands:
            if isinstance(command, QueryCommand1):
                ret.append(command.Query)
            elif isinstance(command, QueryCommand2):
                ret.append(command.SemanticQueryDataShapeCommand.Query)
        return ret


@define()
class Split(LayoutNode):
    # TODO: these strings are all stringy ints
    selects: dict[str, bool]


@define()
class KPI(LayoutNode):
    graphic: str
    normalizedFiveStateKpiRange: bool


@define()
class Restatement(LayoutNode):
    Restatement: str
    Name: str
    Type: int  # TODO: make enum
    DataCategory: int | None = None  # TODO: make enum
    Format: str | None = None
    kpi: KPI | None = None


@define()
class QueryMetadataFilter(LayoutNode):
    type: int | None = None  # TODO: make enum
    expression: Source | None = None


@define()
class QueryMetadata(LayoutNode):
    Select: list[Restatement]
    Filters: list[QueryMetadataFilter] | None = None


@define()
class DataRole(LayoutNode):
    Name: str
    Projection: int
    isActive: bool


@define()
class DataTransformVisualElement(LayoutNode):
    DataRoles: list[DataRole]


@define()
class DataTransformSelectType(LayoutNode):
    category: str | None = None
    underlyingType: int | None = None  # TODO: make enum


@define()
class ColumnFormattingDataBars(LayoutNode):
    metadata: str


@define()
class ColumnFormatting(LayoutNode):
    dataBars: list[ColumnFormattingDataBars]


@define()
class Title(LayoutNode):
    text: list[None]


@define()
class Values(LayoutNode):
    fontColor: list[Selector]


@define()
class RelatedObjects(LayoutNode):
    columnFormatting: ColumnFormatting | None = None
    title: Title | None = None
    values: Values | None = None


@define()
class DataTransformSelect(LayoutNode):
    displayName: str | None = None
    format: str | None = None
    queryName: str
    roles: dict[str, bool] | None = None
    sort: int | None = None  # TODO: make enum
    aggregateSources: AggregateSources | None = None
    sortOrder: FilterSortOrder = FilterSortOrder.NA
    type: DataTransformSelectType | None = None
    expr: Source
    relatedObjects: RelatedObjects | None = None
    kpi: KPI | None = None


@define()
class DataTransform(LayoutNode):
    objects: dict[str, list[PropertyDef]] | None = None
    projectionOrdering: dict[str, list[int]]
    projectionActiveItems: dict[str, list[ProjectionConfig]] | None = None
    splits: list[Split] | None = None
    queryMetadata: QueryMetadata | None = None
    visualElements: list[DataTransformVisualElement] | None = None
    selects: list[DataTransformSelect]
    expansionStates: list[ExpansionState] | None = None


@define(repr=True)
class VisualContainer(LayoutNode):
    """A Container for visuals in a report page.

    Generally, this is 1-1 with a real visual (bar chart, etc.), but can contain 0 (text boxes) or >1.
    It's at this level that the report connects with the SSAS model to get data for each visual.
    """

    _name_field = "name"

    x: float
    y: float
    z: float
    width: float
    height: float
    tabOrder: int | None = field(default=None, repr=repr_exists)
    dataTransforms: Json[DataTransform] | None = field(default=None, repr=repr_exists)
    query: Json[Query] | None = field(default=None, repr=repr_exists)
    queryHash: int | None = None
    filters: Json[list[VisualFilter]] = field(factory=list, repr=repr_len)
    config: Json[VisualConfig] = field(repr=False)

    _section: "Section | None" = field(init=False, repr=False, eq=False, default=None)

    id: int | None = None

    def pbi_core_id(self) -> str:
        """Returns a unique identifier for the visual container.

        Seems to stay the same after edits and after copies of the visual are made (the copies are
            assigned new, unrelated IDs). In some cases, it appears that the name is only unique within a section.

        Raises:
            ValueError: If the visual container does not have an ID or a name defined in the config.

        """
        if self.id is not None:
            return str(self.id)
        if self.config.name is not None:
            return self.config.name
        msg = "VisualContainer must have an id or a name in config"
        raise ValueError(msg)

    def pbi_core_name(self) -> str:
        viz = self.config.singleVisual
        assert viz is not None
        return viz.visualType

    def name(self) -> str | None:
        if self.config.singleVisual is not None:
            return f"{self.config.singleVisual.visualType}(x={round(self.x, 2)}, y={round(self.y, 2)}, z={round(self.z, 2)})"  # noqa: E501
        return None

    def get_visuals(self) -> list["BaseVisual"]:
        """Returns the list of Visuals contained within this VisualContainer.

        Usually, this is a list of one, but can be zero (text boxes) or more (grouped visuals).

        """
        # TODO: find an example of grouped visuals
        if self.config.singleVisual is not None:
            return [self.config.singleVisual]
        return []

    def _get_data_command(self) -> PrototypeQuery | None:
        if self.query is None:
            return None
        if len(self.query.Commands) == 0:
            return None

        if len(self.query.Commands) > 1:
            msg = "Cannot get data for multiple commands"
            raise NotImplementedError(msg)

        query_command = self.query.Commands[0]
        if isinstance(query_command, QueryCommand1):
            query = query_command.Query
        else:
            query = query_command.SemanticQueryDataShapeCommand.Query
        return query

    def get_data(self, model: "BaseTabularModel") -> PrototypeQueryResult | None:
        """Gets data that would populate this visual from the SSAS DB.

        Uses the PrototypeQuery found within query to generate a DAX statement that then gets passed to SSAS.

        Returns None for non-data visuals such as static text boxes

        """
        query = self._get_data_command()
        if query is None:
            return None
        return query.get_data(model)

    def get_performance(self, model: "BaseTabularModel") -> Performance:
        """Calculates various metrics on the speed of the visual.

        Current Metrics:
            Total Seconds to Query
            Total Rows Retrieved

        Raises:
            NoQueryError: If the visual does not have a query command.

        """
        command = self._get_data_command()
        if command is None:
            msg = "Cannot get performance for a visual without a query command"
            raise NoQueryError(msg)
        return get_performance(model, [command.get_dax(model).dax])[0]

    def get_ssas_elements(self) -> set[ModelColumnReference | ModelMeasureReference]:
        """Returns the SSAS elements (columns and measures) this visual is directly dependent on."""
        ret: set[ModelColumnReference | ModelMeasureReference] = set()
        if self.config.singleVisual is not None:
            ret.update(self.config.singleVisual.get_ssas_elements())
        if self.query is not None:
            ret.update(self.query.get_ssas_elements())
        for f in self.filters:
            ret.update(f.get_ssas_elements())
        return ret

    def get_lineage(
        self,
        lineage_type: Literal["children", "parents"],
        tabular_model: "BaseTabularModel",
    ) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(self, lineage_type)

        viz_entities = self.get_ssas_elements()
        page_filters, report_filters = set(), set()
        if (section := self._section) is not None:
            page_filters = section.get_ssas_elements(include_visuals=False)
            if (layout := section._layout) is not None:
                report_filters = layout.get_ssas_elements(include_sections=False)

        entities = viz_entities | page_filters | report_filters
        children_nodes = [ref.to_model(tabular_model) for ref in entities]

        children_lineage = [p.get_lineage(lineage_type) for p in children_nodes if p is not None]
        return LineageNode(self, lineage_type, children_lineage)
