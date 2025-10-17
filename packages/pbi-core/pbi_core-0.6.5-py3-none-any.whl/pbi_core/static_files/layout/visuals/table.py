from attr import define
from attrs import field

from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.selector import Selector

from .base import BaseVisual
from .properties.base import Expression


@define()
class ColumnFormattingProperties(LayoutNode):
    @define()
    class _ColumnFormattingPropertiesHelper(LayoutNode):
        @define()
        class _DataBarsProperties(LayoutNode):
            axisColor: Expression | None = None
            hideText: Expression | None = None
            negativeColor: Expression | None = None
            positiveColor: Expression | None = None
            reverseDirection: Expression | None = None

        alignment: Expression | None = None
        backColor: Expression | None = None
        dataBars: _DataBarsProperties | None = None
        fontColor: Expression | None = None
        labelDisplayUnits: Expression | None = None
        labelPrecision: Expression | None = None
        styleHeader: Expression | None = None
        styleValues: Expression | None = None

    properties: _ColumnFormattingPropertiesHelper = field(factory=_ColumnFormattingPropertiesHelper)
    selector: Selector | None = None


@define()
class ColumnHeadersProperties(LayoutNode):
    @define()
    class _ColumnHeadersPropertiesHelper(LayoutNode):
        alignment: Expression | None = None
        autoSizeColumnWidth: Expression | None = None
        backColor: Expression | None = None
        bold: Expression | None = None
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        outline: Expression | None = None
        outlineStyle: Expression | None = None
        underline: Expression | None = None
        wordWrap: Expression | None = None

    properties: _ColumnHeadersPropertiesHelper = field(factory=_ColumnHeadersPropertiesHelper)
    selector: Selector | None = None


@define()
class ColumnWidthProperties(LayoutNode):
    @define()
    class _ColumnWidthPropertiesHelper(LayoutNode):
        value: Expression | None = None

    properties: _ColumnWidthPropertiesHelper = field(factory=_ColumnWidthPropertiesHelper)
    selector: Selector | None = None


@define()
class GeneralProperties(LayoutNode):
    @define()
    class _GeneralPropertiesHelper(LayoutNode):
        pass

    properties: _GeneralPropertiesHelper = field(factory=_GeneralPropertiesHelper)


@define()
class GridProperties(LayoutNode):
    @define()
    class _GridPropertiesHelper(LayoutNode):
        gridHorizontal: Expression | None = None
        gridHorizontalColor: Expression | None = None
        gridHorizontalWeight: Expression | None = None
        gridVertical: Expression | None = None
        gridVerticalColor: Expression | None = None
        gridVerticalWeight: Expression | None = None
        imageHeight: Expression | None = None
        outlineColor: Expression | None = None
        outlineWeight: Expression | None = None
        rowPadding: Expression | None = None
        textSize: Expression | None = None

    properties: _GridPropertiesHelper = field(factory=_GridPropertiesHelper)
    selector: Selector | None = None


@define()
class TotalProperties(LayoutNode):
    @define()
    class _TotalPropertiesHelper(LayoutNode):
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        outline: Expression | None = None
        totals: Expression | None = None

    properties: _TotalPropertiesHelper = field(factory=_TotalPropertiesHelper)
    selector: Selector | None = None


@define()
class ValuesProperties(LayoutNode):
    @define()
    class _ValuesPropertiesHelper(LayoutNode):
        backColor: Expression | None = None
        backColorPrimary: Expression | None = None
        backColorSecondary: Expression | None = None
        fontColor: Expression | None = None
        fontColorPrimary: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        outline: Expression | None = None
        underline: Expression | None = None
        urlIcon: Expression | None = None
        wordWrap: Expression | None = None

    properties: _ValuesPropertiesHelper = field(factory=_ValuesPropertiesHelper)
    selector: Selector | None = None


@define()
class TableChartColumnProperties(LayoutNode):
    columnFormatting: list[ColumnFormattingProperties] = field(
        factory=lambda: [ColumnFormattingProperties()],
    )
    columnHeaders: list[ColumnHeadersProperties] = field(factory=lambda: [ColumnHeadersProperties()])
    columnWidth: list[ColumnWidthProperties] = field(factory=lambda: [ColumnWidthProperties()])
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    grid: list[GridProperties] = field(factory=lambda: [GridProperties()])
    total: list[TotalProperties] = field(factory=lambda: [TotalProperties()])
    values: list[ValuesProperties] = field(factory=lambda: [ValuesProperties()])


@define()
class TableChart(BaseVisual):
    visualType: str = "tableEx"
    objects: TableChartColumnProperties = field(factory=TableChartColumnProperties)
