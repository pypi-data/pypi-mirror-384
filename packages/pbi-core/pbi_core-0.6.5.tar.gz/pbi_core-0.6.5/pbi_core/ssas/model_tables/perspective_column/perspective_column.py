import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.column import Column
    from pbi_core.ssas.model_tables.perspective_table import PerspectiveTable


@define()
class PerspectiveColumn(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/f468353f-81a9-4a95-bb66-8997602bcd6d)
    """

    column_id: int = field(eq=True)
    perspective_table_id: int = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.perspective_column, init=False, repr=False, eq=False)

    def perspective_table(self) -> "PerspectiveTable":
        return self._tabular_model.perspective_tables.find(self.perspective_table_id)

    def column(self) -> "Column":
        return self._tabular_model.columns.find(self.column_id)
