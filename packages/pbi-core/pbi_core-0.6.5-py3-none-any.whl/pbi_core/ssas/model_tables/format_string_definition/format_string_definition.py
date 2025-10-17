import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord, SsasTable
from pbi_core.ssas.model_tables.enums import DataState, ObjectType
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_parsers import dax

    from pbi_core.ssas.model_tables._group import Group


@define()
class FormatStringDefinition(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/b756b0c1-c912-4218-80dc-7ff09d0968ff)
    """

    object_type: ObjectType = field(eq=True)
    object_id: int = field(eq=True, on_setattr=setters.frozen)
    error_message: Final[str | None] = field(eq=False, default=None, on_setattr=setters.frozen)
    """When no issue exists, this field is blank"""
    expression: str = field(eq=True)
    """The DAX expression defining the format string."""
    state: Final[DataState] = field(eq=False, on_setattr=setters.frozen, default=DataState.READY)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(
        default=SsasCommands.format_string_definition,
        init=False,
        repr=False,
        eq=False,
    )

    def pbi_core_name(self) -> str:
        return str(self.object_id)

    def object(self) -> SsasTable:
        """Returns the object the annotation is describing.

        Raises:
            TypeError: When the Object Type doesn't map to a know SSAS entity type

        """
        if self.object_type == ObjectType.MODEL:
            return self._tabular_model.model

        type_mapper: dict[ObjectType, Group] = {
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
        if self.object_type not in type_mapper:
            msg = f"Object Type {self.object_type} does not map to a known SSAS entity type."
            raise TypeError(msg)

        return type_mapper[self.object_type].find(self.object_id)

    def expression_ast(self) -> "dax.Expression | None":
        from pbi_parsers import dax  # noqa: PLC0415

        if not isinstance(self.expression, str):
            return None
        ret = dax.to_ast(self.expression)
        if ret is None:
            msg = "Failed to parse DAX expression from format string definition"
            raise ValueError(msg)
        return ret

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id}: {self.object():!r})"
