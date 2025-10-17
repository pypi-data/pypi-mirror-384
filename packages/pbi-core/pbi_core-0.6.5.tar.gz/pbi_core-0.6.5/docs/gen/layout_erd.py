from pathlib import Path
from typing import TYPE_CHECKING

from pbi_core.attrs import BaseValidation, fields
from pbi_core.static_files.layout import Layout

if TYPE_CHECKING:
    from pbi_mermaid import Link, Node

BASE_PATH = Path(__file__).parents[1] / "docs" / "layout" / "erd"
BASE_PATH.mkdir(parents=True, exist_ok=True)


def unwrap(t: type) -> list[type]:
    if hasattr(t, "__args__"):
        return [t2_ for t_ in t.__args__ for t2_ in unwrap(t_)]
    return [t]


BREAK_NODE_CLASSES = [
    "MeasureSource",
    "LiteralSource",
    "DateSpan",  # after LiteralSource
    "LiteralExpression",
    "HierarchyLevelSource",
    "ColumnSource",
    "AggregationSource",
    "ArithmeticSource",
    "GroupSource",
    "ScopedEvalAgg",
    "ScopedEvalArith",
    "AndCondition",
    "ComparisonCondition",
    "ContainsCondition",
    "ExistsCondition",
    "NotCondition",
    "InCondition",
    "OrCondition",
    "Condition",
    "ConditionalSource",
    "FillRule",
    "SolidExpression",
    "AlgorithmExpression",
    "AggregationExpression",
    "ColumnExpression",
    "ResourcePackageAccess",
    "ImageExpression",
    "SolidColorExpression",
    "MeasureExpression",
    "GeoJsonExpression",
    "LinearGradient2Expression",
    "LinearGradient3Expression",
    "ImageKindExpression",
    "SelectRefExpression",
    "Scope",
    "TransformMeta",
    "PrototypeQuery",
    "FilterProperties",
    "Filter",
    "Selector",
    "VCProperties",
    "ActionButton",
    "BarChart",
    "BasicShape",
    "Card",
    "ClusteredColumnChart",
    "ColumnChart",
    "ColumnProperty",
    "DonutChart",
    "Funnel",
    "Image",
    "LineChart",
    "LineStackedColumnComboChart",
    "PieChart",
    "ScatterChart",
    "Slicer",
    "TableChart",
    "Paragraph",
    "TextBox",
    "PropertyDef",
    "Query",
    "VisualFilter",
    "VisualConfig",
    "ExpansionState",
    "QueryMetadata",
    "VisualContainer",
    "ExplorationStateProperties",
    "BookmarkFilter",
    "BookmarkVisual",
    "Bookmark",
    "LayoutConfig",
    "ResourcePackage",
    "GlobalFilter",
    "Section",
    "Pod",
]


class ERD:
    visited_nodes: set["Node"] = set()

    def helper(self, m: type[BaseValidation]) -> tuple["Node", set["Node"], set["Link"]]:
        from pbi_mermaid import Link, Node  # noqa: PLC0415

        if m.__name__ in BREAK_NODE_CLASSES:
            content = f"<a href='/layout/erd/{m.__name__}'>{m.__name__}</a>"
        else:
            content = m.__name__
        head = Node(id=m.__name__, content=content)
        nodes: set[Node] = {head}
        links: set[Link] = set()

        if head in self.visited_nodes:
            return head, nodes, links
        self.visited_nodes.add(head)

        for attr in fields(m):
            if attr.type is None:
                continue
            for child in unwrap(attr.type):
                if issubclass(child, BaseValidation):
                    sub_head, sub_nodes, sub_links = self.helper(child)
                    nodes.update(sub_nodes)
                    links.update(sub_links)
                    links.add(Link(head, sub_head, link_text=attr.name))

        return head, nodes, links

    @staticmethod
    def _get_node(nodes: set["Node"], name: str) -> "Node":
        ret = [n for n in nodes if n.id == name]
        if len(ret) != 1:
            msg = f"Node with id '{name}' not found in nodes. Found {len(ret)} matches."
            raise ValueError(msg)
        return ret[0]

    def process(self) -> None:
        from pbi_mermaid import MermaidDiagram  # noqa: PLC0415

        self.visited_nodes.clear()
        _head, nodes, links = self.helper(Layout)
        diagram = MermaidDiagram(list(nodes), list(links), title="ERD for Layout")

        break_nodes = [self._get_node(nodes, name) for name in BREAK_NODE_CLASSES]

        diagrams = diagram.chunk(break_nodes)
        for ret_diagram in diagrams:
            with (BASE_PATH / f"{ret_diagram.title}.md").open("w", encoding="utf-8") as f:
                f.write("```mermaid\n")
                f.write(ret_diagram.to_markdown())
                f.write("\n```")


if __name__ == "__main__":
    ERD().process()
