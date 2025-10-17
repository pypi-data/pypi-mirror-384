import datetime
from typing import TYPE_CHECKING, Final

from attrs import field

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasRenameRecord
from pbi_core.ssas.model_tables.enums import DataState
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.calculation_group import CalculationGroup
    from pbi_core.ssas.model_tables.format_string_definition import FormatStringDefinition


@define()
class CalculationItem(SsasRenameRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/f5a398a7-ff65-45f0-a865-b561416f1cb4)
    """

    calculation_group_id: int = field(eq=True)
    description: str = field(eq=True, default="")
    error_message: Final[str] = field(eq=False)  # error message is read-only, so should not be edited
    expression: str = field(eq=True)
    format_string_definition_id: int = field(eq=True)
    name: str = field(eq=True)
    ordinal: int = field(eq=True)
    state: Final[DataState] = field(eq=False)

    modified_time: Final[datetime.datetime] = field(eq=False, repr=False)
    _commands: RenameCommands = field(default=SsasCommands.calculation_item, init=False, repr=False, eq=False)

    def format_string_definition(self) -> "FormatStringDefinition":
        return self._tabular_model.format_string_definitions.find(self.format_string_definition_id)

    def calculation_group(self) -> "CalculationGroup":
        return self._tabular_model.calculation_groups.find(self.calculation_group_id)
