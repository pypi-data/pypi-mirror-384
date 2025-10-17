import pathlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import backoff
import pbi_pyadomd
import psutil
from bs4 import BeautifulSoup

from pbi_core.logging import get_logger
from pbi_core.ssas.setup import get_startup_config

from ._physical_local_server import SSASProcess
from .tabular_model import BaseTabularModel, LocalTabularModel
from .utils import COMMAND_TEMPLATES, SKU_ERROR, get_msmdsrv_info

logger = get_logger()

if TYPE_CHECKING:
    from _typeshed import StrPath


DT_FORMAT = "%Y-%m-%d_%H-%M-%S"


class BaseServer:
    """Base Server Interface containing the methods used outside of instance lifetime management."""

    host: str
    "A hostname to the background SSAS instance"

    port: int
    "A Port to the background SSAS instance"

    default_db: str | None
    """The default DB to use when executing DAX"""

    def __init__(self, host: str, port: int, default_db: str | None = None) -> None:
        self.host = host
        self.port = port
        self.default_db = default_db

        self.check_ssas_sku()

    def conn_str(self, db_name: str | None = None) -> str:
        """Formats the connection string for connecting to the background SSAS instance."""
        if db_name:
            return f"Provider=MSOLAP;Data Source={self.host}:{self.port};Initial Catalog={db_name};"
        return f"Provider=MSOLAP;Data Source={self.host}:{self.port};"

    def conn(self, db_name: str | None = None) -> pbi_pyadomd.Connection:
        """Returns a pbi_pyadomd connection."""
        return pbi_pyadomd.connect(self.conn_str(db_name))

    def __repr__(self) -> str:
        return f"Server(host={self.host}:{self.port})"

    def query_dax(self, query: str, *, db_name: str | bool | None = True) -> list[dict[str, Any]]:
        """db_name: when bool and == True, uses the DB last loaded by this server instance.

        (almost always the db of the loaded PBI unless you're manually reassigning server instances)
        when None or False, no db is supplied
        when a string, just passed to the client
        """
        if db_name is True:
            db_name = self.default_db
        elif db_name is False:
            db_name = None
        with self.conn(db_name) as conn:
            reader = conn.execute_dax(query)
            return reader.fetch_many()

    def query_xml(self, query: str, db_name: str | None = None) -> BeautifulSoup:
        """Submits an XMLA query to the SSAS instance and returns the result as a BeautifulSoup object.

        The query should be a valid XMLA command.

        Args:
            query (str): The XMLA query to execute.
            db_name (str | None): The name of the database to execute the query against.

        Returns:
            BeautifulSoup: The result of the query parsed as a BeautifulSoup object.

        """
        with self.conn(db_name) as conn:
            return conn.execute_xml(query)

    def tabular_models(self) -> list[BaseTabularModel]:
        """Creates a list of the Tabular models existing in the SSAS server.

        Note:
            Generally tabular models in the local environment correspond 1-1 with a PBIX report open in the Desktop app

        """
        # Query based on https://learn.microsoft.com/en-us/previous-versions/sql/sql-server-2012/ms126314(v=sql.110)
        dbs = self.query_dax(COMMAND_TEMPLATES["list_dbs.xml"].render())
        return [BaseTabularModel(row["CATALOG_NAME"], self) for row in dbs]

    @backoff.on_exception(backoff.expo, ValueError, max_time=10)
    def check_ssas_sku(self) -> None:
        """Checks if the SSAS instance is running the correct SKU version.

        Tests this assumption by running a query that should fail if the SKU under 1400 (image save command).
        Since we could also fail due to the server not being instantiated, we use a backoff decorator
        to retry the command a few times before giving up.

        Raises:
            TypeError: If the SSAS instance is running an incorrect SKU version.
            ValueError: If the SSAS instance is not running or the command fails for another reason.
                This is used to trigger the backoff retry.

        """
        try:
            self.query_xml(
                COMMAND_TEMPLATES["image_save.xml"].render(
                    target_path="---",
                    db_name="---",
                ),  # specifically choosing non-existant values to verify we get at least one error
            )
        except pbi_pyadomd.AdomdErrorResponseException as e:
            error_message = str(e.Message)
            if error_message == SKU_ERROR:
                return
            msg = f"Incorrect SKUVersion. We got the error: {error_message}"
            raise TypeError(msg) from None
        msg = "Got a 'file not loaded' type error. Waiting"
        raise ValueError(msg)

    @staticmethod
    def sanitize_xml(xml_text: str) -> str:
        """Method to XML-encode characters like "&" so that the Adomd connection doesn't mangle the XMLA commands."""
        return xml_text.replace("&", "&amp;")

    @staticmethod
    def remove_invalid_db_name_chars(orig_db_name: str) -> str:
        """Utility function to convert a PBIX report name to an equivalent name for the DB in the SSAS instance.

        Note:
            Raises a warning if the db_name is changed to inform user that the db_name does not match their input

        """
        db_name = orig_db_name.replace("&", " ")[:100]
        db_name = db_name.strip()  # needed to find the correct name, since SSAS does stripping too
        if orig_db_name != db_name:
            logger.warning("db_name changed", original_name=orig_db_name, new_name=db_name)
        return db_name


