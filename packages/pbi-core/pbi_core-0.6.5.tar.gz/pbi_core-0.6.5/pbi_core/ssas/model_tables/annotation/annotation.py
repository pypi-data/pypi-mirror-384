import datetime
from typing import Final, Literal

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.lineage import LineageNode
from pbi_core.ssas.model_tables.base import SsasRenameRecord, SsasTable
from pbi_core.ssas.model_tables.enums import ObjectType
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands


@define()
class Annotation(SsasRenameRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/7a16a837-cb88-4cb2-a766-a97c4d0e1f43)
    """

    object_id: int = field(eq=True)
    object_type: ObjectType = field(eq=True)
    name: str = field(eq=True)
    value: str | None = field(eq=True, default=None)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: RenameCommands = field(default=SsasCommands.annotation, init=False, repr=False)

    def object(self) -> SsasTable:
        """Returns the object the annotation is describing.

        Raises:
            TypeError: When the Object Type doesn't map to a know SSAS entity type

        """
        mapper = {
            ObjectType.ATTRIBUTE_HIERARCHY: self._tabular_model.attribute_hierarchies.find,
            ObjectType.CALCULATION_GROUP: self._tabular_model.calculation_groups.find,
            ObjectType.COLUMN: self._tabular_model.columns.find,
            ObjectType.COLUMN_PERMISSION: self._tabular_model.column_permissions.find,
            ObjectType.CULTURE: self._tabular_model.cultures.find,
            ObjectType.DATASOURCE: self._tabular_model.data_sources.find,
            ObjectType.EXPRESSION: self._tabular_model.expressions.find,
            ObjectType.HIERARCHY: self._tabular_model.hierarchies.find,
            ObjectType.KPI: self._tabular_model.kpis.find,
            ObjectType.LEVEL: self._tabular_model.levels.find,
            ObjectType.LINGUISTIC_METADATA: self._tabular_model.linguistic_metadata.find,
            ObjectType.MEASURE: self._tabular_model.measures.find,
            ObjectType.MODEL: lambda _x: self._tabular_model.model,
            ObjectType.PARTITION: self._tabular_model.partitions.find,
            ObjectType.PERSPECTIVE: self._tabular_model.perspectives.find,
            ObjectType.PERSPECTIVE_HIERARCHY: self._tabular_model.perspective_hierarchies.find,
            ObjectType.PERSPECTIVE_MEASURE: self._tabular_model.perspective_measures.find,
            ObjectType.PERSPECTIVE_TABLE: self._tabular_model.perspective_tables.find,
            ObjectType.QUERY_GROUP: self._tabular_model.query_groups.find,
            ObjectType.RELATIONSHIP: self._tabular_model.relationships.find,
            ObjectType.ROLE: self._tabular_model.roles.find,
            ObjectType.ROLE_MEMBERSHIP: self._tabular_model.role_memberships.find,
            ObjectType.TABLE: self._tabular_model.tables.find,
            ObjectType.TABLE_PERMISSION: self._tabular_model.table_permissions.find,
            ObjectType.VARIATION: self._tabular_model.variations.find,
        }
        if self.object_type not in mapper:
            msg = f"Object Type {self.object_type} does not map to a known SSAS entity type."
            raise TypeError(msg)
        return mapper[self.object_type](self.object_id)

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(self, lineage_type)
        return LineageNode(self, lineage_type, [self.object().get_lineage(lineage_type)])
