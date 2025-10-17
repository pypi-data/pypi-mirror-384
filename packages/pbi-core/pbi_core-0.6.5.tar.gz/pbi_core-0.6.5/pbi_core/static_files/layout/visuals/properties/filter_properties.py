from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode

from .base import Expression


# TODO: subclass filters so that the properties have fewer None defaults
@define()
class FilterProperties(LayoutNode):
    isInvertedSelectionMode: Expression | None = None
    requireSingleSelect: Expression | None = None


@define()
class FilterPropertiesContainer(LayoutNode):
    properties: FilterProperties


@define()
class FilterObjects(LayoutNode):
    general: list[FilterPropertiesContainer] | None = None
