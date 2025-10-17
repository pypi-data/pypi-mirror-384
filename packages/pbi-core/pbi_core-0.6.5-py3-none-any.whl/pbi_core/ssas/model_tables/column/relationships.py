from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.attribute_hierarchy import AttributeHierarchy
    from pbi_core.ssas.model_tables.level import Level
    from pbi_core.ssas.model_tables.relationship.relationship import Relationship
    from pbi_core.ssas.model_tables.table import Table
    from pbi_core.ssas.server.tabular_model import BaseTabularModel

    from .column import Column


class RelationshipMixin:
    id: int
    table_id: int
    attribute_hierarchy_id: int
    sort_by_column_id: int | None
    _tabular_model: "BaseTabularModel"

    def table(self) -> "Table":
        """Returns the table class the column is a part of."""
        return self._tabular_model.tables.find({"id": self.table_id})

    def attribute_hierarchy(self) -> "AttributeHierarchy":
        return self._tabular_model.attribute_hierarchies.find({"id": self.attribute_hierarchy_id})

    def levels(self) -> set["Level"]:
        return self._tabular_model.levels.find_all({"column_id": self.id})

    def sort_by_column(self) -> "Column | None":
        if self.sort_by_column_id is None:
            return None
        return self._tabular_model.columns.find({"id": self.sort_by_column_id})

    def sorting_columns(self) -> set["Column"]:
        """Provides the inverse information of sort_by_column."""
        return self._tabular_model.columns.find_all({"sort_by_column_id": self.id})

    def from_relationships(self) -> set["Relationship"]:
        return self._tabular_model.relationships.find_all({"from_column_id": self.id})

    def to_relationships(self) -> set["Relationship"]:
        return self._tabular_model.relationships.find_all({"to_column_id": self.id})

    def relationships(self) -> set["Relationship"]:
        return self.from_relationships() | self.to_relationships()
