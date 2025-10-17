from typing import TYPE_CHECKING, Literal

from .enums import Alignment, ColumnType
from .relationships import RelationshipMixin

if TYPE_CHECKING:
    from pbi_parsers import dax


class HelpersMixin(RelationshipMixin):
    alignment: Alignment
    expression: str | int | None
    system_flags: int
    explicit_name: str | None
    id: int
    inferred_name: str | None
    type: ColumnType

    def expression_ast(self) -> "dax.Expression | None":
        from pbi_parsers import dax  # noqa: PLC0415

        if not isinstance(self.expression, str):
            return None
        return dax.to_ast(self.expression)

    def is_system_table(self) -> bool:
        return bool(self.system_flags >> 1 % 2)

    def is_from_calculated_table(self) -> bool:
        return bool(self.system_flags % 2)

    def is_calculated_column(self) -> bool:
        return self.type == ColumnType.CALCULATED

    def is_normal(self) -> bool:
        """Returns True if the column is not a row number column or attached to a system/private table."""
        if self.type == ColumnType.ROW_NUMBER:
            return False
        if self.table().is_private:
            return False
        return not self.is_system_table()

    def pbi_core_name(self) -> str:
        """Returns the name displayed in the PBIX report."""
        if self.explicit_name is not None:
            return self.explicit_name
        if self.inferred_name is not None:
            return self.inferred_name
        return str(self.id)

    def _column_type(self) -> Literal["COLUMN", "CALC_COLUMN"]:
        if self.type == ColumnType.DATA:
            return "COLUMN"
        return "CALC_COLUMN"

    def full_name(self) -> str:
        """Returns the fully qualified name for DAX queries.

        Examples:
            'TableName'[ColumnName]

        """
        table_name = self.table().name
        return f"'{table_name}'[{self.explicit_name}]"

    def data(self, head: int = 100) -> list[int | float | str]:
        table_name = self.table().name
        ret = self._tabular_model.server.query_dax(
            f"EVALUATE TOPN({head}, SELECTCOLUMNS(ALL('{table_name}'), {self.full_name()}))",
            db_name=self._tabular_model.db_name,
        )
        return [next(iter(row.values())) for row in ret]
