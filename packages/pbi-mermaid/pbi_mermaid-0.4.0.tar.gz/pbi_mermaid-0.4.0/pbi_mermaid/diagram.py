import tempfile
from enum import StrEnum

from .browser import LEGEND_TEMPLATE, MERMAID_TEMPLATE, render_html
from .link import Link
from .misc.chunker import chunker
from .node import Node, NodeClass


class Orientation(StrEnum):
    default = ""
    top_to_bottom = "TB"
    top_down = "TD"
    bottom_to_top = "BT"
    right_to_left = "RL"
    left_to_right = "LR"


class Flowchart:
    title: str = ""
    nodes: list[Node]
    links: list[Link]
    node_classes: list[NodeClass]
    orientation: Orientation

    def __init__(
        self,
        nodes: list[Node],
        links: list[Link],
        node_classes: list[NodeClass] | None = None,
        title: str = "",
        orientation: Orientation = Orientation.default,
    ) -> None:
        self.title = title
        self.nodes = nodes
        self.node_classes = node_classes or []
        self.links = list(
            set(links)
        )  # no longer will duplicate links with the same ID cause duplicate links in the chart
        self.orientation = orientation

    def to_markdown(self) -> str:
        node_text = "\n".join(node.to_markdown() for node in sorted(self.nodes))
        link_text = "\n".join(link.to_markdown() for link in sorted(self.links))
        node_class_text = "\n".join(nclass.to_markdown() for nclass in sorted(self.node_classes))
        header = f"---\ntitle: {self.title}\n---" if self.title else ""
        graph_defines = f"graph {self.orientation}"
        return f"{header}\n{graph_defines}\n{node_text}\n{link_text}\n{node_class_text}"

    def show(self, include_legend: bool = True) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".html", delete=False
        ) as f:  # delete=False needed to let the renderer actually find the file
            if include_legend:
                legend = LEGEND_TEMPLATE.render(node_classes=self.node_classes)
            f.write(
                MERMAID_TEMPLATE.render(mermaid_markdown=self.to_markdown(), legend=legend if include_legend else "")
            )
            render_html(f.name)

    def chunk(self, split_nodes: list["Node"]) -> list["Flowchart"]:
        return chunker(self.nodes, self.links, split_nodes)
