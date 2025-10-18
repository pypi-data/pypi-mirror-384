from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Shape:
    start: str
    end: str


class NodeShape(Enum):
    normal = Shape("[", "]")
    round_edge = Shape("(", ")")
    stadium_shape = Shape("([", "])")
    subroutine_shape = Shape("[[", "]]")
    cylindrical = Shape("[(", ")]")
    circle = Shape("((", "))")
    label_shape = Shape(">", "]")
    rhombus = Shape("{", "}")
    hexagon = Shape("{{", "}}")
    parallelogram = Shape("[/", "/]")
    parallelogram_alt = Shape("[\\", "\\]")
    trapezoid = Shape("[/", "\\]")
    trapezoid_alt = Shape("[\\", "/]")
    double_circle = Shape("(((", ")))")


@dataclass(order=True)
class Node:
    id: str
    shape: NodeShape = field(default=NodeShape.normal, compare=False, hash=False)
    content: str = field(default="", compare=False, hash=False)
    style: dict[str, str] = field(default_factory=dict, compare=False, hash=False)
    classes: list[str] = field(default_factory=list, compare=False, hash=False)

    def escape_content(self) -> None:
        self.content = f'"{self.content}"'

    def to_markdown(self) -> str:
        ret = f"{self.id}{self.shape.value.start}{self.content or self.id}{self.shape.value.end}"
        if self.style:
            style = ",".join(f"{k}:{v}" for k, v in self.style.items())
            ret += f"\nstyle {self.id} {style}"
        for cls_name in self.classes:
            ret += f"\nclass {self.id} {cls_name}"
        return ret + "\n"

    def __repr__(self) -> str:
        return f"Node({self.id})"


@dataclass(order=True)
class NodeClass:
    name: str
    style: dict[str, str] = field(default_factory=dict, compare=False, hash=False)

    def legend_style_text(self) -> str:
        # Generate the style text for the legend
        css_name_mapper = {
            "fill": "background-color",
            "stroke": "border-color",
            "stroke-width": "border-width",
        }
        html_style = {**self.style}
        if "stroke" in html_style:
            html_style["border-style"] = "solid"
        return "; ".join(f"{css_name_mapper.get(key, key)}: {value}" for key, value in html_style.items())

    def style_text(self) -> str:
        # Generate the style text for the legend
        return ", ".join(f"{key}:{value}" for key, value in self.style.items())

    def to_markdown(self) -> str:
        # The ":" cannot have a space after it or it doesn't parse
        return f"classDef {self.name} {self.style_text()};"
