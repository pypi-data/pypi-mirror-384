from typing import TYPE_CHECKING

from pbi_core.logging import get_logger
from pbi_core.ssas.server import BaseTabularModel

logger = get_logger()

if TYPE_CHECKING:
    from _typeshed import StrPath


class BaseSsasReport:  # noqa: B903
    """An instance of the SSAS-based components in a PowerBI report."""

    _source_path: "StrPath"

    ssas: BaseTabularModel
    """An instance of a local SSAS Server"""

    def __init__(self, ssas: BaseTabularModel, source_path: "StrPath") -> None:
        self.ssas = ssas
        self._source_path = source_path
