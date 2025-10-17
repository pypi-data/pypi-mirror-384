import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasRenameRecord
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands

from .enums import ModelPermission

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.model import Model
    from pbi_core.ssas.model_tables.table_permission import TablePermission


@define()
class Role(SsasRenameRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/94a8e609-b1ae-4814-b8dc-963005eebade)
    """

    description: str | None = field(default=None, eq=True)
    model_id: int = field(eq=True, repr=False)
    model_permission: ModelPermission = field(eq=True)
    name: str = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: RenameCommands = field(default=SsasCommands.role, init=False, repr=False, eq=False)

    def model(self) -> "Model":
        return self._tabular_model.model

    def table_permissions(self) -> list["TablePermission"]:
        return [tp for tp in self._tabular_model.table_permissions if tp.role_id == self.id]
