from enum import Enum
from typing import TYPE_CHECKING, Literal

import attrs
from attrs import field

from pbi_core.attrs import Json, define
from pbi_core.attrs.extra import repr_len
from pbi_core.lineage.main import LineageNode
from pbi_core.static_files.model_references import ModelColumnReference, ModelMeasureReference

from ._base_node import LayoutNode
from .bookmark import LayoutBookmarkChild
from .filters import GlobalFilter
from .pod import Pod
from .resource_package import ResourcePackage
from .section import Section
from .visuals.base import FilterSortOrder
from .visuals.properties.base import Expression

if TYPE_CHECKING:
    from pbi_core.ssas.server.tabular_model.tabular_model import BaseTabularModel


class LayoutOptimization(Enum):
    DESKTOP = 0
    MOBILE = 1


@define()
class PublicCustomVisual(LayoutNode):
    pass  # TODO: find an example where this occurs


@define()
class ThemeVersionInfo(LayoutNode):
    visual: str
    page: str
    report: str


class ThemeResourcePackageType(Enum):
    REGISTERED_RESOURCES = 1
    SHARED_RESOURCES = 2


@define()
class ThemeInfo(LayoutNode):
    name: str
    version: ThemeVersionInfo | str
    type: ThemeResourcePackageType  # def an enum


@define()
class ThemeCollection(LayoutNode):
    baseTheme: ThemeInfo | None = None
    customTheme: ThemeInfo | None = None


@define()
class Settings(LayoutNode):
    allowChangeFilterTypes: bool = True
    allowDataPointLassoSelect: bool = False
    exportDataMode: int = 0  # def an enum
    hideVisualContainerHeader: bool = False
    isPersistentUserStateDisabled: bool = False
    useEnhancedTooltips: bool = True
    useNewFilterPaneExperience: bool = True
    useStylableVisualContainerHeader: bool = True
    useCrossReportDrillthrough: bool = False
    defaultFilterActionIsDataFilter: bool = False
    disableFilterPaneSearch: bool = False
    allowInlineExploration: bool = True
    optOutNewFilterPaneExperience: bool = False
    enableDeveloperMode: bool = False
    filterPaneHiddenInEditMode: bool = False
    queryLimitOption: int = 6
    useDefaultAggregateDisplayName: bool = True


@define()
class SlowDataSourceSettings(LayoutNode):
    isCrossHighlightingDisabled: bool
    isFieldWellButtonEnabled: bool
    isFilterSelectionsButtonEnabled: bool
    isSlicerSelectionsButtonEnabled: bool
    isApplyAllButtonEnabled: bool = False


@define()
class OutspacePaneProperties(LayoutNode):
    visible: Expression | None = None
    expanded: Expression | None = None


@define()
class OutspacePane(LayoutNode):
    properties: OutspacePaneProperties


@define()
class ConfigSectionProperties(LayoutNode):
    verticalAlignment: Expression | None = None


@define()
class ConfigSection(LayoutNode):
    properties: ConfigSectionProperties


@define()
class LayoutProperties(LayoutNode):
    outspacePane: list[OutspacePane] | None = None
    section: list[ConfigSection] | None = None


@define()
class LayoutConfig(LayoutNode):
    linguisticSchemaSyncVersion: int | None = None
    defaultDrillFilterOtherVisuals: bool = True
    bookmarks: list[LayoutBookmarkChild] | None = None
    activeSectionIndex: int
    themeCollection: ThemeCollection
    slowDataSourceSettings: SlowDataSourceSettings | None = None
    settings: Settings | None = None
    version: str  # looks like a float, but we keep it str to allow round tripping. Otherwise
    objects: LayoutProperties | None = None
    filterSortOrder: FilterSortOrder = FilterSortOrder.NA


@define()
class Layout(LayoutNode):
    """Represents the layout of a Power BI report, including sections, filters, and other properties."""

    id: int = -3
    reportId: int = -1
    filters: Json[list[GlobalFilter]] = field(factory=list, repr=repr_len)
    resourcePackages: list[ResourcePackage] = field(repr=repr_len)
    sections: list[Section] = field(repr=repr_len)
    config: Json[LayoutConfig] = field(repr=False)
    layoutOptimization: LayoutOptimization = field(repr=False)
    theme: str | None = None
    pods: list[Pod] = field(factory=list, repr=repr_len)
    publicCustomVisuals: list[PublicCustomVisual] = field(factory=list, repr=repr_len)

    def __attrs_post_init__(self) -> None:
        for viz in self.sections:
            viz._layout = self

    def pbi_core_name(self) -> str:  # noqa: PLR6301
        return "Layout"

    def get_ssas_elements(
        self,
        *,
        include_sections: bool = True,
        include_filters: bool = True,
    ) -> set[ModelColumnReference | ModelMeasureReference]:
        """Returns the SSAS elements (columns and measures) this report is directly dependent on."""
        ret: set[ModelColumnReference | ModelMeasureReference] = set()
        if include_filters:
            for f in self.filters:
                ret.update(f.get_ssas_elements())
        if include_sections:
            for s in self.sections:
                ret.update(s.get_ssas_elements())
        return ret

    def get_lineage(
        self,
        lineage_type: Literal["children", "parents"],
        tabular_model: "BaseTabularModel",
    ) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(self, lineage_type)

        entities = self.get_ssas_elements()
        children_nodes = [ref.to_model(tabular_model) for ref in entities]

        children_lineage = [p.get_lineage(lineage_type) for p in children_nodes if p is not None]
        return LineageNode(self, lineage_type, children_lineage)


attrs.resolve_types(Section, {"Layout": Layout})
