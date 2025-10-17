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
        axisStyle: Expression | None = None
        axisType: Expression | None = None
        concatenateLabels: Expression | None = None
        end: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        gridlineShow: Expression | None = None
        innerPadding: Expression | None = None
        invertAxis: Expression | None = None
        italic: Expression | None = None
        labelColor: Expression | None = None
        labelDisplayUnits: Expression | None = None
        labelPrecision: Expression | None = None
        logAxisScale: Expression | None = None
        maxMarginFactor: Expression | None = None
        position: Expression | None = None
        preferredCategoryWidth: Expression | None = None
        show: Expression | None = None
        showAxisTitle: Expression | None = None
        start: Expression | None = None
        switchAxisPosition: Expression | None = None
        titleColor: Expression | None = None
        titleFontFamily: Expression | None = None
        titleFontSize: Expression | None = None
        titleItalic: Expression | None = None
        titleText: Expression | None = None

    properties: _CategoryAxisPropertiesHelper = field(factory=_CategoryAxisPropertiesHelper)


@define()
class DataPointProperties(LayoutNode):
    @define()
    class _DataPointPropertiesHelper(LayoutNode):
        borderColorMatchFill: Expression | None = None
        borderShow: Expression | None = None
        borderSize: Expression | None = None
        borderTransparency: Expression | None = None
        fill: Expression | None = None
        fillRule: Expression | None = None
        fillTransparency: Expression | None = None
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
        detailFontFamily: Expression | None = None
        detailItalic: Expression | None = None
        enableBackground: Expression | None = None
        enableDetailDataLabel: Expression | None = None
        enableTitleDataLabel: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        italic: Expression | None = None
        labelContainerMaxWidth: Expression | None = None
        labelContentLayout: Expression | None = None
        labelDensity: Expression | None = None
        labelDisplayUnits: Expression | None = None
        labelOverflow: Expression | None = None
        labelPosition: Expression | None = None
        labelPrecision: Expression | None = None
        optimizeLabelDisplay: Expression | None = None
        show: Expression | None = None
        showAll: Expression | None = None
        showBlankAs: Expression | None = None
        titleColor: Expression | None = None
        titleFontFamily: Expression | None = None
        titleFontSize: Expression | None = None
        titleItalic: Expression | None = None
        titleShowBlankAs: Expression | None = None
        titleTransparency: Expression | None = None
        titleUnderline: Expression | None = None
        transparency: Expression | None = None

    properties: _LabelsPropertiesHelper = field(factory=_LabelsPropertiesHelper)
    selector: Selector | None = None


@define()
class LayoutProperties(LayoutNode):
    @define()
    class _LayoutPropertiesHelper(LayoutNode):
        ribbonGapSize: Expression | None = None

    properties: _LayoutPropertiesHelper = field(factory=_LayoutPropertiesHelper)


@define()
class LegendProperties(LayoutNode):
    @define()
    class _LegendPropertiesHelper(LayoutNode):
        fontSize: Expression | None = None
        labelColor: Expression | None = None
        position: Expression | None = None
        show: Expression | None = None
        showTitle: Expression | None = None
        titleText: Expression | None = None

    properties: _LegendPropertiesHelper = field(factory=_LegendPropertiesHelper)


@define()
class RibbonBandsProperties(LayoutNode):
    @define()
    class _RibbonBandsPropertiesHelper(LayoutNode):
        borderColorMatchFill: Expression | None = None
        borderShow: Expression | None = None
        borderTransparency: Expression | None = None
        color: Expression | None = None
        fillTransparency: Expression | None = None
        show: Expression | None = None
        transparency: Expression | None = None

    properties: _RibbonBandsPropertiesHelper = field(factory=_RibbonBandsPropertiesHelper)


@define()
class ValueAxisProperties(LayoutNode):
    @define()
    class _ValueAxisPropertiesHelper(LayoutNode):
        axisScale: Expression | None = None
        bold: Expression | None = None
        end: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        gridlineColor: Expression | None = None
        gridlineShow: Expression | None = None
        invertAxis: Expression | None = None
        labelColor: Expression | None = None
        labelDisplayUnits: Expression | None = None
        labelPrecision: Expression | None = None
        logAxisScale: Expression | None = None
        show: Expression | None = None
        showAxisTitle: Expression | None = None
        start: Expression | None = None
        titleFontFamily: Expression | None = None
        titleColor: Expression | None = None
        titleFontColor: Expression | None = None
        titleFontSize: Expression | None = None
        titleText: Expression | None = None

    properties: _ValueAxisPropertiesHelper = field(factory=_ValueAxisPropertiesHelper)


@define()
class XAxisReferenceLineProperties(LayoutNode):
    @define()
    class _XAxisReferenceLinePropertiesHelper(LayoutNode):
        displayName: Expression | None = None
        show: Expression | None = None
        value: Expression | None = None

    properties: _XAxisReferenceLinePropertiesHelper = field(factory=_XAxisReferenceLinePropertiesHelper)
    selector: Selector | None = None


@define()
class ZoomProperties(LayoutNode):
    @define()
    class _ZoomPropertiesHelper(LayoutNode):
        show: Expression | None = None
        showLabels: Expression | None = None
        showTooltip: Expression | None = None

    properties: _ZoomPropertiesHelper = field(factory=_ZoomPropertiesHelper)


@define()
class BarChartProperties(LayoutNode):
    categoryAxis: list[CategoryAxisProperties] = field(factory=lambda: [CategoryAxisProperties()])
    dataPoint: list[DataPointProperties] = field(factory=lambda: [DataPointProperties()])
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    labels: list[LabelsProperties] = field(factory=lambda: [LabelsProperties()])
    layout: list[LayoutProperties] = field(factory=lambda: [LayoutProperties()])
    legend: list[LegendProperties] = field(factory=lambda: [LegendProperties()])
    ribbonBands: list[RibbonBandsProperties] = field(factory=lambda: [RibbonBandsProperties()])
    valueAxis: list[ValueAxisProperties] = field(factory=lambda: [ValueAxisProperties()])
    xAxisReferenceLine: list[XAxisReferenceLineProperties] = field(
        factory=lambda: [XAxisReferenceLineProperties()],
    )
    zoom: list[ZoomProperties] = field(factory=lambda: [ZoomProperties()])


@define()
class BarChart(BaseVisual):
    visualType: str = "barChart"
    objects: BarChartProperties = field(factory=BarChartProperties, repr=False)
