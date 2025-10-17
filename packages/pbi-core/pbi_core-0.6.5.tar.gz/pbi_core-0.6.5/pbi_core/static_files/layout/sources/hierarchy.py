from typing import Any

from pbi_core.attrs import converter, define
from pbi_core.static_files.layout._base_node import LayoutNode

from .base import SourceExpression, SourceRef


@define()
class PropertyVariationSource(LayoutNode):
    Expression: SourceRef
    Name: str
    Property: str

    def column(self) -> str:
        return self.Property


@define()
class _PropertyVariationSourceHelper(LayoutNode):
    PropertyVariationSource: PropertyVariationSource

    def table(self, entity_mapping: dict[str, str] | None = None) -> str:
        if entity_mapping is None:
            entity_mapping = {}
        return self.PropertyVariationSource.Expression.table(entity_mapping)

    def column(self) -> str:
        return self.PropertyVariationSource.column()


ConditionType = SourceExpression | _PropertyVariationSourceHelper | SourceRef


@converter.register_structure_hook
def get_bookmark_type(v: dict[str, Any], _: type | None = None) -> ConditionType:
    if "PropertyVariationSource" in v:
        return _PropertyVariationSourceHelper.model_validate(v)
    if "SourceRef" in v:
        return SourceRef.model_validate(v)
    if "Property" in v:
        return SourceExpression.model_validate(v)
    raise ValueError


@converter.register_unstructure_hook
def unparse_bookmark_type(v: ConditionType) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class _HierarchySourceHelper(LayoutNode):
    Expression: ConditionType
    Hierarchy: str | None = None


@define()
class HierarchySource(LayoutNode):
    Hierarchy: _HierarchySourceHelper


@define()
class _HierarchyLevelSourceHelper(LayoutNode):
    Expression: HierarchySource
    Level: str | None = None


@define()
class HierarchyLevelSource(LayoutNode):
    HierarchyLevel: _HierarchyLevelSourceHelper
    Name: str | None = None
    NativeReferenceName: str | None = None

    def __repr__(self) -> str:
        table = self.HierarchyLevel.Expression.Hierarchy.Expression.table()
        if isinstance(self.HierarchyLevel.Expression.Hierarchy.Expression, SourceRef):
            column = self.HierarchyLevel.Expression.Hierarchy.Hierarchy
        else:
            column = self.HierarchyLevel.Expression.Hierarchy.Expression.column()
        level = self.HierarchyLevel.Level
        return f"HierarchyLevelSource({table}.{column}.{level})"
