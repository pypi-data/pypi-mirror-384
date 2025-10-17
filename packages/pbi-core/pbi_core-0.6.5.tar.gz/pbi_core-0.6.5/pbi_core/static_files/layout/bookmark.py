from enum import Enum
from typing import TYPE_CHECKING, Any

from attrs import field

from pbi_core.attrs import converter, define

from ._base_node import LayoutNode
from .expansion_state import ExpansionStateLevel, ExpansionStateRoot
from .filters import BookmarkFilter, CachedDisplayNames, Direction, FilterExpressionMetadata, HighlightScope, Orderby
from .selector import Selector
from .sources import Source
from .visuals.base import PropertyDef
from .visuals.properties.base import Expression

if TYPE_CHECKING:
    from .section import Section
    from .visuals.base import BaseVisual


@define()
class BookmarkFilters(LayoutNode):
    byExpr: list[BookmarkFilter] = field(factory=list)
    """Filter containers that will be identified by expression."""
    byType: list[BookmarkFilter] = field(factory=list)
    """Filter containers that will be identified by type."""
    byName: dict[str, BookmarkFilter] = field(factory=dict)
    """Filter containers that will be identified by name."""
    byTransientState: list[BookmarkFilter] = field(factory=list)
    """Filter containers that are transient"""


@define()
class HighlightSelection(LayoutNode):
    dataMap: dict[str, list[HighlightScope]]
    metadata: list[str] | None = None


@define()
class Highlight(LayoutNode):
    selection: list[HighlightSelection]
    filterExpressionMetadata: FilterExpressionMetadata | None = None


class DisplayMode(Enum):
    maximize = "maximize"
    """Visual is shown full screen."""
    spotlight = "spotlight"
    """Visual is spotlighted and other visuals on the page are dimmed."""
    elevation = "elevation"
    """Visual is shown with an elevation."""
    hidden = "hidden"
    """Visual is hidden."""


class DataTableOptions(Enum):
    accessible = "accessible"
    normal = "normal"


@define()
class MaximizedOptions(LayoutNode):
    dataTable: DataTableOptions


@define()
class Display(LayoutNode):
    mode: DisplayMode
    maximizedOptions: MaximizedOptions | None = None


@define()
class Remove(LayoutNode):
    object: str
    property: str
    selector: Selector | None = None


@define()
class BookmarkPartialVisualObject(LayoutNode):
    merge: dict[str, list[PropertyDef]] | None = None
    remove: list[Remove] | None = None


# TODO: merge with ExpansionState in expansion_state
@define()
class BookmarkExpansionState(LayoutNode):
    roles: list[str]
    levels: list[ExpansionStateLevel]
    root: ExpansionStateRoot


@define()
class Parameter(LayoutNode):
    expr: Source
    """Parameter expression."""
    index: int
    """Index from which parameter starts in the visual projection."""
    length: int
    """Number of fields created by the parameter."""
    sortDirection: Direction | None = None
    """If the sort direction is set, the visual is sorted by this field parameter.
    The implication of a visual being sorted by a field parameter is as follows during parameter resolution:
    - If none of the newly projected fields exist in the sort list, apply the parameter sort direction to the first
        projected field and add it to the end of the sort list.
    - If all the projected fields in the sort list have the opposite sort direction as the parameter's sort direction,
        flip the parameter's sort direction."""


@define()
class BookmarkPartialVisual(LayoutNode):
    visualType: str
    """Name of visual"""
    autoSelectVisualType: bool = False
    """Can the visual type change as data changes in the bookmark."""
    objects: BookmarkPartialVisualObject
    """Changes to formatting to apply in this bookmark."""
    orderBy: list[Orderby] | None = None
    """Updated ordering of data."""
    activeProjections: dict[str, list[Source]] | None = None
    """Updated projections that are used by the visual."""
    display: Display | None = None
    """Optional changes to how the visual is displayed."""
    expansionStates: list[BookmarkExpansionState] | None = None
    """Changes to expansion state."""
    targetType: str | None = None
    """Change visual to this type - if different from the original state. Used by personalize this visual on the web."""
    targetAutoSelectVisualType: bool = False
    """Change auto changing visual type."""
    projections: dict[str, list[Source]] | None = None
    """Projections are stored only when presentation changes are applied (such as during personalize visuals)
    or if the projections are resolved projections of a field parameter. When projections are resolved
    projections of a field parameter but presentation changes are not applied, nulls will be present in the
    array to indicate where non-parameter projections of the visual are."""
    parameters: dict[str, list[Parameter]] | None = None
    """Field parameters that were used as part of the query. We always capture parameter state when parameters
    are present regardless of the bookmark type."""
    cachedFilterDisplayItems: list[CachedDisplayNames] | None = None
    isDrillDisabled: bool = False
    """Indicates whether the drill feature is disabled"""


