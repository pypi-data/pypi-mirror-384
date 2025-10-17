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
        concatenateLabels: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        gridlineShow: Expression | None = None
        gridlineStyle: Expression | None = None
        innerPadding: Expression | None = None
        labelColor: Expression | None = None
        maxMarginFactor: Expression | None = None
        preferredCategoryWidth: Expression | None = None
        show: Expression | None = None
        showAxisTitle: Expression | None = None
        titleColor: Expression | None = None
        titleFontSize: Expression | None = None

    properties: _CategoryAxisPropertiesHelper = field(factory=_CategoryAxisPropertiesHelper)


@define()
class DataPointProperties(LayoutNode):
    @define()
    class _DataPointPropertiesHelper(LayoutNode):
        fill: Expression | None = None
        showAllDataPoints: Expression | None = None

    properties: _DataPointPropertiesHelper = field(factory=_DataPointPropertiesHelper)
    selector: Selector | None = None


@define()
class GeneralProperties(LayoutNode):
    @define()
    class _GeneralPropertiesHelper(LayoutNode):
        responsive: Expression | None = None

    properties: _GeneralPropertiesHelper = field(factory=_GeneralPropertiesHelper)


@define()
class LabelsProperties(LayoutNode):
    @define()
    class _LabelsPropertiesHelper(LayoutNode):
        backgroundTransparency: Expression | None = None
        color: Expression | None = None
        enableBackground: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        labelDisplayUnits: Expression | None = None
        labelOrientation: Expression | None = None
        labelOverflow: Expression | None = None
        labelPosition: Expression | None = None
        labelPrecision: Expression | None = None
        show: Expression | None = None
        showAll: Expression | None = None

    properties: _LabelsPropertiesHelper = field(factory=_LabelsPropertiesHelper)
    selector: Selector | None = None


@define()
class LegendProperties(LayoutNode):
    @define()
    class _LegendPropertiesHelper(LayoutNode):
        fontSize: Expression | None = None
        labelColor: Expression | None = None
        position: Expression | None = None
        show: Expression | None = None
        showTitle: Expression | None = None

    properties: _LegendPropertiesHelper = field(factory=_LegendPropertiesHelper)


@define()
class PlotAreaProperties(LayoutNode):
    @define()
    class _PlotAreaPropertiesHelper(LayoutNode):
        transparency: Expression | None = None

    properties: _PlotAreaPropertiesHelper = field(factory=_PlotAreaPropertiesHelper)


@define()
class TrendProperties(LayoutNode):
    @define()
    class _TrendPropertiesHelper(LayoutNode):
        displayName: Expression | None = None
        lineColor: Expression | None = None
        show: Expression | None = None

    properties: _TrendPropertiesHelper = field(factory=_TrendPropertiesHelper)


@define()
class ValueAxisProperties(LayoutNode):
    @define()
    class _ValueAxisPropertiesHelper(LayoutNode):
        axisScale: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        gridlineShow: Expression | None = None
        labelColor: Expression | None = None
        labelDisplayUnits: Expression | None = None
        logAxisScale: Expression | None = None
        show: Expression | None = None
        showAxisTitle: Expression | None = None
        start: Expression | None = None
        titleFontFamily: Expression | None = None

    properties: _ValueAxisPropertiesHelper = field(factory=_ValueAxisPropertiesHelper)
    selector: Selector | None = None


@define()
class ClusteredColumnChartProperties(LayoutNode):
    categoryAxis: list[CategoryAxisProperties] = field(factory=lambda: [CategoryAxisProperties()])
    dataPoint: list[DataPointProperties] = field(factory=lambda: [DataPointProperties()])
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    labels: list[LabelsProperties] = field(factory=lambda: [LabelsProperties()])
    legend: list[LegendProperties] = field(factory=lambda: [LegendProperties()])
    plotArea: list[PlotAreaProperties] = field(factory=lambda: [PlotAreaProperties()])
    trend: list[TrendProperties] = field(factory=lambda: [TrendProperties()])
    valueAxis: list[ValueAxisProperties] = field(factory=lambda: [ValueAxisProperties()])


@define()
class ClusteredColumnChart(BaseVisual):
    visualType: str = "clusteredColumnChart"

    drillFilterOtherVisuals: bool = True
    objects: ClusteredColumnChartProperties = field(factory=ClusteredColumnChartProperties, repr=False)
