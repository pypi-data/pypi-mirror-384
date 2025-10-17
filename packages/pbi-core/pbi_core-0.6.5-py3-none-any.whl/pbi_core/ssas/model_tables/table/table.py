import datetime
from typing import TYPE_CHECKING, Final, Literal
from uuid import UUID, uuid4

from attrs import field, setters
from bs4 import BeautifulSoup

from pbi_core.attrs import define
from pbi_core.lineage import LineageNode
from pbi_core.ssas.model_tables.base import RefreshType, SsasRefreshRecord
from pbi_core.ssas.model_tables.column import Column
from pbi_core.ssas.model_tables.enums import DataCategory
from pbi_core.ssas.model_tables.measure import Measure
from pbi_core.ssas.model_tables.partition import Partition
from pbi_core.ssas.server._commands import RefreshCommands
from pbi_core.ssas.server.utils import SsasCommands
from pbi_core.static_files.layout.sources.base import Entity

from . import set_name

if TYPE_CHECKING:
    from pbi_parsers.pq.misc.external_sources import BaseExternalSource

    from pbi_core.ssas.model_tables.calculation_group import CalculationGroup
    from pbi_core.ssas.model_tables.detail_row_definition import DetailRowDefinition
    from pbi_core.ssas.model_tables.model import Model
    from pbi_core.ssas.model_tables.refresh_policy import RefreshPolicy
    from pbi_core.static_files.layout.layout import Layout


@define()
class Table(SsasRefreshRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/6360ac84-0717-4170-bce0-284cbef419ca)
    """

    _default_refresh_type: RefreshType = field(default=RefreshType.DATA_ONLY, init=False, repr=False, eq=False)

    alternate_source_precedence: int = field(eq=True)
    calculation_group_id: int | None = field(default=None, eq=True)
    data_category: DataCategory | None = field(default=None, eq=True)
    default_detail_rows_defintion_id: int | None = field(default=None, eq=True)
    description: str | None = field(default=None, eq=True)
    """A description of the table, which may be used in the hover tooltip in edit mode"""
    exclude_from_automatic_aggregations: bool = False
    exclude_from_model_refresh: bool = field(default=False, eq=True)
    """Controls whether this table is included in the model-wide refresh process"""
    is_hidden: bool = field(default=False, eq=True)
    """Controls whether the table appears in the edit mode of the report"""
    is_private: bool = field(default=False, eq=True)
    model_id: int = field(eq=True, repr=False)
    """The ID of the model this table belongs to"""
    name: str = field(eq=True)
    """The name of the table as it appears in the report"""
    refresh_policy_id: int | None = field(default=None, eq=True)
    show_as_variations_only: bool = field(default=False, eq=True)
    system_flags: int = field(eq=True)
    system_managed: bool | None = field(default=None, eq=True)
    table_storage_id: int | None = field(default=None, eq=True)

    lineage_tag: UUID = field(factory=uuid4, eq=True, repr=False)
    source_lineage_tag: UUID = field(factory=uuid4, eq=True, repr=False)

    modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)
    structure_modified_time: Final[datetime.datetime] = field(eq=False, on_setattr=setters.frozen, repr=False)

    _commands: RefreshCommands = field(default=SsasCommands.table, init=False, repr=False, eq=False)

    def set_name(self, new_name: str, layout: "Layout") -> None:
        """Renames the measure and update any dependent expressions to use the new name.

        Since measures are referenced by name in DAX expressions, renaming a measure will break any dependent
        expressions.
        """
        entities = layout.find_all(Entity, lambda e: e.Entity == self.name)
        for entity in entities:
            entity.Entity = new_name

        set_name.fix_dax(self, new_name)
        self.name = new_name

    def calculation_group(self) -> "CalculationGroup | None":
        if self.calculation_group_id is None:
            return None
        return self._tabular_model.calculation_groups.find(self.calculation_group_id)

    def refresh_policy(self) -> "RefreshPolicy | None":
        if self.refresh_policy_id is None:
            return None
        return self._tabular_model.refresh_policies.find(self.refresh_policy_id)

    def is_system_table(self) -> bool:
        return bool(self.system_flags >> 1 % 2)

    def is_from_calculated_table(self) -> bool:
        return bool(self.system_flags % 2)

    def data(self, head: int = 100) -> list[dict[str, int | float | str]]:
        """Extracts records from the table in SSAS.

        Args:
            head (int): The number of records to return from the table.

        Returns:
            list[dict[str, int | float | str]]: A list of SSAS records in dictionary form.
                The keys are the field names and the values are the record values

        """
        return self._tabular_model.server.query_dax(
            f"EVALUATE TOPN({head}, ALL('{self.name}'))",
            db_name=self._tabular_model.db_name,
        )

    def partitions(self) -> set[Partition]:
        """Get associated dependent partitions.

        Returns:
            (set[Partition]): A list of the partitions containing data for this table

        """
        return self._tabular_model.partitions.find_all({"table_id": self.id})

    def columns(self) -> set[Column]:
        """Get associated dependent partitions.

        Returns:
            (set[Column]): A list of the columns in this table

        """
        return self._tabular_model.columns.find_all({"table_id": self.id})

    def default_row_definition(self) -> "DetailRowDefinition | None":
        if self.default_detail_rows_defintion_id is None:
            return None
        return self._tabular_model.detail_row_definitions.find(self.default_detail_rows_defintion_id)

    def table_measures(self) -> set[Measure]:
        """Get measures saved to this table.

        Returns:
            (set[Measure]): A list of measures saved to this table

        Note:
            These measures do not necessarily have calculations that depend on this table.
                For that use `table.measures()`

        """
        return self._tabular_model.measures.find_all({"table_id": self.id})

    def measures(self, *, recursive: bool = False) -> set[Measure]:
        """Get measures that logically depend on this table.

        Examples:
            ```python
            print(measure.expression)
            # sumx(example, [a])

            Table(name=example).measures()
            # [..., Measure(name='measure'), ...]
            ```
        Args:
            recursive (bool): Whether to include measures that depend on other measures.

        Returns:
            (set[Measure]): A list of measures that logically depend this table

        Note:
            These measures are not necessarily saved physically to this table. For that use `table.table_measures()`

        """
        ret = set()
        for col in self.columns():
            ret.update(col.child_measures(recursive=recursive))
        return ret

    def model(self) -> "Model":
        return self._tabular_model.model

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(
                self,
                lineage_type,
                [col.get_lineage(lineage_type) for col in self.columns()]
                + [partition.get_lineage(lineage_type) for partition in self.partitions()]
                + [measure.get_lineage(lineage_type) for measure in self.measures()],
            )
        return LineageNode(self, lineage_type, [self.model().get_lineage(lineage_type)])

    def refresh(self, *, include_model_refresh: bool = True) -> list[BeautifulSoup]:  # pyright: ignore reportIncompatibleMethodOverride
        """Needs a model refresh to properly propogate the update."""
        if include_model_refresh:
            return [
                super().refresh(),
                self.model().refresh(),
            ]
        return [super().refresh()]

    def external_sources(self) -> list["BaseExternalSource"]:
        return list({source for partition in self.partitions() for source in partition.external_sources()})
