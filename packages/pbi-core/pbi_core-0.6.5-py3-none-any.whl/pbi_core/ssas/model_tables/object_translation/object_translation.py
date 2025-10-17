import datetime
from typing import Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord, SsasTable
from pbi_core.ssas.model_tables.enums import ObjectType
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

from .enums import Property


@define()
class ObjectTranslation(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/1eade819-5599-4ddd-9bf5-7d365806069d)
    """

    altered: bool = field(eq=True)
    culture_id: int = field(eq=True)
    object_id: int = field(eq=True)
    object_type: ObjectType = field(eq=True)
    property: Property = field(eq=True)
    value: str = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.object_translation, init=False, repr=False, eq=False)

    def object(self) -> SsasTable:
        """Returns the object the annotation is describing.

        Raises:
            TypeError: When the Object Type doesn't map to a know SSAS entity type

        """
        if self.object_type == ObjectType.MODEL:
            return self._tabular_model.model
        mapper = {
            ObjectType.DATASOURCE: self._tabular_model.data_sources,
            ObjectType.TABLE: self._tabular_model.tables,
            ObjectType.COLUMN: self._tabular_model.columns,
            ObjectType.ATTRIBUTE_HIERARCHY: self._tabular_model.attribute_hierarchies,
            ObjectType.PARTITION: self._tabular_model.partitions,
            ObjectType.RELATIONSHIP: self._tabular_model.relationships,
            ObjectType.MEASURE: self._tabular_model.measures,
            ObjectType.HIERARCHY: self._tabular_model.hierarchies,
            ObjectType.LEVEL: self._tabular_model.levels,
            ObjectType.KPI: self._tabular_model.kpis,
            ObjectType.CULTURE: self._tabular_model.cultures,
            ObjectType.LINGUISTIC_METADATA: self._tabular_model.linguistic_metadata,
            ObjectType.PERSPECTIVE: self._tabular_model.perspectives,
            ObjectType.PERSPECTIVE_TABLE: self._tabular_model.perspective_tables,
            ObjectType.PERSPECTIVE_HIERARCHY: self._tabular_model.perspective_hierarchies,
            ObjectType.PERSPECTIVE_MEASURE: self._tabular_model.perspective_measures,
            ObjectType.ROLE: self._tabular_model.roles,
            ObjectType.ROLE_MEMBERSHIP: self._tabular_model.role_memberships,
            ObjectType.TABLE_PERMISSION: self._tabular_model.table_permissions,
            ObjectType.VARIATION: self._tabular_model.variations,
            ObjectType.EXPRESSION: self._tabular_model.expressions,
            ObjectType.COLUMN_PERMISSION: self._tabular_model.column_permissions,
            ObjectType.CALCULATION_GROUP: self._tabular_model.calculation_groups,
            ObjectType.QUERY_GROUP: self._tabular_model.query_groups,
        }
        if self.object_type in mapper:
            return mapper[self.object_type]
        msg = f"No logic implemented for type {self.object_type}"
        raise TypeError(msg)