@define()
class BookmarkVisual(LayoutNode):
    filters: BookmarkFilters | None = None
    """State of filters for this visual when the bookmark was captured."""
    singleVisual: BookmarkPartialVisual
    """State of the configuration of the visual."""
    highlight: Highlight | None = None
    """"Cross-highlights captured in the bookmark."""


@define()
class VisualContainerGroup(LayoutNode):
    isHidden: bool = False
    children: dict[str, "VisualContainerGroup"] | None = None


@define()
class BookmarkSection(LayoutNode):
    visualContainers: dict[str, BookmarkVisual]
    """Flat list of visual-container-specific state.
    Does not include state of groups."""
    filters: BookmarkFilters | None = None
    """State of filters for this page when the bookmark was captured."""
    visualContainerGroups: dict[str, VisualContainerGroup] | None = None
    """Flat list of group-specific state.\nDoes not include state of visual containers."""


@define()
class OutspacePaneProperties(LayoutNode):
    expanded: Expression | None = None
    visible: Expression | None = None


@define()
class OutspacePane(LayoutNode):
    properties: OutspacePaneProperties


@define()
class MergeProperties(LayoutNode):
    outspacePane: list[OutspacePane]


@define()
class ExplorationStateProperties(LayoutNode):
    merge: MergeProperties | None = None


@define()
class ExplorationState(LayoutNode):
    version: str
    """Version of bookmark."""
    sections: dict[str, BookmarkSection]
    """State of all pages when the bookmark was captured."""
    activeSection: str
    """Name of the page that was active when this bookmark was captured."""
    filters: BookmarkFilters | None = None
    """State of filters for the report when the bookmark was captured."""
    objects: ExplorationStateProperties | None = None
    """Changes to formatting to apply in this bookmark."""
    dataSourceVariables: str | None = None
    """A string containing the state of any variables from the underlying direct query data source that should be
    overridden when rendering this content.
    Data source variables do not supply values for M parameters in the semantic model. Instead, data source variables
    are applied when accessing the underlying direct query source."""


@define()
class BookmarkOptions(LayoutNode):
    applyOnlyToTargetVisuals: bool = False
    """Only applies changes to selected visuals when the bookmark was captured."""
    targetVisualNames: list[str] | None = None
    """Specific visuals to which this bookmark applies."""
    suppressActiveSection: bool = False
    """Don't apply changes to active section."""
    suppressData: bool = False
    """Don't apply data changes."""
    suppressDisplay: bool = False
    """Don't apply display property changes."""


@define()
class Bookmark(LayoutNode):
    """Defines a bookmark that captures the state of a report.

    Based on schema/bookmark.json
    """

    options: BookmarkOptions | None
    """Additional options for the bookmark."""
    explorationState: ExplorationState
    """Bookmark definition to use when applying this bookmark."""
    name: str
    """Unique identifier for the bookmark - unique across the report."""
    displayName: str
    """Display name for the bookmark."""

    def match_current_filters(self) -> None:
        raise NotImplementedError

    @staticmethod
    def new(  # noqa: PLR0913
        section: "Section",
        selected_visuals: list["BaseVisual"],
        bookmark_name: str,
        *,
        include_data: bool = True,
        include_display: bool = True,
        include_current_page: bool = True,
    ) -> "Bookmark":
        raise NotImplementedError


@define()
class BookmarkFolder(LayoutNode):
    displayName: str
    name: str  # acts as an ID
    children: list[Bookmark]


LayoutBookmarkChild = Bookmark | BookmarkFolder


@converter.register_structure_hook
def get_bookmark_type(v: dict[str, Any], _: type | None = None) -> LayoutBookmarkChild:
    if "explorationState" in v:
        return Bookmark.model_validate(v)
    return BookmarkFolder.model_validate(v)


@converter.register_unstructure_hook
def unparse_bookmark_type(v: LayoutBookmarkChild) -> dict[str, Any]:
    return converter.unstructure(v)