class LocalServer(BaseServer):
    """A Server running locally on the user's machine.

    This subclass has the ability to load/dump Tabular Models
    to a PBIX file. Also creates a background SSAS instance and workspace to handle processing if none is provided.

    Args:
        kill_on_exit (bool): Indicates if the background SSAS instance handling
            processing should be terminated at the end of the python session

    """

    physical_process: SSASProcess
    """
    A Python class handling the lifetime of the SSAS Instance. Interacts with the SSAS instance only as a process
    """

    def __init__(
        self,
        host: str = "localhost",
        workspace_directory: "StrPath | None" = None,
        pid: int | None = None,
        *,
        kill_on_exit: bool = True,
    ) -> None:
        if pid is not None:
            self.physical_process = SSASProcess(pid=pid, kill_on_exit=kill_on_exit, startup_config=None)
        else:
            startup_config = get_startup_config()
            workspace_directory = workspace_directory or (
                startup_config.workspace_dir / datetime.now(UTC).strftime(DT_FORMAT)
            )
            self.physical_process = SSASProcess(
                workspace_directory=workspace_directory,
                kill_on_exit=kill_on_exit,
                startup_config=startup_config,
            )
        super().__init__(host, self.physical_process._port)

    def load_pbix(self, path: "StrPath", *, db_name: str | None = None) -> LocalTabularModel:
        """Takes a Path to a PBIX report and loads the PBIX Datamodel to the SSAS instance in the SSASProcess.

        Raises:
            FileNotFoundError: when the path to the PBIX file does not exist
            AdomdErrorResponseException: Occurs when the DB already exists

        """
        path = pathlib.Path(path)
        if not path.exists():
            msg = f"The path to the PBIX does not exist: {path.absolute().as_posix()}"
            raise FileNotFoundError(msg)
        if db_name is None:
            db_name = path.stem
        db_name = self.remove_invalid_db_name_chars(db_name)
        load_command = COMMAND_TEMPLATES["image_load.xml"].render(
            db_name=db_name,
            source_path=self.sanitize_xml(path.absolute().as_posix()),
        )
        try:
            self.query_xml(load_command)
        except pbi_pyadomd.AdomdErrorResponseException as e:
            if (
                "user does not have permission to restore the database, or the database already exists and AllowOverwrite is not specified"  # noqa: E501
                in str(e.Message)
            ):
                logger.warning("Removing old version of PBIX data model for new version", db_name=db_name)
                self.query_xml(COMMAND_TEMPLATES["db_delete.xml"].render(db_name=db_name))
                self.query_xml(load_command)
            else:
                raise pbi_pyadomd.AdomdErrorResponseException from e

        self.default_db = db_name  # needed so the DAX queries are pointed to the right DB by defauilt
        logger.info("Tabular Model load complete")
        tab_model = LocalTabularModel(db_name=db_name, server=self, pbix_path=path)
        tab_model.sync_from()
        return tab_model

    def save_pbix(self, path: "StrPath", db_name: str) -> None:
        path = pathlib.Path(path)
        self.query_xml(
            COMMAND_TEMPLATES["image_save.xml"].render(
                db_name=db_name,
                target_path=self.sanitize_xml(path.absolute().as_posix()),
            ),
        )

    def __repr__(self) -> str:
        return f"LocalServer(port={self.port})"


def list_local_servers() -> list[LocalServer]:
    """Returns all active SSAS instances on a computer accessible from the python instance.

    Note:
        The main thing that would block a SSAS instance from being verified by a python
        instance is insufficient permissions

    """
    ret: list[LocalServer] = [
        LocalServer(pid=process.pid, kill_on_exit=False)
        for process in psutil.process_iter()
        if get_msmdsrv_info(process) is not None
    ]
    return ret


def get_or_create_local_server(*, kill_on_exit: bool = True) -> LocalServer:
    """Gets a local server to load the PBIX to.

    Checks the list of active processes on your local machine for a ``msmdsrv.exe`` process with an active port and
    a corresponding workspace folder. If no matching process is found, this function generates a new process.

    Args:
        kill_on_exit (bool, optional): **If** this function creates a new instance of a local SSAS process, this
            argument will control if the process is killed at the end of the Python session.

    """
    candidates: list[LocalServer] = list_local_servers()
    if candidates:
        logger.info("Re-using existing local SSAS instance", port=candidates[0].port)
        return candidates[0]
    return LocalServer(kill_on_exit=kill_on_exit)


def terminate_all_local_servers() -> None:
    """Attempts to terminate all SSAS instances on a computer.

    Useful for cleaning up the environment and avoiding memory leaks
    """
    for server in list_local_servers():
        server.physical_process.terminate()
