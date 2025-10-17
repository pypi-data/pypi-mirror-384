from typing import TYPE_CHECKING

from pbi_core.ssas.model_tables.partition.enums import PartitionType

if TYPE_CHECKING:
    from .column import Column


def update_column_references(dax_expr: str, old_name: str, new_name: str) -> str | None:
    from pbi_parsers import dax  # noqa: PLC0415

    ast = dax.to_ast(dax_expr)
    if ast is None:
        return None

    ast_nodes = ast.find_all((dax.exprs.ColumnExpression, dax.exprs.HierarchyExpression))
    # this will eventually be a function to handle escaping properly
    dax_new_name = f"[{new_name}]"
    for node in ast_nodes:
        if dax.utils.get_inner_text(node.column) == old_name:
            node.column = dax.Token.from_str(dax_new_name)
    return dax.Formatter(ast).format()


def fix_dax(column: "Column", new_name: str) -> None:
    """Fix DAX expressions for a table rename.

    Args:
        column (Column): The column being renamed.
        new_name (str): The new name for the column.

    """
    if column.explicit_name is None:
        return
    for p in column._tabular_model.partitions.find_all({"type": PartitionType.CALCULATED}):
        p.query_definition = (
            update_column_references(p.query_definition, column.explicit_name, new_name) or p.query_definition
        )
    for m in column._tabular_model.measures:
        if isinstance(m.expression, str):
            m.expression = update_column_references(m.expression, column.explicit_name, new_name) or m.expression
        if f := m.format_string_definition():
            f.expression = update_column_references(f.expression, column.explicit_name, new_name) or f.expression
    for c in column._tabular_model.columns:
        if isinstance(c.expression, str):
            c.expression = update_column_references(c.expression, column.explicit_name, new_name) or c.expression
    for tp in column._tabular_model.table_permissions:
        if tp.filter_expression:
            tp.filter_expression = (
                update_column_references(tp.filter_expression, column.explicit_name, new_name) or tp.filter_expression
            )
