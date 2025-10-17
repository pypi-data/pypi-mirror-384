from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.selector import Selector

from .base import BaseVisual
from .properties.base import Expression


@define()
class FillProperties(LayoutNode):
    @define()
    class _FillPropertiesHelper(LayoutNode):
        fillColor: Expression | None = None
        image: Expression | None = None
        show: Expression | None = None
        transparency: Expression | None = None

    properties: _FillPropertiesHelper = field(factory=_FillPropertiesHelper)
    selector: Selector | None = None


@define()
class IconProperties(LayoutNode):
    @define()
    class _IconPropertiesHelper(LayoutNode):
        bottomMargin: Expression | None = None
        horizontalAlignment: Expression | None = None
        leftMargin: Expression | None = None
        lineColor: Expression | None = None
        lineTransparency: Expression | None = None
        lineWeight: Expression | None = None
        padding: Expression | None = None
        rightMargin: Expression | None = None
        shapeType: Expression | None = None
        show: Expression | None = None
        topMargin: Expression | None = None
        verticalAlignment: Expression | None = None

    properties: _IconPropertiesHelper = field(factory=_IconPropertiesHelper)
    selector: Selector | None = None


@define()
class OutlineProperties(LayoutNode):
    @define()
    class _OutlinePropertiesHelper(LayoutNode):
        lineColor: Expression | None = None
        roundEdge: Expression | None = None
        show: Expression | None = None
        transparency: Expression | None = None
        weight: Expression | None = None

    properties: _OutlinePropertiesHelper = field(factory=_OutlinePropertiesHelper)
    selector: Selector | None = None


@define()
class ShapeProperties(LayoutNode):
    @define()
    class _ShapePropertiesHelper(LayoutNode):
        roundEdge: Expression | None = None

    properties: _ShapePropertiesHelper = field(factory=_ShapePropertiesHelper)
    selector: Selector | None = None


@define()
class TextProperties(LayoutNode):
    @define()
    class _TextPropertiesHelper(LayoutNode):
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        horizontalAlignment: Expression | None = None
        leftMargin: Expression | None = None
        padding: Expression | None = None
        rightMargin: Expression | None = None
        show: Expression | None = None
        text: Expression | None = None
        topMargin: Expression | None = None
        verticalAlignment: Expression | None = None

    properties: _TextPropertiesHelper = field(factory=_TextPropertiesHelper)
    selector: Selector | None = None


@define()
class ActionButtonProperties(LayoutNode):
    fill: list[FillProperties] = field(factory=lambda: [FillProperties()])
    icon: list[IconProperties] = field(factory=lambda: [IconProperties()])
    outline: list[OutlineProperties] = field(factory=lambda: [OutlineProperties()])
    shape: list[ShapeProperties] = field(factory=lambda: [ShapeProperties()])
    text: list[TextProperties] = field(factory=lambda: [TextProperties()])


@define()
class ActionButton(BaseVisual):
    visualType: str = "actionButton"

    drillFilterOtherVisuals: bool = True
    objects: ActionButtonProperties = field(factory=ActionButtonProperties, repr=False)
