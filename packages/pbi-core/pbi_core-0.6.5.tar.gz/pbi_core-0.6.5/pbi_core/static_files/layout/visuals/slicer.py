from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.filters import Filter
from pbi_core.static_files.layout.selector import SelectorData

from .base import BaseVisual
from .properties.base import Expression


@define()
class SyncGroup(LayoutNode):
    groupName: str
    fieldChanges: bool
    filterChanges: bool = True


@define()
class CachedFilterDisplayItems(LayoutNode):
    id: SelectorData
    displayName: str


@define()
class DataProperties(LayoutNode):
    @define()
    class _DataPropertiesHelper(LayoutNode):
        endDate: Expression | None = None
        isInvertedSelectionMode: Expression | None = None
        mode: Expression | None = None
        numericEnd: Expression | None = None
        numericStart: Expression | None = None
        startDate: Expression | None = None

    properties: _DataPropertiesHelper = field(factory=_DataPropertiesHelper)


@define()
class DateProperties(LayoutNode):
    @define()
    class _DatePropertiesHelper(LayoutNode):
        background: Expression | None = None
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        textSize: Expression | None = None

    properties: _DatePropertiesHelper = field(factory=_DatePropertiesHelper)


@define()
class GeneralProperties(LayoutNode):
    @define()
    class _GeneralPropertiesHelper(LayoutNode):
        filter: Filter | None = None
        responsive: Expression | None = None
        selfFilterEnabled: Expression | None = None
        selfFilter: Filter | None = None
        orientation: Expression | None = None
        outlineColor: Expression | None = None
        outlineWeight: Expression | None = None

    properties: _GeneralPropertiesHelper = field(factory=_GeneralPropertiesHelper)


@define()
class HeaderProperties(LayoutNode):
    @define()
    class _HeaderPropertiesHelper(LayoutNode):
        background: Expression | None = None
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        outlineStyle: Expression | None = None
        show: Expression | None = None
        showRestatement: Expression | None = None
        text: Expression | None = None
        textSize: Expression | None = None
        underline: Expression | None = None

    properties: _HeaderPropertiesHelper = field(factory=_HeaderPropertiesHelper)


@define()
class NumericInputStyleProperties(LayoutNode):
    @define()
    class _NumericInputStylePropertiesHelper(LayoutNode):
        background: Expression | None = None
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        textSize: Expression | None = None

    properties: _NumericInputStylePropertiesHelper = field(factory=_NumericInputStylePropertiesHelper)


@define()
class ItemProperties(LayoutNode):
    @define()
    class _ItemPropertiesHelper(LayoutNode):
        background: Expression | None = None
        bold: Expression | None = None
        expandCollapseToggleType: Expression | None = None
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        outline: Expression | None = None
        outlineColor: Expression | None = None
        outlineStyle: Expression | None = None
        padding: Expression | None = None
        steppedLayoutIndentation: Expression | None = None
        textSize: Expression | None = None

    properties: _ItemPropertiesHelper = field(factory=_ItemPropertiesHelper)


@define()
class PendingChangeIconProperties(LayoutNode):
    @define()
    class _PendingChangeIconPropertiesHelper(LayoutNode):
        color: Expression | None = None
        size: Expression | None = None
        tooltipLabel: Expression | None = None
        tooltipText: Expression | None = None
        transparency: Expression | None = None

    properties: _PendingChangeIconPropertiesHelper = field(factory=_PendingChangeIconPropertiesHelper)


@define()
class SelectionProperties(LayoutNode):
    @define()
    class _SelectionPropertiesHelper(LayoutNode):
        selectAllCheckboxEnabled: Expression | None = None
        singleSelect: Expression | None = None
        strictSingleSelect: Expression | None = None

    properties: _SelectionPropertiesHelper = field(factory=_SelectionPropertiesHelper)


@define()
class SliderProperties(LayoutNode):
    @define()
    class _SliderPropertiesHelper(LayoutNode):
        color: Expression | None = None
        show: Expression | None = None

    properties: _SliderPropertiesHelper = field(factory=_SliderPropertiesHelper)


@define()
class SlicerProperties(LayoutNode):
    date: list[DateProperties] = field(factory=lambda: [DateProperties()])
    data: list[DataProperties] = field(factory=lambda: [DataProperties()])
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    header: list[HeaderProperties] = field(factory=lambda: [HeaderProperties()])
    items: list[ItemProperties] = field(factory=lambda: [ItemProperties()])
    numericInputStyle: list[NumericInputStyleProperties] = field(
        factory=lambda: [NumericInputStyleProperties()],
    )
    pendingChangesIcon: list[PendingChangeIconProperties] = field(
        factory=lambda: [PendingChangeIconProperties()],
    )
    selection: list[SelectionProperties] = field(factory=lambda: [SelectionProperties()])
    slider: list[SliderProperties] = field(factory=lambda: [SliderProperties()])


@define()
class Slicer(BaseVisual):
    visualType: str = "slicer"
    syncGroup: SyncGroup | None = None
    cachedFilterDisplayItems: list[CachedFilterDisplayItems] | None = None
    objects: SlicerProperties = field(factory=SlicerProperties)
