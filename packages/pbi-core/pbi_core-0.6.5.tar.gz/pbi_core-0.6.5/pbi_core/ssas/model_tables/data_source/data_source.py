import datetime
from typing import TYPE_CHECKING, Final

from attrs import field

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasRenameRecord
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands

from .enums import DataSourceType, ImpersonationMode, Isolation

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.model import Model


@define()
class DataSource(SsasRenameRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/ee12dcb7-096e-4e4e-99a4-47caeb9390f5)
    """

    account: str | None = field(default=None, eq=True)
    connection_string: str = field(eq=True)
    context_expression: str | None = field(default=None, eq=True)
    credential: str | None = field(default=None, eq=True)
    description: str | None = field(default=None, eq=True)
    impersonation_mode: ImpersonationMode = field(eq=True)
    isolation: Isolation = field(eq=True)
    max_connections: int = field(eq=True)
    model_id: int = field(eq=True, repr=False)
    name: str = field(eq=True)
    options: str | None = field(default=None, eq=True)
    password: str | None = field(default=None, eq=True)
    provider: str | None = field(default=None, eq=True)
    timeout: int = field(eq=True)
    type: DataSourceType = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, repr=False)

    _commands: RenameCommands = field(default=SsasCommands.data_source, init=False, repr=False, eq=False)

    def model(self) -> "Model":
        return self._tabular_model.model
