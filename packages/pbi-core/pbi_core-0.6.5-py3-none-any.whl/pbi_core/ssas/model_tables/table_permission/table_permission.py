import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.model_tables.enums import DataState
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

from .enums import MetadataPermission

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.role import Role
    from pbi_core.ssas.model_tables.table import Table


@define()
class TablePermission(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/ac2ceeb3-a54e-4bf5-85b0-a770d4b1716e)
    """

    error_message: Final[str | None] = field(default=None, eq=False, on_setattr=setters.frozen)
    filter_expression: str | None = field(default=None, eq=True)
    metadata_permission: MetadataPermission = field(eq=True)
    role_id: int = field(eq=True)
    state: Final[DataState] = field(eq=False, on_setattr=setters.frozen, default=DataState.READY)
    table_id: int = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.table_permission, init=False, repr=False, eq=False)

    def __repr__(self) -> str:
        role_name = self.role().pbi_core_name()
        table_name = self.table().pbi_core_name()
        return f"TablePermission(id: {self.id}, role: {role_name}, table: {table_name})"

    def role(self) -> "Role":
        return self._tabular_model.roles.find(self.role_id)

    def table(self) -> "Table":
        return self._tabular_model.tables.find(self.table_id)
