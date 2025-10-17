import datetime
from typing import TYPE_CHECKING, Final, Literal

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.lineage import LineageNode
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.measure import Measure


@define()
class KPI(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/1289ceca-8113-4019-8f90-8132a91117cf)
    """

    description: str | None = field(default=None, eq=True)
    measure_id: int = field(eq=True)
    status_description: str | None = field(default=None, eq=True)
    status_expression: str = field(eq=True)
    status_graphic: str = field(eq=True)
    target_description: str | None = field(default=None, eq=True)
    target_expression: str = field(eq=True)
    target_format_string: str = field(eq=True)
    trend_description: str | None = field(default=None, eq=True)
    trend_expression: str | None = field(default=None, eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.kpi, init=False, repr=False, eq=False)

    def pbi_core_name(self) -> str:
        """Returns the name displayed in the PBIX report."""
        return self.measure().pbi_core_name()

    def measure(self) -> "Measure":
        return self._tabular_model.measures.find({"id": self.measure_id})

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(self, lineage_type)
        return LineageNode(self, lineage_type, [self.measure().get_lineage(lineage_type)])

    @classmethod
    def _db_command_obj_name(cls) -> str:
        return "Kpis"
