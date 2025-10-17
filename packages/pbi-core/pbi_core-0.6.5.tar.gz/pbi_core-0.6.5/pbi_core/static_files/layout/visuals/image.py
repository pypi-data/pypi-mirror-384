from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode

from .base import BaseVisual
from .properties.base import Expression


@define()
class GeneralProperties(LayoutNode):
    @define()
    class _GeneralPropertiesHelper(LayoutNode):
        imageUrl: Expression | None = None

    properties: _GeneralPropertiesHelper = field(factory=_GeneralPropertiesHelper)


@define()
class ImageScalingProperties(LayoutNode):
    @define()
    class _ImageScalingPropertiesHelper(LayoutNode):
        imageScalingType: Expression | None = None

    properties: _ImageScalingPropertiesHelper = field(factory=_ImageScalingPropertiesHelper)


@define()
class ImageProperties(LayoutNode):
    general: list[GeneralProperties] = field(factory=lambda: [GeneralProperties()])
    imageScaling: list[ImageScalingProperties] = field(factory=lambda: [ImageScalingProperties()])


@define()
class Image(BaseVisual):
    visualType: str = "image"

    drillFilterOtherVisuals: bool = True
    objects: ImageProperties = field(factory=ImageProperties, repr=False)
