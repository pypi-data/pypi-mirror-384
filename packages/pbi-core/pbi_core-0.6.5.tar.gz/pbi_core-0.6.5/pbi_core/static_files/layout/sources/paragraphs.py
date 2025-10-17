from typing import Any

from pbi_core.attrs import converter, define
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.selector import Selector
from pbi_core.static_files.layout.sources import Source


@define()
class TextStyle(LayoutNode):
    color: str | None = None  # TODO: check that it's hex
    fontSize: str | None = None
    fontFamily: str | None = None
    fontStyle: str | None = None  # italic, etc
    fontWeight: str | None = None  # bold, etc
    textDecoration: str | None = None  # underline, etc


@define()
class CasePattern(LayoutNode):
    expr: Source


@define()
class Case(LayoutNode):
    pattern: CasePattern
    textRuns: list["TextRun"]


@define()
class DefaultCaseTextRun(LayoutNode):
    value: str


@define()
class DefaultCase(LayoutNode):
    textRuns: list[DefaultCaseTextRun]


@define()
class PropertyIdentifier(LayoutNode):
    objectName: str | None = None
    propertyName: str | None = None
    selector: Selector | None = None
    propertyIdentifier: "PropertyIdentifier | None" = None


@define()
class TextRunExpression(LayoutNode):
    propertyIdentifier: PropertyIdentifier
    selector: Selector | None = None


TextRunValue = str | PropertyIdentifier


@converter.register_structure_hook
def get_bookmark_type(v: dict[str, Any], _: type | None = None) -> TextRunValue:
    if isinstance(v, str):
        return converter.structure(v, str)
    if isinstance(v, dict) and "propertyIdentifier" in v:
        return PropertyIdentifier.model_validate(v)
    msg = f"Unknown class: {v.keys()}"
    raise TypeError(msg)


@converter.register_unstructure_hook
def unparse_bookmark_type(v: TextRunValue) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class TextRun(LayoutNode):
    textStyle: TextStyle | None = None
    value: TextRunValue | None = None
    cases: list[Case] | None = None
    defaultCase: DefaultCase | None = None
    url: str | None = None
    expression: TextRunExpression | None = None


@define()
class Paragraph(LayoutNode):
    horizontalTextAlignment: str | None = None  # TODO: convert to enum
    textRuns: list[TextRun]
