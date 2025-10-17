import datetime
from typing import TYPE_CHECKING, Final, Literal

from attrs import field, setters

from pbi_core.attrs import BaseValidation, Json, define
from pbi_core.lineage import LineageNode
from pbi_core.ssas.model_tables.base import RefreshType, SsasModelRecord
from pbi_core.ssas.server._commands import ModelCommands
from pbi_core.ssas.server.utils import SsasCommands

from .enums import DefaultDataView

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.culture import Culture
    from pbi_core.ssas.model_tables.measure import Measure
    from pbi_core.ssas.model_tables.query_group import QueryGroup
    from pbi_core.ssas.model_tables.table import Table


@define()
class DataAccessOptions(BaseValidation):
    fastCombine: bool = field(default=True, eq=True)
    legacyRedirects: bool = field(default=False, eq=True)
    returnErrorValuesAsNull: bool = field(default=False, eq=True)


@define()
class Model(SsasModelRecord):
    """tbd.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/60094cd5-1c7e-4353-9299-251bfa838cc6)
    """

    _default_refresh_type: RefreshType = field(default=RefreshType.CALCULATE, init=False, repr=False, eq=False)

    automatic_aggregation_options: str | None = field(default=None, eq=True)
    collation: str | None = field(default=None, eq=True)
    culture: str = field(eq=True)
    data_access_options: Json[DataAccessOptions] = field(factory=DataAccessOptions, eq=True)
    data_source_default_max_connections: int = field(eq=True)
    data_source_variables_override_behavior: int = field(eq=True)
    default_data_view: DefaultDataView = field(eq=True)
    default_measure_id: int | None = field(default=None, eq=True)
    default_mode: int = field(eq=True)
    default_powerbi_data_source_version: int = field(eq=True)
    description: str | None = field(default=None, eq=True)
    discourage_composite_models: bool = field(default=True, eq=True)
    discourage_implicit_measures: bool = field(default=False, eq=True)
    disable_auto_exists: int | None = field(default=None, eq=True)
    force_unique_names: bool = field(default=False, eq=True)
    m_attributes: str | None = field(default=None, eq=True)
    max_parallelism_per_refresh: int | None = field(default=None, eq=True)
    max_parallelism_per_query: int | None = field(default=None, eq=True)
    name: str = field(eq=True)
    source_query_culture: str = field(default="en-US", eq=True)
    storage_location: str | None = field(default=None, eq=True)
    version: int = field(eq=True)

    modified_time: Final[datetime.datetime] = field(
        eq=False,
        on_setattr=setters.frozen,
        repr=False,
    )
    structure_modified_time: Final[datetime.datetime] = field(
        eq=False,
        on_setattr=setters.frozen,
        repr=False,
    )

    _commands: ModelCommands = field(default=SsasCommands.model, init=False, repr=False, eq=False)

    def default_measure(self) -> "Measure | None":
        if self.default_measure_id is None:
            return None
        return self._tabular_model.measures.find(self.default_measure_id)

    def cultures(self) -> set["Culture"]:
        return self._tabular_model.cultures.find_all({"model_id": self.id})

    def tables(self) -> set["Table"]:
        return self._tabular_model.tables.find_all({"model_id": self.id})

    def query_groups(self) -> set["QueryGroup"]:
        return self._tabular_model.query_groups.find_all({"model_id": self.id})

    @classmethod
    def _db_command_obj_name(cls) -> str:
        return "Model"

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(
                self,
                lineage_type,
                [c.get_lineage(lineage_type) for c in self.cultures()]
                + [t.get_lineage(lineage_type) for t in self.tables()]
                + [q.get_lineage(lineage_type) for q in self.query_groups()],
            )
        return LineageNode(self, lineage_type)
