from typing import Any, Literal
from uuid import UUID

from pbi_core.attrs import BaseValidation, converter, define

base_val = bool | int | str


@define()
class Position(BaseValidation):
    x: int | float
    y: int | float


@define()
class Size(BaseValidation):
    height: int | float
    width: int | float


@define()
class Node100(BaseValidation):
    top: float
    left: float
    width: float
    height: float
    layedOut: bool
    nodeIndex: str


@define()
class Node110(BaseValidation):
    location: Position
    nodeIndex: str
    nodeLineageTag: UUID | None = None
    size: Size
    zIndex: int


@define()
class BoundingBoxPosition(BaseValidation):
    x: float
    y: float


@define()
class TableLayout(BaseValidation):
    boundingBoxHeight: float
    boundingBoxWidth: float
    boundingBoxPosition: BoundingBoxPosition
    nodes: list[Node100]


@define()
class DiagramV100(BaseValidation):
    name: str
    zoomValue: float
    isDefault: bool
    tables: list[str]
    layout: TableLayout


@define()
class DiagramV110(BaseValidation):
    ordinal: int
    scrollPosition: Position
    nodes: list[Node110]
    name: str
    zoomValue: float
    pinKeyFieldsToTop: bool
    showExtraHeaderInfo: bool
    hideKeyFieldsWhenCollapsed: bool
    tablesLocked: bool = False


@define()
class DiagramLayoutV100(BaseValidation):
    version: Literal["1.0.0"]
    diagrams: list[DiagramV100]
    selectedDiagram: str | None = None
    defaultDiagram: str | None = None
    showIntroduceNewModelViewDialog: bool = True


@define()
class DiagramLayoutV110(BaseValidation):
    version: Literal["1.1.0"]
    diagrams: list[DiagramV110]
    selectedDiagram: str | None = None
    defaultDiagram: str | None = None


DiagramLayout = DiagramLayoutV100 | DiagramLayoutV110


@converter.register_structure_hook
def parse_diagram_layout(v: dict[str, Any], _: type | None = None) -> DiagramLayout:
    if v["version"] == "1.0.0":
        return DiagramLayoutV100.model_validate(v)
    if v["version"] == "1.1.0":
        return DiagramLayoutV110.model_validate(v)
    msg = f"Unknown Version: {v['version']}"
    raise ValueError(msg)


@converter.register_unstructure_hook
def unparse_diagram_layout(v: DiagramLayout) -> dict[str, Any]:
    return converter.unstructure(v)
