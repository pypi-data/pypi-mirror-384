from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.selector import Selector

from .base import BaseVisual
from .properties.base import Expression


@define()
class AnomalyDetectionProperties(LayoutNode):
    @define()
    class _AnomalyDetectionPropertiesHelper(LayoutNode):
        confidenceBandColor: Expression | None = None
        displayName: Expression | None = None
        explainBy: Expression | None = None
        markerColor: Expression | None = None
        markerShape: Expression | None = None
        show: Expression | None = None
        transform: Expression | None = None
        transparency: Expression | None = None

    properties: _AnomalyDetectionPropertiesHelper = field(factory=_AnomalyDetectionPropertiesHelper)
    selector: Selector | None = None


@define()
class CategoryAxisProperties(LayoutNode):
    @define()
    class _CategoryAxisPropertiesHelper(LayoutNode):
        axisType: Expression | None = None
        concatenateLabels: Expression | None = None
        end: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        gridlineShow: Expression | None = None
        labelColor: Expression | None = None
        maxMarginFactor: Expression | None = None
        show: Expression | None = None
        showAxisTitle: Expression | None = None
        start: Expression | None = None
        titleColor: Expression | None = None
        titleFontFamily: Expression | None = None
        titleFontSize: Expression | None = None

    properties: _CategoryAxisPropertiesHelper = field(factory=_CategoryAxisPropertiesHelper)
    selector: Selector | None = None


@define()
class DataPointProperties(LayoutNode):
    @define()
    class _DataPointPropertiesHelper(LayoutNode):
        fill: Expression | None = None
        showAllDataPoints: Expression | None = None

    properties: _DataPointPropertiesHelper = field(factory=_DataPointPropertiesHelper)
    selector: Selector | None = None


@define()
class ForecastProperties(LayoutNode):
    @define()
    class _ForecastPropertiesHelper(LayoutNode):
        show: Expression | None = None
        displayName: Expression | None = None
        lineColor: Expression | None = None
        transform: Expression | None = None

    properties: _ForecastPropertiesHelper = field(factory=_ForecastPropertiesHelper)
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
        color: Expression | None = None
        labelPosition: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        labelDensity: Expression | None = None
        show: Expression | None = None
        showAll: Expression | None = None
        showSeries: Expression | None = None

    properties: _LabelsPropertiesHelper = field(factory=_LabelsPropertiesHelper)
    selector: Selector | None = None


@define()
class LegendProperties(LayoutNode):
    @define()
    class _LegendPropertiesHelper(LayoutNode):
        defaultToCircle: Expression | None = None
        fontSize: Expression | None = None
        labelColor: Expression | None = None
        legendMarkerRendering: Expression | None = None
        position: Expression | None = None
        show: Expression | None = None
        showTitle: Expression | None = None
        titleText: Expression | None = None

    properties: _LegendPropertiesHelper = field(factory=_LegendPropertiesHelper)


@define()
class LineStylesProperties(LayoutNode):
    @define()
    class _LineStylesPropertiesHelper(LayoutNode):
        lineStyle: Expression | None = None
        markerColor: Expression | None = None
        markerShape: Expression | None = None
        markerSize: Expression | None = None
        showMarker: Expression | None = None
        showSeries: Expression | None = None
        stepped: Expression | None = None
        strokeLineJoin: Expression | None = None
        strokeWidth: Expression | None = None

    properties: _LineStylesPropertiesHelper = field(factory=_LineStylesPropertiesHelper)
    selector: Selector | None = None


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
        end: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        gridlineColor: Expression | None = None
        gridlineShow: Expression | None = None
        gridlineStyle: Expression | None = None
        gridlineThickness: Expression | None = None
        labelColor: Expression | None = None
        labelDensity: Expression | None = None
        labelDisplayUnits: Expression | None = None
        position: Expression | None = None
        show: Expression | None = None
        showAxisTitle: Expression | None = None
        start: Expression | None = None
        titleFontFamily: Expression | None = None
        titleText: Expression | None = None

    properties: _ValueAxisPropertiesHelper = field(factory=_ValueAxisPropertiesHelper)


@define()
class Y1AxisReferenceLineProperties(LayoutNode):
    @define()
    class _Y1AxisReferenceLinePropertiesHelper(LayoutNode):
        displayName: Expression | None = None
        position: Expression | None = None
        show: Expression | None = None
        style: Expression | None = None

    properties: _Y1AxisReferenceLinePropertiesHelper = field(factory=_Y1AxisReferenceLinePropertiesHelper)
    selector: Selector | None = None


@define()
class Y2AxisProperties(LayoutNode):
    @define()
    class _Y2AxisPropertiesHelper(LayoutNode):
        show: Expression | None = None

    properties: _Y2AxisPropertiesHelper = field(factory=_Y2AxisPropertiesHelper)


@define()
class ZoomProperties(LayoutNode):
    @define()
    class _ZoomPropertiesHelper(LayoutNode):
        show: Expression | None = None
        categoryMax: Expression | None = None
        categoryMin: Expression | None = None
        valueMax: Expression | None = None
        valueMin: Expression | None = None

    properties: _ZoomPropertiesHelper = field(factory=_ZoomPropertiesHelper)


@define()
class LineChartProperties(LayoutNode):
    anomalyDetection: list[AnomalyDetectionProperties] = field(
        factory=lambda: [AnomalyDetectionProperties()],
    )
    categoryAxis: list[CategoryAxisProperties] = field(factory=lambda: [CategoryAxisProperties()])
    dataPoint: list[DataPointProperties] = field(factory=lambda: [DataPointProperties()])
    forecast: list[ForecastProperties] = field(factory=lambda: [ForecastProperties()])
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    labels: list[LabelsProperties] = field(factory=lambda: [LabelsProperties()])
    legend: list[LegendProperties] = field(factory=lambda: [LegendProperties()])
    lineStyles: list[LineStylesProperties] = field(factory=lambda: [LineStylesProperties()])
    plotArea: list[PlotAreaProperties] = field(factory=lambda: [PlotAreaProperties()])
    trend: list[TrendProperties] = field(factory=lambda: [TrendProperties()])
    valueAxis: list[ValueAxisProperties] = field(factory=lambda: [ValueAxisProperties()])
    zoom: list[ZoomProperties] = field(factory=lambda: [ZoomProperties()])
    y1AxisReferenceLine: list[Y1AxisReferenceLineProperties] = field(
        factory=lambda: [Y1AxisReferenceLineProperties()],
    )
    y2Axis: list[Y2AxisProperties] = field(factory=lambda: [Y2AxisProperties()])


@define()
class LineChart(BaseVisual):
    visualType: str = "lineChart"

    drillFilterOtherVisuals: bool = True
    objects: LineChartProperties = field(factory=LineChartProperties, repr=False)
