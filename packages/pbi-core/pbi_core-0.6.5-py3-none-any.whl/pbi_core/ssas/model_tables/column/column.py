import datetime
from typing import TYPE_CHECKING, ClassVar, Final
from uuid import UUID, uuid4

from attrs import field, setters
from structlog import BoundLogger

from pbi_core.attrs import define
from pbi_core.logging import get_logger
from pbi_core.ssas.model_tables.base import SsasRenameRecord
from pbi_core.ssas.model_tables.enums import DataState, DataType
from pbi_core.ssas.server._commands import RenameCommands
from pbi_core.ssas.server.utils import SsasCommands
from pbi_core.static_files.layout.filters import Filter
from pbi_core.static_files.layout.sources.base import Entity, Source, SourceRef
from pbi_core.static_files.layout.sources.column import ColumnSource
from pbi_core.static_files.layout.sources.hierarchy import HierarchySource, _PropertyVariationSourceHelper
from pbi_core.static_files.layout.visuals.base import BaseVisual

from . import set_name
from .commands import CommandMixin
from .enums import Alignment, ColumnType, EncodingHint, SummarizedBy

if TYPE_CHECKING:
    from pbi_core.static_files.layout._base_node import LayoutNode
    from pbi_core.static_files.layout.layout import Layout


logger: BoundLogger = get_logger()


@define()
class Column(SsasRenameRecord, CommandMixin):  # pyright: ignore[reportIncompatibleMethodOverride]
    """A column of an SSAS table.

    PowerBI spec: [Power BI](https://learn.microsoft.com/en-us/analysis-services/tabular-models/column-properties-ssas-tabular?view=asallproducts-allversions)

    SSAS spec: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/00a9ec7a-5f4d-4517-8091-b370fe2dc18b)
    """

    # TODO: record the meaning of the various common methods and private attrs
    _field_mapping: ClassVar[dict[str, str]] = {
        "description": "Description",
    }
    _repr_name_field: str = field(default="explicit_name", eq=False)

    alignment: Alignment = field(eq=True)
    attribute_hierarchy_id: int = field(eq=True)
    column_origin_id: int | None = field(eq=True, default=None)
    column_storage_id: int = field(eq=True)
    data_category: str | None = field(eq=True, default=None)
    description: str | None = field(eq=True, default=None)
    display_folder: str | None = field(eq=True, default=None)
    display_ordinal: int = field(eq=True)
    encoding_hint: EncodingHint = field(eq=True)
    error_message: Final[str | None] = field(
        eq=False,
        default=None,
    )  # error message is read-only, so should not be edited
    explicit_data_type: DataType = field(eq=True)
    explicit_name: str | None = field(eq=True, default=None)
    expression: str | int | None = field(eq=True, default=None)
    format_string: int | str | None = field(eq=True, default=None)
    inferred_data_type: int = field(eq=True)
    inferred_name: str | None = field(eq=True, default=None)
    is_available_in_mdx: bool = field(eq=True)
    is_default_image: bool = field(eq=True)
    is_default_label: bool = field(eq=True)
    is_hidden: bool = field(eq=True)
    is_key: bool = field(eq=True)
    is_nullable: bool = field(eq=True)
    is_unique: bool = field(eq=True)
    keep_unique_rows: bool = field(eq=True)
    lineage_tag: UUID = field(factory=uuid4, eq=True, repr=False)
    sort_by_column_id: int | None = field(eq=True, default=None)
    source_column: str | None = field(eq=True, default=None)
    state: Final[DataState] = field(eq=False, default=DataState.READY, on_setattr=setters.frozen)
    summarize_by: SummarizedBy = field(eq=True)
    system_flags: int = field(eq=True)
    table_id: Final[int] = field(eq=True, on_setattr=setters.frozen)  # pyright: ignore[reportIncompatibleVariableOverride]
    table_detail_position: int = field(eq=True)
    type: ColumnType = field(eq=True)

    modified_time: Final[datetime.datetime] = field(eq=False, repr=False)
    refreshed_time: Final[datetime.datetime] = field(eq=False, repr=False)
    structure_modified_time: Final[datetime.datetime] = field(eq=False, repr=False)

    _commands: RenameCommands = field(default=SsasCommands.column, init=False, repr=False)

    def __repr__(self) -> str:
        return f"Column({self.id}: {self.full_name()})"

    def set_name(self, new_name: str, layout: "Layout") -> None:
        """Renames the column and update any dependent expressions to use the new name.

        Since measures are referenced by name in DAX expressions, renaming a measure will break any dependent
        expressions.
        """
        columns = _get_columns_sources(self, layout)
        for c in columns:
            c.Column.Property = new_name
            if c.NativeReferenceName == self.explicit_name:
                c.NativeReferenceName = new_name
        hierarchies = _get_hierarchies_sources(self, layout)
        for h in hierarchies:
            if isinstance(h.Hierarchy.Expression, SourceRef):
                h.Hierarchy.Hierarchy = new_name
            elif isinstance(h.Hierarchy.Expression, _PropertyVariationSourceHelper):
                h.Hierarchy.Expression.PropertyVariationSource.Property = new_name
            else:
                h.Hierarchy.Hierarchy = new_name
        set_name.fix_dax(self, new_name)
        self.explicit_name = new_name


