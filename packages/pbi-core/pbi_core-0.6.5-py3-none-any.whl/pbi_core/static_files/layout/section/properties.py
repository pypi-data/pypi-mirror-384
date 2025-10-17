from typing import Any

from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.selector import Selector


@define()
class PageInformationProperties(LayoutNode):
    pageInformationName: Any = None
    pageInformationQnaPodEnabled: Any = None
    pageInformationAltName: Any = None
    pageInformationType: Any = None


@define()
class PageInformation(LayoutNode):
    selector: Selector | None = None
    """Defines the scope at which to apply the formatting for this object.
    Can also define rules for matching highlighted values and how multiple definitions for the same property should
    be ordered."""
    properties: PageInformationProperties = field(factory=PageInformationProperties)
    """Describes the properties of the object to apply formatting changes to."""


@define()
class PageSizeProperties(LayoutNode):
    pageSizeTypes: Any = None
    pageSizeWidth: Any = None
    pageSizeHeight: Any = None


@define()
class PageSize(LayoutNode):
    selector: Selector | None = None
    properties: PageSizeProperties = field(factory=PageSizeProperties)


@define()
class BackgroundProperties(LayoutNode):
    color: Any = None
    image: Any = None
    transparency: Any = None


@define()
class Background(LayoutNode):
    selector: Selector | None = None
    properties: BackgroundProperties = field(factory=BackgroundProperties)


@define()
class DisplayAreaProperties(LayoutNode):
    verticalAlignment: Any = None


@define()
class DisplayArea(LayoutNode):
    selector: Selector | None = None
    properties: DisplayAreaProperties = field(factory=DisplayAreaProperties)


@define()
class OutspacePaneProperties(LayoutNode):
    backgroundColor: Any = None
    transparency: Any = None
    foregroundColor: Any = None
    titleSize: Any = None
    searchTextSize: Any = None
    headerSize: Any = None
    fontFamily: Any = None
    border: Any = None
    borderColor: Any = None
    checkboxAndApplyColor: Any = None
    inputBoxColor: Any = None
    width: Any = None


@define()
class OutspacePane(LayoutNode):
    selector: Selector | None = None
    properties: OutspacePaneProperties = field(factory=OutspacePaneProperties)


@define()
class FilterCardProperties(LayoutNode):
    backgroundColor: Any = None
    transparency: Any = None
    border: Any = None
    borderColor: Any = None
    foregroundColor: Any = None
    textSize: Any = None
    fontFamily: Any = None
    inputBoxColor: Any = None


@define()
class FilterCard(LayoutNode):
    selector: Selector | None = None
    properties: FilterCardProperties = field(factory=FilterCardProperties)


@define()
class PageRefreshProperties(LayoutNode):
    show: Any = None
    refreshType: Any = None
    duration: Any = None
    dialogLauncher: Any = None
    measure: Any = None
    checkEvery: Any = None


@define()
class PageRefresh(LayoutNode):
    selector: Selector | None = None
    properties: PageRefreshProperties = field(factory=PageRefreshProperties)


@define()
class PersonalizeVisualProperties(LayoutNode):
    show: Any = None
    perspectiveRef: Any = None
    applyToAllPages: Any = None


@define()
class PersonalizeVisual(LayoutNode):
    selector: Selector | None = None
    properties: PersonalizeVisualProperties = field(factory=PersonalizeVisualProperties)


@define()
class PageFormattingObjects(LayoutNode):
    pageInformation: list[PageInformation] = field(factory=lambda: [PageInformation()])
    pageSize: list[PageSize] = field(factory=lambda: [PageSize()])
    background: list[Background] = field(factory=lambda: [Background()])
    displayArea: list[DisplayArea] = field(factory=lambda: [DisplayArea()])
    outspace: list[Background] = field(factory=lambda: [Background()])  # This is in fact a Background
    outspacePane: list[OutspacePane] = field(factory=lambda: [OutspacePane()])
    filterCard: list[FilterCard] = field(factory=lambda: [FilterCard()])
    pageRefresh: list[PageRefresh] = field(factory=lambda: [PageRefresh()])
    personalizeVisuals: list[PersonalizeVisual] = field(factory=lambda: [PersonalizeVisual()])
