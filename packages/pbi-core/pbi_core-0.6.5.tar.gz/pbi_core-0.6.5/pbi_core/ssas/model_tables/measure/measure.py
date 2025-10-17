import datetime
from typing import TYPE_CHECKING, Final, Literal
from uuid import UUID, uuid4

from attrs import field, setters

from pbi_core.attrs import define
from pbi_core.lineage import LineageNode
from pbi_core.ssas.model_tables.base import SsasRenameRecord, SsasTable
from pbi_core.ssas.model_tables.column import Column
from pbi_core.ssas.model_tables.enums import DataState, DataType
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands
from pbi_core.static_files.layout.sources.measure import MeasureSource

from . import set_name

if TYPE_CHECKING:
    from pbi_parsers import dax

    from pbi_core.ssas.model_tables.calc_dependency import CalcDependency
    from pbi_core.ssas.model_tables.detail_row_definition import DetailRowDefinition
    from pbi_core.ssas.model_tables.format_string_definition import FormatStringDefinition
    from pbi_core.ssas.model_tables.kpi import KPI
    from pbi_core.ssas.model_tables.table import Table
    from pbi_core.ssas.server.tabular_model.tabular_model import BaseTabularModel
    from pbi_core.static_files.layout.layout import Layout


@define()
class Measure(SsasRenameRecord):
    """TBD.

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/ab331e04-78f7-49f0-861f-3f155b8b4c5b)
    """

    data_category: str | None = field(default=None, eq=True)
    data_type: DataType = field(eq=True)
    description: str | None = field(default=None, eq=True)
    """This description will appear in the hover-over for the measure in the edit mode of the report"""

    detail_rows_definition_id: int | None = field(default=None, eq=True)
    display_folder: str | None = field(default=None, eq=True)
    error_message: Final[str | None] = field(default=None, eq=False, on_setattr=setters.frozen)
    expression: str | int | float | None = field(default=None, eq=True)
    format_string: str | int | None = field(default="0", eq=True)
    """A static definition for the formatting of the measure"""

    format_string_definition_id: int | None = field(default=None, eq=True)
    """A foreign key to a FormatStringDefinition object. Used for dynamic-type measure formatting.

    Note:
        Mutually exclusive with format_string
    """
    is_hidden: bool = field(eq=True, default=False)
    """Controls whether the measure appears in the edit mode of the report"""
    is_simple_measure: bool = field(eq=True, default=False)
    kpi_id: int | None = field(default=None, eq=True)
    name: str = field(eq=True)
    """The name of the measure"""
    state: Final[DataState] = field(eq=False, on_setattr=setters.frozen, default=DataState.READY)
    table_id: int = field(eq=True)

    lineage_tag: UUID = field(factory=uuid4, eq=True, repr=False)
    source_lineage_tag: UUID = field(factory=uuid4, eq=True, repr=False)

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

    _commands: RenameCommands = field(default=SsasCommands.measure, init=False, repr=False, eq=False)

    def set_name(self, new_name: str, layout: "Layout") -> None:
        """Renames the measure and update any dependent expressions to use the new name.

        Since measures are referenced by name in DAX expressions, renaming a measure will break any dependent
        expressions.
        """
        measures = layout.find_all(MeasureSource, lambda m: m.Measure.Property == self.name)
        for m in measures:
            m.Measure.Property = new_name
            if m.NativeReferenceName == self.name:
                m.NativeReferenceName = new_name
        set_name.fix_dax(self, new_name)
        self.name = new_name

    def expression_ast(self) -> "dax.Expression | None":
        from pbi_parsers import dax  # noqa: PLC0415

        if not isinstance(self.expression, str):
            return None
        ret = dax.to_ast(self.expression)
        if ret is None:
            msg = "Failed to parse DAX expression from measure"
            raise ValueError(msg)
        return ret

    def detail_rows_definition(self) -> "DetailRowDefinition | None":
        if self.detail_rows_definition_id is None:
            return None
        return self._tabular_model.detail_row_definitions.find(self.detail_rows_definition_id)

    def format_string_definition(self) -> "FormatStringDefinition | None":
        if self.format_string_definition_id is None:
            return None
        return self._tabular_model.format_string_definitions.find(self.format_string_definition_id)

    def KPI(self) -> "KPI | None":  # noqa: N802
        if self.kpi_id is not None:
            return self._tabular_model.kpis.find({"id": self.kpi_id})
        return None

    def table(self) -> "Table":
        """The Table object the measure is saved under."""
        return self._tabular_model.tables.find({"id": self.table_id})

    def full_name(self) -> str:
        """Returns the fully qualified name for DAX queries."""
        table_name = self.table().name
        return f"'{table_name}'[{self.name}]"

    def data(self, columns: Column | list[Column], head: int = 100) -> list[dict[str, int | float | str]]:
        if isinstance(columns, Column):
            columns = [columns]
        column_str = "\n".join(
            col.full_name() + "," for col in columns
        )  # this should eventually be converted to jinja imo
        command = f"""
        EVALUATE TOPN({head}, SUMMARIZECOLUMNS(
            {column_str}
            {columns[0].table().name},
            "measure", {self.full_name()}
        ))
        """
        return self._tabular_model.server.query_dax(command)

    def __repr__(self) -> str:
        return f"Measure({self.id}: {self.full_name()})"

    def child_measures(self, *, recursive: bool = False) -> set["Measure"]:
        dependent_measures = self._tabular_model.calc_dependencies.find_all({
            "referenced_object_type": "MEASURE",
            "referenced_table": self.table().name,
            "referenced_object": self.name,
            "object_type": "MEASURE",
        })
        child_keys: list[tuple[str | None, str]] = [(m.table, m.object) for m in dependent_measures]
        full_dependencies = [m for m in self._tabular_model.measures if (m.table().name, m.name) in child_keys]

        if recursive:
            recursive_dependencies: set[Measure] = set()
            for dep in full_dependencies:
                if f"[{self.name}]" in str(dep.expression):
                    recursive_dependencies.add(dep)
                    recursive_dependencies.update(dep.child_measures(recursive=True))
            return recursive_dependencies

        return {x for x in full_dependencies if f"[{self.name}]" in str(x.expression)}

    def parent_measures(self, *, recursive: bool = False) -> set["Measure"]:
        """Calculated columns can use Measures too :(."""
        dependent_measures: set[CalcDependency] = self._tabular_model.calc_dependencies.find_all({
            "object_type": "MEASURE",
            "table": self.table().name,
            "object": self.name,
            "referenced_object_type": "MEASURE",
        })
        parent_keys = [(m.referenced_table, m.referenced_object) for m in dependent_measures]
        full_dependencies = [m for m in self._tabular_model.measures if (m.table().name, m.name) in parent_keys]

        if recursive:
            recursive_dependencies: set[Measure] = set()
            for dep in full_dependencies:
                if f"[{dep.name}]" in str(self.expression):
                    recursive_dependencies.add(dep)
                    recursive_dependencies.update(dep.parent_measures(recursive=True))
            return recursive_dependencies

        return {x for x in full_dependencies if f"[{x.name}]" in str(self.expression)}

    def child_columns(self, *, recursive: bool = False) -> set["Column"]:
        """Only occurs when the dependent column is calculated (expression is not None)."""
        dependent_measures = self._tabular_model.calc_dependencies.find_all({
            "referenced_object_type": "MEASURE",
            "referenced_table": self.table().name,
            "referenced_object": self.name,
        })
        child_keys = [(m.table, m.object) for m in dependent_measures if m.object_type in {"CALC_COLUMN", "COLUMN"}]
        full_dependencies = [m for m in self._tabular_model.columns if (m.table().name, m.explicit_name) in child_keys]

        if recursive:
            recursive_dependencies: set[Column] = set()
            for dep in full_dependencies:
                if f"[{self.name}]" in str(dep.expression):
                    recursive_dependencies.add(dep)
                    recursive_dependencies.update(dep.child_columns(recursive=True))
            return recursive_dependencies

        return {x for x in full_dependencies if f"[{self.name}]" in str(x.expression)}

    def parent_columns(self, *, recursive: bool = False) -> set["Column"]:
        """Only occurs when column is calculated."""
        dependent_measures = self._tabular_model.calc_dependencies.find_all({
            "object_type": "MEASURE",
            "table": self.table().name,
            "object": self.name,
        })
        parent_keys = {
            (m.referenced_table, m.referenced_object)
            for m in dependent_measures
            if m.referenced_object_type in {"CALC_COLUMN", "COLUMN"}
        }
        full_dependencies = [c for c in self._tabular_model.columns if (c.table().name, c.explicit_name) in parent_keys]

        if recursive:
            recursive_dependencies: set[Column] = set()
            for dep in full_dependencies:
                if f"[{dep.explicit_name}]" in str(self.expression):
                    recursive_dependencies.add(dep)
                    recursive_dependencies.update(dep.parent_columns(recursive=True))
            return recursive_dependencies

        return {x for x in full_dependencies if f"[{x.explicit_name}]" in str(self.expression)}

    def parents(self, *, recursive: bool = False) -> "set[Column | Measure]":
        """Returns all columns and measures this Measure is dependent on."""
        full_dependencies = self.parent_columns() | self.parent_measures()
        if recursive:
            recursive_dependencies: set[Column | Measure] = set()
            for dep in full_dependencies:
                recursive_dependencies.add(dep)
                recursive_dependencies.update(dep.parents(recursive=True))
            return recursive_dependencies

        return full_dependencies

    def children(self, *, recursive: bool = False) -> "set[Column | Measure]":
        """Returns all columns and measures dependent on this Measure."""
        full_dependencies = self.child_columns() | self.child_measures()
        if recursive:
            recursive_dependencies: set[Column | Measure] = set()
            for dep in full_dependencies:
                recursive_dependencies.add(dep)
                recursive_dependencies.update(dep.children(recursive=True))
            return recursive_dependencies

        return full_dependencies

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(
                self,
                lineage_type,
                [c.get_lineage(lineage_type) for c in self.child_measures() | self.child_columns()],
            )
        parent_nodes: list[SsasTable | None] = [
            self.KPI(),
            self.table(),
            *self.parent_measures(),
            *self.parent_columns(),
        ]
        parent_lineage = [c.get_lineage(lineage_type) for c in parent_nodes if c is not None]
        return LineageNode(self, lineage_type, parent_lineage)

    @staticmethod
    def new(
        name: str,
        expression: str,
        table: "int | Table",
        ssas: "BaseTabularModel",
    ) -> "Measure":
        table_id = table if isinstance(table, int) else table.id

        return Measure(
            name=name,
            data_type=DataType.UNKNOWN,
            is_simple_measure=True,
            state=DataState.READY,
            modified_time=datetime.datetime.now(tz=datetime.UTC),
            structure_modified_time=datetime.datetime.now(tz=datetime.UTC),
            expression=expression,
            table_id=table_id,
            _tabular_model=ssas,
            id=-1,
        )
