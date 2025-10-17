from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode

from .base import SourceExpression


@define()
class ColumnSource(LayoutNode):
    Column: SourceExpression
    Name: str | None = None  # only seen on a couple TopN filters
    NativeReferenceName: str | None = None  # only for Layout.Visual.Query

    def __repr__(self) -> str:
        return f"ColumnSource({self.Column.Expression.table()}.{self.Column.Property})"

    def filter_name(self) -> str:
        return self.Column.Property
