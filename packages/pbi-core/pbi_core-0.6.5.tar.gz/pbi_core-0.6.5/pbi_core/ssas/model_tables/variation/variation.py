from typing import TYPE_CHECKING, Literal

from attrs import field

from pbi_core.attrs import define
from pbi_core.lineage import LineageNode
from pbi_core.ssas.model_tables.base import SsasRenameRecord
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.column import Column
    from pbi_core.ssas.model_tables.hierarchy import Hierarchy
    from pbi_core.ssas.model_tables.relationship import Relationship


@define()
class Variation(SsasRenameRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/b9dfeb51-cbb6-4eab-91bd-fa2b23f51ca3)
    """

    column: int | None = field(default=None, eq=True)  # TODO: pbi says this shouldn't exist
    column_id: int = field(eq=True)
    default_column_id: int | None = field(default=None, eq=True)
    default_hierarchy_id: int = field(eq=True)
    description: str | None = field(default=None, eq=True)
    is_default: bool = field(eq=True)
    name: str = field(eq=True)
    relationship_id: int = field(eq=True)

    _commands: RenameCommands = field(default=SsasCommands.variation, init=False, repr=False)

    def get_column(self) -> "Column":
        """Name is bad to not consistent with other methods because the column field in this entity :(."""
        return self._tabular_model.columns.find(self.column_id)

    def default_column(self) -> "Column | None":
        if self.default_column_id is None:
            return None
        return self._tabular_model.columns.find(self.default_column_id)

    def default_hierarchy(self) -> "Hierarchy":
        return self._tabular_model.hierarchies.find(self.default_hierarchy_id)

    def relationship(self) -> "Relationship":
        return self._tabular_model.relationships.find(self.relationship_id)

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(self, lineage_type)
        return LineageNode(
            self,
            lineage_type,
            [
                self.default_hierarchy().get_lineage(lineage_type),
                self.relationship().get_lineage(lineage_type),
            ],
        )
