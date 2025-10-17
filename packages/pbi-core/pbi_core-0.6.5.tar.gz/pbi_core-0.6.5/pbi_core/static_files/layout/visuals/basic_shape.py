from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode

from .base import BaseVisual
from .properties.base import Expression


@define()
class FillProperties(LayoutNode):
    @define()
    class _FillPropertiesHelper(LayoutNode):
        fillColor: Expression | None = None
        show: Expression | None = None
        transparency: Expression | None = None

    properties: _FillPropertiesHelper = field(factory=_FillPropertiesHelper)


@define()
class GeneralProperties(LayoutNode):
    @define()
    class _GeneralPropertiesHelper(LayoutNode):
        shapeType: Expression | None = None

    properties: _GeneralPropertiesHelper = field(factory=_GeneralPropertiesHelper)


@define()
class LineProperties(LayoutNode):
    @define()
    class _LinePropertiesHelper(LayoutNode):
        lineColor: Expression | None = None
        roundEdge: Expression | None = None
        transparency: Expression | None = None
        weight: Expression | None = None

    properties: _LinePropertiesHelper = field(factory=_LinePropertiesHelper)


@define()
class RotationProperties(LayoutNode):
    @define()
    class _RotationPropertiesHelper(LayoutNode):
        angle: Expression | None = None

    properties: _RotationPropertiesHelper = field(factory=_RotationPropertiesHelper)


@define()
class BasicShapeProperties(LayoutNode):
    fill: list[FillProperties] = field(factory=lambda: [FillProperties()])
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    line: list[LineProperties] = field(factory=lambda: [LineProperties()])
    rotation: list[RotationProperties] = field(factory=lambda: [RotationProperties()])


@define()
class BasicShape(BaseVisual):
    visualType: str = "basicShape"

    drillFilterOtherVisuals: bool = True
    objects: BasicShapeProperties = field(factory=BasicShapeProperties, repr=False)
