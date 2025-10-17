from attrs import field

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

from .enums import Granularity, PolicyType, RefreshMode


@define()
class RefreshPolicy(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/e11ae511-5064-470b-8abc-e2a4dd3999e6)
    This class represents the refresh policy for a partition in a Tabular model.
    """

    incremental_granularity: Granularity = field(eq=True)
    incremental_periods: int = field(eq=True)
    incremental_periods_offset: int = field(eq=True)
    mode: RefreshMode = field(eq=True)
    policy_type: PolicyType = field(eq=True)
    polling_expression: str = field(eq=True)
    rolling_window_granularity: Granularity = field(eq=True)
    rolling_window_periods: int = field(eq=True)
    source_expression: str = field(eq=True)
    table_id: int = field(eq=True)

    _commands: BaseCommands = field(default=SsasCommands.refresh_policy, init=False, repr=False, eq=False)
