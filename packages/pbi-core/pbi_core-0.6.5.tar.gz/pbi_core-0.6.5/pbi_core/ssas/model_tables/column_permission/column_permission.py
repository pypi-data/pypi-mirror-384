import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.model_tables.table_permission import MetadataPermission, TablePermission
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.column import Column


@define()
class ColumnPermission(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/10566cbb-390d-470d-b0ff-fc2713277031)
    """

    column_id: int = field(eq=True)
    metadata_permission: MetadataPermission = field(eq=True)
    table_permission_id: int = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.column_permission, init=False, repr=False, eq=False)

    def table_permission(self) -> TablePermission:
        return self._tabular_model.table_permissions.find(self.table_permission_id)

    def column(self) -> "Column":
        return self._tabular_model.columns.find(self.column_id)
