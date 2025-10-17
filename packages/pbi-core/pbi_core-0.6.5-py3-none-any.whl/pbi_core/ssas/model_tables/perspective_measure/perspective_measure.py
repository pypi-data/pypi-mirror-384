import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.measure import Measure
    from pbi_core.ssas.model_tables.perspective_table import PerspectiveTable


@define()
class PerspectiveMeasure(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/d6bda989-a6d0-42c9-954b-3494b5857db4)
    """

    measure_id: int = field(eq=True)
    perspective_table_id: int = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.perspective_measure, init=False, repr=False, eq=False)

    def perspective_table(self) -> "PerspectiveTable":
        return self._tabular_model.perspective_tables.find(self.perspective_table_id)

    def measure(self) -> "Measure":
        return self._tabular_model.measures.find(self.measure_id)
