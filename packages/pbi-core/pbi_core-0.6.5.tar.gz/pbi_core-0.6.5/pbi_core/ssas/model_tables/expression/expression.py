import datetime
from enum import Enum
from typing import TYPE_CHECKING, Final, Literal
from uuid import UUID, uuid4

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasRenameRecord, SsasTable
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.column import Column
    from pbi_core.ssas.model_tables.model import Model
    from pbi_core.ssas.model_tables.query_group import QueryGroup
from pbi_core.lineage import LineageNode


class Kind(Enum):
    M = 0


@define()
class Expression(SsasRenameRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/61f98e45-d5e3-4435-b829-2f2f043839c1)
    """

    description: str | None = field(default=None, eq=True)
    expression: str = field(eq=True)
    kind: Kind = field(eq=True, default=Kind.M)
    model_id: Final[int] = field(eq=False)
    name: str = field(eq=True)
    parameter_values_column_id: int | None = field(default=None, eq=True)
    query_group_id: int | None = field(default=None, eq=True)

    lineage_tag: UUID = field(factory=uuid4, eq=True, repr=False)
    source_lineage_tag: UUID = field(factory=uuid4, eq=True, repr=False)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: RenameCommands = field(default=SsasCommands.expression, init=False, repr=False, eq=False)

    def model(self) -> "Model":
        return self._tabular_model.model

    def parameter_values_column(self) -> "Column | None":
        if self.parameter_values_column_id is None:
            return None
        return self._tabular_model.columns.find(self.parameter_values_column_id)

    def query_group(self) -> "QueryGroup | None":
        return self._tabular_model.query_groups.find({"id": self.query_group_id})

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(self, lineage_type)
        parent_nodes: list[SsasTable | None] = [self.model(), self.query_group()]
        parent_lineage = [p.get_lineage(lineage_type) for p in parent_nodes if p is not None]
        return LineageNode(self, lineage_type, parent_lineage)
