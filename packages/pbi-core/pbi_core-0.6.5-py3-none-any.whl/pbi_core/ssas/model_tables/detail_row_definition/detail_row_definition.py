import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.model_tables.enums import DataState, ObjectType
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.measure import Measure
    from pbi_core.ssas.model_tables.table import Table


@define()
class DetailRowDefinition(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/7eb1e044-4eed-467d-b10f-ce208798ddb0)

    Note:
        Additional details can be found here: [SQLBI](https://www.sqlbi.com/articles/controlling-drillthrough-in-excel-pivottables-connected-to-power-bi-or-analysis-services/)

    """

    error_message: Final[str | None] = field(
        eq=False,
        on_setattr=setters.frozen,
    )  # error message is read-only, so should not be edited
    expression: str = field(eq=True)
    object_id: int = field(eq=True)
    object_type: ObjectType = field(eq=True)
    state: Final[DataState] = field(eq=False, on_setattr=setters.frozen, default=DataState.READY)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.detail_row_definition, init=False, repr=False)

    @classmethod
    def _db_type_name(cls) -> str:
        return "DetailRowsDefinition"

    def object(self) -> "Table | Measure":
        match self.object_type:
            case ObjectType.MEASURE:
                return self._tabular_model.measures.find(self.object_id)
            case ObjectType.TABLE:
                return self._tabular_model.tables.find(self.object_id)
            case _:
                msg = f"No logic for object type: {self.object_type}"
                raise TypeError(msg)
