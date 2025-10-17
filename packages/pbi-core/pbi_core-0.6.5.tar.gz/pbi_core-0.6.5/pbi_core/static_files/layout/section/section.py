from typing import TYPE_CHECKING, Literal
from uuid import UUID

import attrs
from attrs import field, validators

from pbi_core.attrs import Json, define
from pbi_core.attrs.extra import repr_len
from pbi_core.lineage.main import LineageNode
from pbi_core.ssas.trace import Performance, get_performance
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.filters import PageFilter
from pbi_core.static_files.layout.visual_container import VisualContainer
from pbi_core.static_files.model_references import ModelColumnReference, ModelMeasureReference

from .config import Annotation, AutoPageGenerationConfig, PageBinding, SectionConfig, VisualInteraction
from .enums import (
    DisplayOption,
    PageHowCreated,
    PageType,
    PageVisibility,
)

if TYPE_CHECKING:
    from pbi_core.ssas.server.tabular_model.tabular_model import BaseTabularModel
    from pbi_core.static_files.layout.layout import Layout


@define(repr=True)
class Section(LayoutNode):
    height: int
    """Height of the page (in pixels) - optional only for 'DeprecatedDynamic' option, required otherwise."""
    width: int
    """Width of the page (in pixels) - optional only for 'DeprecatedDynamic' option, required otherwise."""
    displayOption: DisplayOption
    """Defines how the page is scaled."""
    config: Json[SectionConfig] = field(repr=False)
    objectId: UUID | None = None
    visualContainers: list[VisualContainer] = field(repr=repr_len)
    ordinal: int = 0
    filters: Json[list[PageFilter]] = field(repr=repr_len)
    """Filters that apply to all the visuals on this page - on top of the filters defined for the whole report."""
    displayName: str
    """A user facing name for this page."""
    name: str = field(validator=validators.max_len(50))
    """A unique identifier for the page across the whole report."""
    id: int | None = None
    pageBinding: PageBinding | None = field(repr=False, default=None)
    """Additional metadata defined for how this page is used (tooltip, drillthrough, etc)."""
    """Defines the formatting for different objects on a page."""
    type: PageType | None = None
    """Specific usage of this page (for example drillthrough)."""
    visibility: PageVisibility | None = PageVisibility.ALWAYS_VISIBLE
    """Defines when this page should be visible - by default it is always visible."""
    visualInteractions: list[VisualInteraction] | None = field(repr=repr_len, default=None)
    """Defines how data point selection on a specific visual flow (as filters) to other visuals on the page.
    By default it is up-to the visual to apply it either as a cross-highlight or as a filter."""
    autoPageGenerationConfig: AutoPageGenerationConfig | None = None
    """Configuration that was used to automatically generate a page (for example using 'Auto create the report'
    option)."""
    annotations: list[Annotation] | None = field(repr=repr_len, default=None)
    """Additional information to be saved (for example comments, readme, etc) for this page."""
    howCreated: PageHowCreated | None = None
    """Source of creation of this page."""

    _layout: "Layout | None" = field(init=False, repr=False, eq=False, default=None)

    def __attrs_post_init__(self) -> None:
        for viz in self.visualContainers:
            viz._section = self

    def pbi_core_name(self) -> str:
        return self.name

    def get_ssas_elements(
        self,
        *,
        include_visuals: bool = True,
        include_filters: bool = True,
    ) -> set[ModelColumnReference | ModelMeasureReference]:
        """Returns the SSAS elements (columns and measures) this report page is directly dependent on."""
        ret: set[ModelColumnReference | ModelMeasureReference] = set()
        if include_visuals:
            for viz in self.visualContainers:
                ret.update(viz.get_ssas_elements())
        if include_filters:
            for f in self.filters:
                ret.update(f.get_ssas_elements())
        return ret

    def get_lineage(
        self,
        lineage_type: Literal["children", "parents"],
        tabular_model: "BaseTabularModel",
    ) -> LineageNode:
        if lineage_type == "children":
            return LineageNode(self, lineage_type)

        page_filters = self.get_ssas_elements()

        report_filters = set()
        if self._layout is not None:
            report_filters = self._layout.get_ssas_elements(include_sections=False)

        entities = page_filters | report_filters
        children_nodes = [ref.to_model(tabular_model) for ref in entities]

        children_lineage = [p.get_lineage(lineage_type) for p in children_nodes if p is not None]
        return LineageNode(self, lineage_type, children_lineage)

    def get_performance(self, model: "BaseTabularModel", *, clear_cache: bool = False) -> list[Performance]:
        """Calculates various metrics on the speed of the visual.

        Current Metrics:
            Total Seconds to Query
            Total Rows Retrieved

        Raises:
            ValueError: If the page does not have any querying visuals.

        """
        commands: list[str] = []
        for viz in self.visualContainers:
            if viz.query is not None:
                command = viz._get_data_command()
                if command is not None:
                    commands.append(command.get_dax(model).dax)
        if not commands:
            msg = "Cannot get performance for a page without any querying visuals"
            raise ValueError(msg)
        return get_performance(model, commands, clear_cache=clear_cache)


attrs.resolve_types(VisualContainer, {"Section": Section})
