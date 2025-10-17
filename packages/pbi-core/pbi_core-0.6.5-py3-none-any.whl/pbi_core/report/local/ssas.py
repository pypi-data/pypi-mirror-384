from typing import TYPE_CHECKING

from pbi_core.logging import get_logger
from pbi_core.report.base import BaseSsasReport
from pbi_core.ssas.server import LocalTabularModel, get_or_create_local_server

logger = get_logger()

if TYPE_CHECKING:
    from _typeshed import StrPath


class LocalSsasReport(BaseSsasReport):
    """An instance of the SSAS-based components in a PowerBI report from a local PBIX file.

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
    ssas: LocalTabularModel  # pyright: ignore[reportIncompatibleVariableOverride]
    """An instance of a local SSAS Server"""

    @staticmethod
    def load_pbix(path: "StrPath", *, kill_ssas_on_exit: bool = True) -> "LocalSsasReport":
        """Creates a ``LocalReport`` instance from a PBIX file.

        Args:
                path (StrPath): The absolute or local path to the PBIX report
                kill_ssas_on_exit (bool, optional): The LocalReport object depends on a ``msmdsrv.exe`` process that is
                    independent of the Python session process. If this function creates a new ``msmdsrv.exe`` instance
                    and kill_ssas_on_exit is true, the process will be killed on exit.

        Examples:
            ```python

               from pbi_core import LocalReport

               report = LocalReport.load_pbix("example.pbix")
            ```

        Returns:
                LocalReport: the local PBIX class

        """
        logger.info("Loading PBIX SSAS", path=path)
        server = get_or_create_local_server(kill_on_exit=kill_ssas_on_exit)
        ssas = server.load_pbix(path)
        return LocalSsasReport(ssas=ssas, source_path=path)

    def save_pbix(self, path: "StrPath", *, sync_ssas_changes: bool = True) -> None:
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
        if sync_ssas_changes:
            self.ssas.sync_to()
        self.ssas.save_pbix(path)
