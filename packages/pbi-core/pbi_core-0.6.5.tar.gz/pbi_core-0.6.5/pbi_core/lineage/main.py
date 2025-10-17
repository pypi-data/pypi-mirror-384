from typing import TYPE_CHECKING, Any, Literal, Protocol

if TYPE_CHECKING:
    from pbi_mermaid import Link, MermaidDiagram, Node

"""
#ffffcc, #ffcc99, #ffcccc,
#ff99cc, #ffccff, #cc99ff,
#ccccff, #99ccff, #ccffff,
#99ffcc, #ccffcc, #ccff99,
"""

CLASS_STYLES = {
    # SSAS Stuff
    "AttributeHierarchy": {"fill": "#ffffcc", "stroke": "#333", "stroke-width": "1px"},
    "Column": {"fill": "#ffcc99", "stroke": "#333", "stroke-width": "1px"},
    "Culture": {"fill": "#ffcccc", "stroke": "#333", "stroke-width": "1px"},
    "LinguisticMetadata": {"fill": "#ff99cc", "stroke": "#333", "stroke-width": "1px"},
    "Measure": {"fill": "#ffccff", "stroke": "#333", "stroke-width": "1px"},
    "Table": {"fill": "#cc99ff", "stroke": "#333", "stroke-width": "1px"},
    "Partition": {"fill": "#ccccff", "stroke": "#333", "stroke-width": "1px"},
    "Model": {"fill": "#99ccff", "stroke": "#333", "stroke-width": "1px"},
    # Visuals
    "BarChart": {"fill": "#ccffff", "stroke": "#333", "stroke-width": "1px"},
    "VisualContainer": {"fill": "#99ffcc", "stroke": "#333", "stroke-width": "1px"},
    "Section": {"fill": "#ccffcc", "stroke": "#333", "stroke-width": "1px"},
    "Layout": {"fill": "#ccff99", "stroke": "#333", "stroke-width": "1px"},
}


class LineageProtocol(Protocol):
    id: str

    def pbi_core_name(self) -> str:
        """Returns the name displayed in the PBIX report."""
        raise NotImplementedError


class LineageNode:
    """Class used to track DAX dependencies from visuals to measures to PowerQueries."""

    value: Any
    relatives: list["LineageNode"]
    lineage_type: Literal["children", "parents"]

    def __init__(
        self,
        value: Any,
        lineage_type: Literal["children", "parents"],
        relatives: list["LineageNode"] | None = None,
    ) -> None:
        """Initialize."""
        self.value = value
        self.relatives = relatives or []
        self.lineage_type = lineage_type

    @staticmethod
    def _create_node(value: LineageProtocol) -> "Node":
        from pbi_mermaid import Node  # noqa: PLC0415
        from pbi_mermaid.node import NodeShape  # noqa: PLC0415

        return Node(
            id=f"{value.__class__.__name__}-{value.id}",
            content=value.pbi_core_name(),
            style=CLASS_STYLES[value.__class__.__name__],
            shape=NodeShape.round_edge,
        )

    def _to_mermaid_helper(self, node: "Node") -> tuple[list["Node"], list["Link"]]:
        from pbi_mermaid import Link  # noqa: PLC0415

        nodes: list[Node] = [node]
        links: list[Link] = []
        for relative in self.relatives:
            child_node = self._create_node(relative.value)
            child_nodes, child_links = relative._to_mermaid_helper(child_node)
            links.append(Link(nodes[0], child_node))
            links.extend(child_links)
            nodes.extend(child_nodes)
        return nodes, links

    def to_mermaid(self) -> "MermaidDiagram":
        from pbi_mermaid import MermaidDiagram  # noqa: PLC0415

        base_node = self._create_node(self.value)
        nodes, links = self._to_mermaid_helper(base_node)
        return MermaidDiagram(title="Lineage Chart", nodes=nodes, links=links)
