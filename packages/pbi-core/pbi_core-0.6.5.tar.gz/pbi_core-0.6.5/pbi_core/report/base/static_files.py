from typing import TYPE_CHECKING

from pbi_core.logging import get_logger
from pbi_core.static_files import StaticFiles

logger = get_logger()

if TYPE_CHECKING:
    from _typeshed import StrPath


class BaseStaticReport:  # noqa: B903
    """An instance of a PowerBI report."""

    """Classes representing the static design portions of the PBIX report"""

    _source_path: "StrPath"
    static_files: StaticFiles
    """Classes representing the static design portions of the PBIX report"""

    def __init__(self, static_files: StaticFiles, source_path: "StrPath") -> None:
        self.static_files = static_files
        self._source_path = source_path
