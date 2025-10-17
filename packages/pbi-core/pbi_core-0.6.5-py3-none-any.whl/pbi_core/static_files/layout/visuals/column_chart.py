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
        fontSize: Expression | None = None
        gridlineColor: Expression | None = None
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
        titleText: Expression | None = None

    properties: _CategoryAxisPropertiesHelper = field(factory=_CategoryAxisPropertiesHelper)
    selector: Selector | None = None


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
class GeneralProperties(LayoutNode):
    @define()
    class _GeneralPropertiesHelper(LayoutNode):
        responsive: Expression | None = None

    properties: _GeneralPropertiesHelper = field(factory=_GeneralPropertiesHelper)


@define()
class LabelsProperties(LayoutNode):
    @define()
    class _LabelsPropertiesHelper(LayoutNode):
        backgroundColor: Expression | None = None
        backgroundTransparency: Expression | None = None
        color: Expression | None = None
        enableBackground: Expression | None = None
        fontSize: Expression | None = None
        labelDensity: Expression | None = None
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
        fontSize: Expression | None = None
        labelColor: Expression | None = None
        position: Expression | None = None
        show: Expression | None = None
        showTitle: Expression | None = None

    properties: _LegendPropertiesHelper = field(factory=_LegendPropertiesHelper)
    selector: Selector | None = None


@define()
class TotalProperties(LayoutNode):
    @define()
    class _TotalPropertiesHelper(LayoutNode):
        show: Expression | None = None

    properties: _TotalPropertiesHelper = field(factory=_TotalPropertiesHelper)


@define()
class ValueAxisProperties(LayoutNode):
    @define()
    class _ValueAxisPropertiesHelper(LayoutNode):
        axisScale: Expression | None = None
        fontSize: Expression | None = None
        gridlineShow: Expression | None = None
        logAxisScale: Expression | None = None
        show: Expression | None = None
        showAxisTitle: Expression | None = None
        start: Expression | None = None
        titleFontFamily: Expression | None = None

    properties: _ValueAxisPropertiesHelper = field(factory=_ValueAxisPropertiesHelper)
    selector: Selector | None = None


@define()
class Y1AxisReferenceLineProperties(LayoutNode):
    @define()
    class _Y1AxisReferenceLinePropertiesHelper(LayoutNode):
        displayName: Expression | None = None
        lineColor: Expression | None = None
        show: Expression | None = None
        style: Expression | None = None
        transparency: Expression | None = None
        value: Expression | None = None

    properties: _Y1AxisReferenceLinePropertiesHelper = field(factory=_Y1AxisReferenceLinePropertiesHelper)
    selector: Selector | None = None


@define()
class ZoomProperties(LayoutNode):
    @define()
    class _ZoomPropertiesHelper(LayoutNode):
        show: Expression | None = None

    properties: _ZoomPropertiesHelper = field(factory=_ZoomPropertiesHelper)


@define()
class ColumnChartColumnProperties(LayoutNode):
    categoryAxis: list[CategoryAxisProperties] = field(factory=lambda: [CategoryAxisProperties()])
    dataPoint: list[DataPointProperties] = field(factory=lambda: [DataPointProperties()])
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    labels: list[LabelsProperties] = field(factory=lambda: [LabelsProperties()])
    legend: list[LegendProperties] = field(factory=lambda: [LegendProperties()])
    valueAxis: list[ValueAxisProperties] = field(factory=lambda: [ValueAxisProperties()])
    totals: list[TotalProperties] = field(factory=lambda: [TotalProperties()])
    y1AxisReferenceLine: list[Y1AxisReferenceLineProperties] = field(
        factory=lambda: [Y1AxisReferenceLineProperties()],
    )
    zoom: list[ZoomProperties] = field(factory=lambda: [ZoomProperties()])


@define()
class ColumnChart(BaseVisual):
    visualType: str = "columnChart"

    objects: ColumnChartColumnProperties = field(factory=ColumnChartColumnProperties, repr=False)
    selector: Selector | None = None
    columnCount: Expression | None = None
