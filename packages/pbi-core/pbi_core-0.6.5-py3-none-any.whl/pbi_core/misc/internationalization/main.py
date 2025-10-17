from pbi_core.logging import get_logger
from pbi_core.report.base.main import BaseReport
from pbi_core.ssas.model_tables.column.column import Column
from pbi_core.ssas.model_tables.enums import DataType
from pbi_core.ssas.model_tables.measure.measure import Measure
from pbi_core.ssas.model_tables.table.table import Table
from pbi_core.ssas.server.tabular_model.tabular_model import BaseTabularModel

from .get_static_elements import get_static_elements
from .text_elements import TextElement, TextElements

logger = get_logger()


def get_measure_ssas_elements(measures: list[Measure]) -> list[TextElement]:
    text_elements = []
    for m in measures:
        text_elements.append(
            TextElement(
                category="Measure",
                source="ssas",
                xpath=["measures", m.id],
                field="name",
                text=m.name,
            ),
        )
        if m.data_type == DataType.STRING and isinstance(m.expression, str):
            text_elements.append(
                TextElement(
                    category="Measure",
                    source="ssas",
                    xpath=["measures", m.id],
                    field="expression",
                    text=m.expression,
                ),
            )
        if isinstance(m.format_string, str):
            text_elements.append(
                TextElement(
                    category="Measure",
                    source="ssas",
                    xpath=["measures", m.id],
                    field="format_string",
                    text=m.format_string,
                ),
            )
        if isinstance(m.description, str):
            text_elements.append(
                TextElement(
                    category="Measure",
                    source="ssas",
                    xpath=["measures", m.id],
                    field="description",
                    text=m.description,
                ),
            )
    return text_elements


def get_column_ssas_elements(columns: list[Column]) -> list[TextElement]:
    text_elements = []
    for c in columns:
        if (
            c.is_key or c.table().is_private or c.table().show_as_variations_only
        ):  # these are secret row-number columns, so we don't want to mess with them.
            # The private tables are system tables that we shouldn't be changing either.
            # The variations-only tables are for auto date tables, which we also shouldn't change.
            continue
        if isinstance(c.explicit_name, str):
            text_elements.append(
                TextElement(
                    category="Column",
                    source="ssas",
                    xpath=["columns", c.id],
                    field="explicit_name",
                    text=c.explicit_name,
                ),
            )
        if isinstance(c.description, str):
            text_elements.append(
                TextElement(
                    category="Column",
                    source="ssas",
                    xpath=["columns", c.id],
                    field="description",
                    text=c.description,
                ),
            )
        if isinstance(c.expression, str):
            text_elements.append(
                TextElement(
                    category="Column",
                    source="ssas",
                    xpath=["columns", c.id],
                    field="expression",
                    text=c.expression,
                ),
            )
    return text_elements


def get_hierarchy_ssas_elements(hierarchies: list) -> list[TextElement]:
    text_elements = []
    for h in hierarchies:
        text_elements.append(
            TextElement(
                category="Hierarchy",
                source="ssas",
                xpath=["hierarchies", h.id],
                field="name",
                text=h.name,
            ),
        )
        if isinstance(h.description, str):
            text_elements.append(
                TextElement(
                    category="Hierarchy",
                    source="ssas",
                    xpath=["hierarchies", h.id],
                    field="description",
                    text=h.description,
                ),
            )
    return text_elements


def get_table_ssas_elements(tables: list[Table]) -> list[TextElement]:
    text_elements = []
    for t in tables:
        if t.is_private or t.show_as_variations_only:
            continue
        if isinstance(t.description, str):
            text_elements.append(
                TextElement(
                    category="Table",
                    source="ssas",
                    xpath=["tables", t.id],
                    field="description",
                    text=t.description,
                ),
            )
        text_elements.append(
            TextElement(
                category="Table",
                source="ssas",
                xpath=["tables", t.id],
                field="name",
                text=t.name,
            ),
        )
    return text_elements


def get_ssas_elements(server: BaseTabularModel) -> TextElements:
    text_elements = [
        *get_measure_ssas_elements(server.measures),
        *get_column_ssas_elements(server.columns),
        *get_hierarchy_ssas_elements(server.hierarchies),
        *get_table_ssas_elements(server.tables),
    ]

    return TextElements(text_elements=text_elements)


def get_source_text_elements(report: BaseReport) -> TextElements:
    static_elements = get_static_elements(report.static_files.layout)
    ssas_elements = get_ssas_elements(report.ssas)
    return TextElements(text_elements=static_elements.text_elements + ssas_elements.text_elements)
