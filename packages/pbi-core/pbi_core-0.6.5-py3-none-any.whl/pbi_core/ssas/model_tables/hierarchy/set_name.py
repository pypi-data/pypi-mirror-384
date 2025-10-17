from typing import TYPE_CHECKING

from pbi_core.ssas.model_tables.partition.enums import PartitionType

if TYPE_CHECKING:
    from .hierarchy import Hierarchy


def update_hierarchy_references(dax_expr: str, old_name: str, new_name: str) -> str | None:
    from pbi_parsers import dax  # noqa: PLC0415

    ast = dax.to_ast(dax_expr)
    if ast is None:
        return None

    ast_nodes = ast.find_all(dax.exprs.HierarchyExpression)
    # this will eventually be a function to handle escaping properly
    dax_new_name = f"[{new_name}]"
    for node in ast_nodes:
        if dax.utils.get_inner_text(node.column) == old_name:
            node.column = dax.Token.from_str(dax_new_name)
    return dax.Formatter(ast).format()


def fix_dax(hierarchy: "Hierarchy", new_name: str) -> None:
    """Fix DAX expressions for a hierarchy rename.

    Args:
        hierarchy (Hierarchy): The hierarchy being renamed.
        new_name (str): The new name for the hierarchy.

    """
    for p in hierarchy._tabular_model.partitions.find_all({"type": PartitionType.CALCULATED}):
        new_query = update_hierarchy_references(p.query_definition, hierarchy.name, new_name)
        if new_query is not None and new_query != p.query_definition:
            p.query_definition = new_query
    for m in hierarchy._tabular_model.measures:
        if isinstance(m.expression, str):
            m.expression = update_hierarchy_references(m.expression, hierarchy.name, new_name) or m.expression
        if f := m.format_string_definition():
            f.expression = update_hierarchy_references(f.expression, hierarchy.name, new_name) or f.expression
    for c in hierarchy._tabular_model.columns:
        if isinstance(c.expression, str):
            c.expression = update_hierarchy_references(c.expression, hierarchy.name, new_name) or c.expression
