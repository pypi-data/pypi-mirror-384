from typing import Any

from attrs import field

from pbi_core.attrs import BaseValidation, define
from pbi_core.attrs.extra import Color

base_val = bool | int | str


@define()
class TextClass(BaseValidation):
    fontSize: int | None = None
    fontFace: str
    color: Color


@define()
class TextClasses(BaseValidation):
    callout: TextClass
    title: TextClass
    header: TextClass
    label: TextClass


@define()
class ColorName(BaseValidation):
    color: Color


@define()
class ColorThemeData(BaseValidation):
    solid: ColorName


@define()
class Theme(BaseValidation):
    """A class mapping the fields of the Theme JSON.

    Documented `here <https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-report-themes#set-theme-colors>`
    """

    name: str | None = None
    type: str | None = None

    dataColors: list[str] = field(factory=list)
    foreground: str | None = None
    foregroundNeutralSecondary: Color | None = None
    foregroundNeutralTertiary: Color | None = None
    background: Color | None = None
    backgroundLight: Color | None = None
    backgroundNeutral: Color | None = None
    tableAccent: Color | None = None
    good: Color | None = None
    neutral: Color | None = None
    bad: Color | None = None
    maximum: Color | None = None
    center: Color | None = None
    minimum: Color | None = None
    null: Color | None = None
    hyperlink: Color | None = None
    visitedHyperlink: Color | None = None

    objects: Any = None
    arcs: list[list[list[int]]] = field(factory=list)
    transform: Any = None

    textClasses: TextClasses | None = None
    visualStyles: dict[str, dict[str, dict[str, list[dict[str, bool | int | str | ColorThemeData]]]]] | None = None
