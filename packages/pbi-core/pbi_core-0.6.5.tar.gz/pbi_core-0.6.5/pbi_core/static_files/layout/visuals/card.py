from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.selector import Selector

from .base import BaseVisual
from .properties.base import Expression


@define()
class CategoryLabelsProperties(LayoutNode):
    @define()
    class _CategoryLabelsPropertiesHelper(LayoutNode):
        color: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        show: Expression | None = None

    properties: _CategoryLabelsPropertiesHelper = field(factory=_CategoryLabelsPropertiesHelper)
    selector: Selector | None = None


@define()
class GeneralProperties(LayoutNode):
    @define()
    class _GeneralPropertiesHelper(LayoutNode):
        pass

    properties: _GeneralPropertiesHelper = field(factory=_GeneralPropertiesHelper)


@define()
class LabelsProperties(LayoutNode):
    @define()
    class _LabelsPropertiesHelper(LayoutNode):
        color: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        labelPrecision: Expression | None = None
        labelDisplayUnits: Expression | None = None
        preserveWhitespace: Expression | None = None

    properties: _LabelsPropertiesHelper = field(factory=_LabelsPropertiesHelper)
    selector: Selector | None = None


@define()
class WordWrapProperties(LayoutNode):
    @define()
    class _WordWrapperPropertiesHelper(LayoutNode):
        show: Expression | None = None

    properties: _WordWrapperPropertiesHelper = field(factory=_WordWrapperPropertiesHelper)


@define()
class CardProperties(LayoutNode):
    categoryLabels: list[CategoryLabelsProperties] = field(factory=lambda: [CategoryLabelsProperties()])
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    labels: list[LabelsProperties] = field(factory=lambda: [LabelsProperties()])
    wordWrap: list[WordWrapProperties] = field(factory=lambda: [WordWrapProperties()])


@define()
class Card(BaseVisual):
    visualType: str = "card"

    drillFilterOtherVisuals: bool = True
    objects: CardProperties = field(factory=CardProperties, repr=False)
