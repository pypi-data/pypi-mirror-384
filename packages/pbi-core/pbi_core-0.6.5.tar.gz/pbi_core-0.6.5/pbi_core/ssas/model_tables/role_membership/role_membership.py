import datetime
from typing import TYPE_CHECKING, Final

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasEditableRecord
from pbi_core.ssas.server._commands import BaseCommands
from pbi_core.ssas.server.utils import SsasCommands

from .enums import MemberType

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.role import Role


@define()
class RoleMembership(SsasEditableRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/dbecc1f4-142b-4765-8374-a4d4dc51313b)
    """

    identity_provider: str = field(eq=True)
    member_id: str = field(eq=True)
    member_name: str = field(eq=True)
    member_type: MemberType = field(eq=True)
    role_id: int = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: BaseCommands = field(default=SsasCommands.role_membership, init=False, repr=False, eq=False)

    def role(self) -> "Role":
        return self._tabular_model.roles.find(self.role_id)
