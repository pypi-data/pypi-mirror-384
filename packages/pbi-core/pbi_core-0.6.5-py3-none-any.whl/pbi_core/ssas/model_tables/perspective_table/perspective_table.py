import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.perspective import Perspective
    from pbi_core.ssas.model_tables.table import Table


@define()
class PerspectiveTable(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/06bc5956-20e3-4bd2-8e5f-68a200efc18b)
    """

    include_all: bool = field(eq=True)
    perspective_id: int = field(eq=True)
    table_id: int = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.perspective_table, init=False, repr=False, eq=False)

    def perspective(self) -> "Perspective":
        return self._tabular_model.perspectives.find(self.perspective_id)

    def table(self) -> "Table":
        return self._tabular_model.tables.find(self.table_id)
