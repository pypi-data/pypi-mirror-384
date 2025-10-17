import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.hierarchy import Hierarchy
    from pbi_core.ssas.model_tables.perspective_table import PerspectiveTable


@define()
class PerspectiveHierarchy(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/07941935-98bf-4e14-ab40-ef97d5c29765)
    """

    hierarchy_id: int = field(eq=True)
    perspective_table_id: int = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(
        default=SsasCommands.perspective_hierarchy,
        init=False,
        repr=False,
        eq=False,
    )

    def perspective_table(self) -> "PerspectiveTable":
        return self._tabular_model.perspective_tables.find(self.perspective_table_id)

    def hierarchy(self) -> "Hierarchy":
        return self._tabular_model.hierarchies.find(self.hierarchy_id)
