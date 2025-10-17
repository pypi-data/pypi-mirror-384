import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import BaseValidation, Json, define
from pbi_core.ssas.model_tables.base import SsasRenameRecord, SsasTable
from pbi_core.ssas.model_tables.enums import ObjectType
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands
from pbi_core.static_files.layout.sources.column import ColumnSource

if TYPE_CHECKING:
    from collections.abc import Callable


@define()
class BinSize(BaseValidation):
    value: float = field(eq=True)
    unit: int = field(eq=True)


@define()
class BinningMetadata(BaseValidation):
    binSize: BinSize = field(eq=True)


@define()
class ExtendedPropertyValue(BaseValidation):
    version: int = field(eq=True)
    daxTemplateName: str | None = field(default=None, eq=True)
    groupedColumns: list[ColumnSource] | None = field(default=None, eq=True)
    binningMetadata: BinningMetadata | None = field(default=None, eq=True)


@define()
class ExtendedProperty(SsasRenameRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/5c1521e5-defe-4ba2-9558-b67457e94569)
    """

    object_id: int = field(eq=True)
    object_type: ObjectType = field(eq=True)
    name: str = field(eq=True)
    type: ObjectType = field(eq=True)
    value: Json[ExtendedPropertyValue] = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: RenameCommands = field(
        default=SsasCommands.extended_property,
        init=False,
        repr=False,
        eq=False,
    )

    def object(self) -> "SsasTable":
        """Returns the object the property is describing."""
        mapper: dict[ObjectType, Callable[[int], SsasTable]] = {
            ObjectType.MODEL: lambda _x: self._tabular_model.model,
            ObjectType.DATASOURCE: self._tabular_model.data_sources.find,
            ObjectType.TABLE: self._tabular_model.tables.find,
            ObjectType.COLUMN: self._tabular_model.columns.find,
            ObjectType.ATTRIBUTE_HIERARCHY: self._tabular_model.attribute_hierarchies.find,
            ObjectType.PARTITION: self._tabular_model.partitions.find,
            ObjectType.RELATIONSHIP: self._tabular_model.relationships.find,
            ObjectType.MEASURE: self._tabular_model.measures.find,
            ObjectType.HIERARCHY: self._tabular_model.hierarchies.find,
            ObjectType.LEVEL: self._tabular_model.levels.find,
            ObjectType.KPI: self._tabular_model.kpis.find,
            ObjectType.CULTURE: self._tabular_model.cultures.find,
            ObjectType.LINGUISTIC_METADATA: self._tabular_model.linguistic_metadata.find,
            ObjectType.PERSPECTIVE: self._tabular_model.perspectives.find,
            ObjectType.PERSPECTIVE_TABLE: self._tabular_model.perspective_tables.find,
            ObjectType.PERSPECTIVE_HIERARCHY: self._tabular_model.perspective_hierarchies.find,
            ObjectType.PERSPECTIVE_MEASURE: self._tabular_model.perspective_measures.find,
            ObjectType.ROLE: self._tabular_model.roles.find,
            ObjectType.ROLE_MEMBERSHIP: self._tabular_model.role_memberships.find,
            ObjectType.TABLE_PERMISSION: self._tabular_model.table_permissions.find,
            ObjectType.VARIATION: self._tabular_model.variations.find,
            ObjectType.EXPRESSION: self._tabular_model.expressions.find,
            ObjectType.COLUMN_PERMISSION: self._tabular_model.column_permissions.find,
            ObjectType.CALCULATION_GROUP: self._tabular_model.calculation_groups.find,
            ObjectType.QUERY_GROUP: self._tabular_model.query_groups.find,
        }
        return mapper[self.object_type](self.object_id)

    @classmethod
    def _db_command_obj_name(cls) -> str:
        return "ExtendedProperties"
