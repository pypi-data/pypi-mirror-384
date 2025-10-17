import shutil
from typing import TYPE_CHECKING

from pbi_core.logging import get_logger
from pbi_core.report.base import BaseStaticReport
from pbi_core.static_files import StaticFiles

logger = get_logger()

if TYPE_CHECKING:
    from _typeshed import StrPath


class LocalStaticReport(BaseStaticReport):
    """An instance of a PowerBI report from a local PBIX file.

    Args:
        static_files (StaticElements): An instance of all the static files (except DataModel) in the PBIX file

    Examples:
        ```python
        from pbi_core import LocalReport

        report = LocalReport.load_pbix("example.pbix")
        report.save_pbix("example_out.pbix")
        ```

    """

    # Redefining here to add docstring
    _source_path: "StrPath"
    """Since this class doesn't load the full PBIX, we need to keep track of the source path for saving later"""

    @staticmethod
    def load_pbix(path: "StrPath") -> "LocalStaticReport":
        logger.info("Loading PBIX Static Files", path=path)
        static_files = StaticFiles.load_pbix(path)
        return LocalStaticReport(static_files=static_files, source_path=path)

    def save_pbix(self, path: "StrPath") -> None:
        """Creates a new PBIX with the information in this class to the given path.

        Examples:
            ```python

               from pbi_core import LocalReport

               report = LocalReport.load_pbix("example.pbix")
            ```
               report.save_pbix("example_out.pbix")

        Args:
            path (StrPath): the path (relative or absolute) to save the PBIX to
            sync_ssas_changes (bool, optional): whether to sync changes made in the SSAS model back to the PBIX file

        """
        shutil.copy(self._source_path, path)
        self.static_files.save_pbix(path)
