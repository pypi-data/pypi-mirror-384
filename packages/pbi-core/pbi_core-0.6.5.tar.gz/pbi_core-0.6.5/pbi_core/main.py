from .logging import get_logger
from .ssas.model_tables import Column, Measure
from .static_files.model_references import ModelColumnReference, ModelMeasureReference

logger = get_logger()


def column_finder(c: Column, reference: ModelColumnReference) -> bool:
    match = c.explicit_name == reference.column and c.table().name == reference.table
    logger.debug(
        "column_finder",
        column=c.explicit_name,
        table=c.table().name,
        reference_table=reference.table,
        reference_column=reference.column,
        match=match,
    )
    return match


def measure_finder(m: Measure, reference: ModelMeasureReference) -> bool:
    match = m.name == reference.measure and m.table().name == reference.table
    logger.debug(
        "measure_finder",
        measure=m.name,
        table=m.table().name,
        reference_table=reference.table,
        reference_measure=reference.measure,
        match=match,
    )
    return match
