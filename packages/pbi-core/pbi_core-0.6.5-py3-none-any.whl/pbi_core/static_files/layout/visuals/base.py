from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from pbi_core.attrs import converter, define
from pbi_core.lineage import LineageNode
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.expansion_state import ExpansionState
from pbi_core.static_files.layout.filters import Filter, PrototypeQuery
from pbi_core.static_files.layout.selector import Selector
from pbi_core.static_files.layout.sources.column import ColumnSource
from pbi_core.static_files.layout.sources.measure import MeasureSource
from pbi_core.static_files.layout.sources.paragraphs import Paragraph
from pbi_core.static_files.layout.visuals.properties import Expression, get_expression_type

from .properties.vc_properties import VCProperties

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables import Column, Measure
    from pbi_core.ssas.server import BaseTabularModel
    from pbi_core.static_files.model_references import ModelColumnReference, ModelMeasureReference


class FilterSortOrder(Enum):
    NA = 0
    NA1 = 1
    NA2 = 2
    NA3 = 3


class DisplayMode(Enum):
    hidden = "hidden"


@define()
class Display(LayoutNode):
    mode: DisplayMode


@define()
class ProjectionConfig(LayoutNode):
    queryRef: str
    active: bool = False
    suppressConcat: bool = False


@define()
class ColorRule1(LayoutNode):
    positiveColor: Expression
    negativeColor: Expression
    axisColor: Expression
    reverseDirection: Expression
    hideText: Expression | None = None


PropertyExpression = Expression | Filter | ColorRule1 | list[Paragraph]


@converter.register_structure_hook
def get_property_expression_type(v: Any, _: type | None = None) -> PropertyExpression:
    if isinstance(v, dict):
        if "positiveColor" in v:
            return ColorRule1.model_validate(v)
        if "filter" in v:
            return Filter.model_validate(v)
        return get_expression_type(v)
    if isinstance(v, list):
        return [Paragraph.model_validate(x) for x in v]
    msg = f"Unknown expression type: {v['expr']}"
    raise TypeError(msg)


@converter.register_unstructure_hook
def unparse_property_expression_type(v: PropertyExpression) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class PropertyDef(LayoutNode):
    properties: dict[str, PropertyExpression]
    selector: Selector | None = None


@converter.register_structure_hook
def get_property_def_type(v: dict[str, Any], _: type | None = None) -> PropertyDef:
    try:
        properties = {k: get_property_expression_type(e) for k, e in v.get("properties", {}).items()}
    except Exception:
        properties = v.get("properties", {})
    selector = Selector.model_validate(v["selector"]) if "selector" in v else None
    return PropertyDef(properties=properties, selector=selector)


@define()
class QueryOptions(LayoutNode):
    allowOverlappingPointsSample: bool = False
    keepProjectionOrder: bool = True


@define()
class ColumnProperty(LayoutNode):
    displayName: str | None = None
    formatString: str | None = None


@define()
class BaseVisual(LayoutNode):
    """Base class for all visual representations in the layout.

    This class defines the common properties and methods that all visuals should implement. It
    serves as a foundation for more specific visual types.

    Note:
        This class is not intended to be instantiated directly. Instead, it should be subclassed

    """

    prototypeQuery: PrototypeQuery | None = None
    projections: dict[str, list[ProjectionConfig]] | None = None
    hasDefaultSort: bool = False
    drillFilterOtherVisuals: bool = False
    filterSortOrder: FilterSortOrder = FilterSortOrder.NA
    vcObjects: VCProperties | None = None
    """vcObjects means "visual container objects"."""
    objects: Any = None
    """Objects contains the properties unique to the specific visual type.

    Subclasses should specify a real attrs model for this field"""
    visualType: str = "unknown"
    queryOptions: QueryOptions | None = None
    showAllRoles: list[str] | None = None
    display: Display | None = None
    columnProperties: dict[str, ColumnProperty] | None = None
    expansionStates: list[ExpansionState] | None = None

    @property
    def id(self) -> str:
        """Obviously terrible, but works for now lol."""
        return self.visualType

    def pbi_core_name(self) -> str:
        """Returns the name displayed in the PBIX report."""
        return self.__class__.__name__

    def get_ssas_elements(self) -> "set[ModelColumnReference | ModelMeasureReference]":
        if self.prototypeQuery is None:
            return set()
        return self.prototypeQuery.get_ssas_elements()

    def get_lineage(
        self,
        lineage_type: Literal["children", "parents"],
        tabular_model: "BaseTabularModel",
    ) -> LineageNode:
        ret: list[Column | Measure] = []
        if self.prototypeQuery is None:
            return LineageNode(self, lineage_type, [])
        table_mapping = self.prototypeQuery.table_mapping()
        children = self.prototypeQuery.get_ssas_elements()
        for child in children:
            if isinstance(child, ColumnSource):
                candidate_columns = tabular_model.columns.find_all({"explicit_name": child.Column.column()})
                for candidate_column in candidate_columns:
                    if candidate_column.table().name == table_mapping[child.Column.table()]:
                        ret.append(candidate_column)
                        break
            elif isinstance(child, MeasureSource):
                candidate_measures = tabular_model.measures.find_all({"name": child.Measure.column()})
                for candidate_measure in candidate_measures:
                    if candidate_measure.table().name == table_mapping[child.Measure.table()]:
                        ret.append(candidate_measure)
                        break
        return LineageNode(self, lineage_type, relatives=[child.get_lineage(lineage_type) for child in ret])