def _get_matching_columns(n: "LayoutNode", entity_mapping: dict[str, str], column: "Column") -> list[ColumnSource]:
    columns = []
    for c in n.find_all(ColumnSource):
        if c.Column.Property != column.explicit_name:
            continue

        if isinstance(c.Column.Expression, SourceRef):
            src = c.Column.Expression.SourceRef
        else:
            src = c.Column.Expression.TransformTableRef

        if isinstance(src, Source):
            if entity_mapping[src.Source] == column.table().name:
                columns.append(c)
        elif src.Entity == column.table().name:
            columns.append(c)

    return columns


def _get_columns_sources(column: "Column", layout: "Layout") -> list[ColumnSource]:
    columns = []
    visuals = layout.find_all(BaseVisual)
    for v in visuals:
        if v.prototypeQuery is None:
            continue
        entity_mapping = {
            e.Name: e.Entity for e in v.prototypeQuery.From if isinstance(e, Entity) and e.Name is not None
        }
        columns.extend(_get_matching_columns(v, entity_mapping, column))

    filters = layout.find_all(Filter)
    for f in filters:
        entity_mapping = {}
        if f.filter is not None:
            entity_mapping = {e.Name: e.Entity for e in f.filter.From if isinstance(e, Entity) and e.Name is not None}
        columns.extend(_get_matching_columns(f, entity_mapping, column))
    return columns


def _get_matching_hierarchies(
    n: "LayoutNode",
    entity_mapping: dict[str, str],
    column: "Column",
) -> list[HierarchySource]:
    hierarchies = []
    if column.explicit_name != "date_Column":
        return []

    for h in n.find_all(HierarchySource):
        if isinstance(h.Hierarchy.Expression, SourceRef):
            table_name = h.Hierarchy.Expression.table(entity_mapping)
            column_name = h.Hierarchy.Hierarchy
        if isinstance(h.Hierarchy.Expression, _PropertyVariationSourceHelper):
            table_name = h.Hierarchy.Expression.PropertyVariationSource.Expression.table(entity_mapping)
            column_name = h.Hierarchy.Expression.PropertyVariationSource.Property
        else:
            table_name = h.Hierarchy.Expression.table(entity_mapping)
            column_name = h.Hierarchy.Hierarchy

        if column_name == column.explicit_name and table_name == column.table().name:
            hierarchies.append(h)
    return hierarchies


def _get_hierarchies_sources(column: "Column", layout: "Layout") -> list[HierarchySource]:
    hierarchies = []
    visuals = layout.find_all(BaseVisual)
    for v in visuals:
        if v.prototypeQuery is None:
            continue
        entity_mapping = {
            e.Name: e.Entity for e in v.prototypeQuery.From if isinstance(e, Entity) and e.Name is not None
        }
        hierarchies.extend(_get_matching_hierarchies(v, entity_mapping, column))

    return hierarchies
