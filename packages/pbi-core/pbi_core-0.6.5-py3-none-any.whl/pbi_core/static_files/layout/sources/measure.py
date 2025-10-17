from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode

from .base import SourceExpression


@define()
class MeasureSource(LayoutNode):
    Measure: SourceExpression
    Name: str | None = None
    NativeReferenceName: str | None = None
