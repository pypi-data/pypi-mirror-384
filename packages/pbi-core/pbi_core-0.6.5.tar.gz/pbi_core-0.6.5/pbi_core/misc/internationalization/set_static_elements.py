import json
from pathlib import Path
from typing import TYPE_CHECKING

import openpyxl

from pbi_core import LocalReport

from .text_elements import TextElement

if TYPE_CHECKING:
    from _typeshed import StrPath


def set_static_elements(translation_path: "StrPath", pbix_path: "StrPath") -> None:
    """We parse an excel file containing translations and create a pbix file for each language.

    The excel file must have the following structure:
    - Each worksheet represents a category (e.g., "Section", "Visual", etc.)
    - The first row contains the headers: "xpath", "field", "default", and then one column for each language
        (e.g., "en", "fr", "de").
    """
    wb = openpyxl.load_workbook(translation_path)
    languages: list[str] = [str(x) for x in next(iter(wb.worksheets[0].values))[3:]]
    processing: dict[str, list[TextElement]] = {}
    for ws in wb.worksheets:
        for row in list(ws.values)[1:]:
            for i, language in enumerate(languages):
                processing.setdefault(language, []).append(
                    TextElement(
                        category=ws.title,
                        source="layout",
                        xpath=json.loads(str(row[0])),
                        field=str(row[1]),
                        text=str(row[3 + i]),
                    ),
                )
    for language, static_elements in processing.items():
        pbix = LocalReport.load_pbix(pbix_path)
        for static_element in static_elements:
            node = pbix.static_files.layout.find_xpath(static_element.xpath)
            setattr(node, static_element.field, static_element.text)
        out_path = f"{Path(pbix_path).with_suffix('').absolute().as_posix()}_{language}.pbix"
        pbix.save_pbix(out_path)
