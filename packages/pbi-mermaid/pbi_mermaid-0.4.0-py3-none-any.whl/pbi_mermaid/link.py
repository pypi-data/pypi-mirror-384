from dataclasses import dataclass, field
from enum import StrEnum

from .node import Node


class LinkShape(StrEnum):
    normal = "---"
    dotted = "-.-"
    thick = "==="


class LinkHead(StrEnum):
    none = ""
    arrow = ">"
    left_arrow = "<"
    bullet = "o"
    cross = "x"


@dataclass(order=True, unsafe_hash=True)
class Link:
    from_node: Node = field(compare=False, hash=False)
    to_node: Node = field(compare=False, hash=False)
    id: str = field(default="", kw_only=True, hash=True)
    from_head: str = field(default=LinkHead.none, compare=False, hash=False, kw_only=True)
    to_head: str = field(default=LinkHead.arrow, compare=False, hash=False, kw_only=True)
    link_shape: LinkShape = field(default=LinkShape.normal, compare=False, hash=False, kw_only=True)
    link_text: str | None = field(default=None, compare=False, hash=False, kw_only=True)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"{self.from_node.id}-->{self.to_node.id}"

    def to_markdown(self) -> str:
        link_text = f"{self.from_head}{self.link_shape}{self.to_head}"
        if self.link_text:
            link_text += f"|{self.link_text}|"
        return f"{self.from_node.id} {link_text} {self.to_node.id}"

    def __repr__(self) -> str:
        return f"Link(from={self.from_node}, to={self.to_node})"
