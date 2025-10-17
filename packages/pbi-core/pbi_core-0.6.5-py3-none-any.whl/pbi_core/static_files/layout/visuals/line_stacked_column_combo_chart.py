from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.selector import Selector

from .base import BaseVisual
from .properties.base import Expression


@define()
class CategoryAxisProperties(LayoutNode):
    @define()
    class _CategoryAxisPropertiesHelper(LayoutNode):
        axisType: Expression | None = None

    properties: _CategoryAxisPropertiesHelper = field(factory=_CategoryAxisPropertiesHelper)


@define()
class DataPointProperties(LayoutNode):
    @define()
    class _DataPointPropertiesHelper(LayoutNode):
        fill: Expression | None = None
        fillRule: Expression | None = None
        showAllDataPoints: Expression | None = None

    properties: _DataPointPropertiesHelper = field(factory=_DataPointPropertiesHelper)
    selector: Selector | None = None


@define()
class LabelsProperties(LayoutNode):
    @define()
    class _LabelsPropertiesHelper(LayoutNode):
        backgroundColor: Expression | None = None
        backgroundTransparency: Expression | None = None
        color: Expression | None = None
        enableBackground: Expression | None = None
        fontSize: Expression | None = None
        labelDisplayUnits: Expression | None = None
        labelOrientation: Expression | None = None
        labelPosition: Expression | None = None
        show: Expression | None = None
        showAll: Expression | None = None

    properties: _LabelsPropertiesHelper = field(factory=_LabelsPropertiesHelper)
    selector: Selector | None = None


@define()
class LegendProperties(LayoutNode):
    @define()
    class _LegendPropertiesHelper(LayoutNode):
        legendMarkerRendering: Expression | None = None
        position: Expression | None = None
        show: Expression | None = None

    properties: _LegendPropertiesHelper = field(factory=_LegendPropertiesHelper)
    selector: Selector | None = None


@define()
class LineStylesProperties(LayoutNode):
    @define()
    class _LineStylesPropertiesHelper(LayoutNode):
        lineStyle: Expression | None = None
        markerShape: Expression | None = None
        shadeArea: Expression | None = None
        showMarker: Expression | None = None
        showSeries: Expression | None = None
        stepped: Expression | None = None
        strokeWidth: Expression | None = None

    properties: _LineStylesPropertiesHelper = field(factory=_LineStylesPropertiesHelper)
    selector: Selector | None = None


@define()
class SmallMultiplesLayoutProperties(LayoutNode):
    @define()
    class _SmallMultiplesLayoutPropertiesHelper(LayoutNode):
        gridLineColor: Expression | None = None
        gridLineStyle: Expression | None = None
        gridLineType: Expression | None = None
        gridPadding: Expression | None = None
        rowCount: Expression | None = None

    properties: _SmallMultiplesLayoutPropertiesHelper = field(factory=_SmallMultiplesLayoutPropertiesHelper)


@define()
class SubheaderProperties(LayoutNode):
    @define()
    class _SubheaderPropertiesHelper(LayoutNode):
        fontSize: Expression | None = None

    properties: _SubheaderPropertiesHelper = field(factory=_SubheaderPropertiesHelper)


@define()
class ValueAxisProperties(LayoutNode):
    @define()
    class _ValueAxisPropertiesHelper(LayoutNode):
        alignZeros: Expression | None = None
        end: Expression | None = None
        gridlineShow: Expression | None = None
        secEnd: Expression | None = None
        secShow: Expression | None = None
        secStart: Expression | None = None
        start: Expression | None = None
        show: Expression | None = None

    properties: _ValueAxisPropertiesHelper = field(factory=_ValueAxisPropertiesHelper)
    selector: Selector | None = None


@define()
class LineStackedColumnComboChartProperties(LayoutNode):
    categoryAxis: list[CategoryAxisProperties] = field(factory=lambda: [CategoryAxisProperties()])
    dataPoint: list[DataPointProperties] = field(factory=lambda: [DataPointProperties()])
    labels: list[LabelsProperties] = field(factory=lambda: [LabelsProperties()])
    legend: list[LegendProperties] = field(factory=lambda: [LegendProperties()])
    lineStyles: list[LineStylesProperties] = field(factory=lambda: [LineStylesProperties()])
    smallMultiplesLayout: list[SmallMultiplesLayoutProperties] = field(
        factory=lambda: [SmallMultiplesLayoutProperties()],
    )
    subheader: list[SubheaderProperties] = field(factory=lambda: [SubheaderProperties()])
    valueAxis: list[ValueAxisProperties] = field(factory=lambda: [ValueAxisProperties()])


@define()
class LineStackedColumnComboChart(BaseVisual):
    visualType: str = "lineStackedColumnComboChart"

    drillFilterOtherVisuals: bool = True
    objects: LineStackedColumnComboChartProperties = field(
        factory=LineStackedColumnComboChartProperties,
        repr=False,
    )
