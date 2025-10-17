from enum import Enum
from typing import Any

from pbi_core.attrs import converter, define
from pbi_core.static_files.layout._base_node import LayoutNode


class EntityType(Enum):
    NA = 1
    NA2 = 0
    NA3 = 2


@define()
class Entity(LayoutNode):
    Entity: str
    Name: str | None = None
    Type: EntityType | None = EntityType.NA2

    def table(self) -> str:
        return self.Entity

    def table_mapping(self) -> dict[str, str]:
        if self.Name is None:
            return {}
        return {self.Name: self.Entity}

    @staticmethod
    def create(entity: str) -> "Entity":
        return Entity.model_validate({"Entity": entity})

    def __repr__(self) -> str:
        return f"Entity({self.Name}: {self.Entity})"


@define()
class Source(LayoutNode):
    Source: str

    def table(self) -> str:
        return self.Source


SourceRefSource = Entity | Source


@converter.register_structure_hook
def get_source_ref_type(v: dict[str, Any], _: type | None = None) -> SourceRefSource:
    if "Source" in v:
        return Source.model_validate(v)
    if "Entity" in v:
        return Entity.model_validate(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_source_ref_type(v: SourceRefSource) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class TransformTableRef(LayoutNode):
    TransformTableRef: SourceRefSource

    def table(self, entity_mapping: dict[str, str] | None = None) -> str:
        if entity_mapping is None:
            entity_mapping = {}
        if isinstance(self.TransformTableRef, Source):
            return entity_mapping[self.TransformTableRef.table()]
        return self.TransformTableRef.table()


@define()
class SourceRef(LayoutNode):
    SourceRef: SourceRefSource

    def table(self, entity_mapping: dict[str, str] | None = None) -> str:
        if entity_mapping is None:
            entity_mapping = {}
        if isinstance(self.SourceRef, Source):
            # TODO: make this handle the utility case where the source missing should be an error and the
            # printing version where it just prints something
            if self.SourceRef.table() not in entity_mapping:
                return self.SourceRef.table()
            return entity_mapping[self.SourceRef.table()]
        return self.SourceRef.table()


SourceExpressionUnion = TransformTableRef | SourceRef


@converter.register_structure_hook
def get_source_expression_type(v: dict[str, Any], _: type | None = None) -> SourceExpressionUnion:
    if "SourceRef" in v:
        return SourceRef.model_validate(v)
    if "TransformTableRef" in v:
        return TransformTableRef.model_validate(v)
    raise TypeError(v)


@converter.register_unstructure_hook
def unparse_source_expression_type(v: SourceExpressionUnion) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class SourceExpression(LayoutNode):
    Expression: SourceExpressionUnion
    Property: str

    def table(self, entity_mapping: dict[str, str] | None = None) -> str:
        if entity_mapping is None:
            entity_mapping = {}
        return self.Expression.table(entity_mapping)

    def column(self) -> str:
        return self.Property

    @staticmethod
    def create(table: str, column: str) -> "SourceExpression":
        entity = Entity.create(entity=table)
        ret: SourceExpression = SourceExpression.model_validate({
            "Expression": {
                "SourceRef": entity.model_dump_json(),
                "Property": column,
            },
        })
        return ret
