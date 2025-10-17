from pbi_core.attrs import define

from ._base_node import LayoutNode
from .condition import ConditionType


@define()
class DataViewWildcard(LayoutNode):
    matchingOption: int
    roles: list[str] | None = None


@define()
class SelectorData(LayoutNode):
    roles: list[str] | None = None
    dataViewWildcard: DataViewWildcard | None = None
    scopeId: ConditionType | None = None


# TODO: possibly replace with a union?
@define()
class Selector(LayoutNode):
    id: str | None = None
    # Weird values, pretty confident this is not an enum
    metadata: str | None = None
    data: list[SelectorData] | None = None
