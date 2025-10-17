from pbi_core.attrs import BaseValidation, fields
from pbi_core.logging import get_logger
from pbi_core.static_files import Layout
from pbi_core.static_files.layout.filters import Filter
from pbi_core.static_files.layout.sources.literal import LiteralSource
from pbi_core.static_files.layout.sources.paragraphs import TextRun
from pbi_core.static_files.layout.visuals.base import PropertyDef
from pbi_core.static_files.layout.visuals.properties.base import LiteralExpression
from pbi_core.static_files.layout.visuals.text_box import TextBox

from .text_elements import TextElement, TextElements

logger = get_logger()


def _parse_viz_config(config: BaseValidation | dict | None) -> list[LiteralSource]:
    if config is None:
        return []
    ret: list[LiteralSource] = []
    if isinstance(config, dict):
        for dict_value in config.values():
            for element in dict_value:
                assert isinstance(element, PropertyDef)
                assert isinstance(element.properties, dict)
                ret.extend(
                    field_value.expr
                    for field_value in element.properties.values()
                    if isinstance(field_value, LiteralExpression) and isinstance(field_value.expr.value(), str)
                )
    else:
        for field in fields(config.__class__):
            value: list[BaseValidation] = getattr(config, field.name)
            for element in value:
                properties: BaseValidation = element.properties  # pyright: ignore[reportAttributeAccessIssue]
                for prop in fields(properties.__class__):
                    prop_value = getattr(properties, prop.name)
                    if isinstance(prop_value, LiteralExpression) and isinstance(prop_value.expr.value(), str):
                        ret.append(prop_value.expr)
    return ret


def _get_text_runs(viz: TextBox) -> list[TextRun]:
    ret: list[TextRun] = []
    for property_list in viz.objects.general:
        for paragraph in property_list.properties.paragraphs or []:
            ret.extend(run for run in paragraph.textRuns)
    return ret


def get_static_elements(layout: Layout) -> TextElements:
    """Retrieves all static elements of a report Layout.

    The static elements in the report are:
    1. Section names
    2. Filter names
    3. Visual config names such as title, header, etc.
    """
    elements: list[TextElement] = []

    elements.extend(
        TextElement(
            category="Filter",
            source="layout",
            xpath=f.get_xpath(layout),
            field="displayName",
            text=f.displayName,
        )
        for f in layout.find_all(Filter)
        if f.displayName is not None
    )

    for section in layout.sections:
        elements.append(
            TextElement(
                category="Section",
                source="layout",
                xpath=section.get_xpath(layout),
                field="displayName",
                text=section.displayName,
            ),
        )

        for visual_container in section.visualContainers:
            for visual in visual_container.get_visuals():
                if isinstance(visual, TextBox):
                    text_runs = _get_text_runs(visual)
                    elements.extend(
                        TextElement(
                            category="Visual",
                            source="layout",
                            xpath=run.get_xpath(layout),
                            field="value",
                            text=run.value,
                        )
                        for run in text_runs
                        if isinstance(run.value, str)
                    )
                for config_obj in [visual.vcObjects, visual.objects]:
                    text_config = _parse_viz_config(config_obj)
                    for prop in text_config:
                        val = prop.value()
                        assert isinstance(
                            val,
                            str,
                        )  # technically done before, but the type checker doesn't remember that
                        elements.append(
                            TextElement(
                                category="Visual",
                                source="layout",
                                xpath=prop.get_xpath(layout),
                                field="expr",
                                text=val,
                            ),
                        )

    return TextElements(elements)
