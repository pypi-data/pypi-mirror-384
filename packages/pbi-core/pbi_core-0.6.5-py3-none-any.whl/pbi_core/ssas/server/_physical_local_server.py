import atexit
import pathlib
import shutil
import subprocess  # nosec. It's necessary to run the msmdsrv exe  # noqa: S404
from functools import cached_property
from typing import TYPE_CHECKING

import backoff
import psutil

from pbi_core.logging import get_logger
from pbi_core.ssas.setup import PbiCoreStartupConfig, get_startup_config

from .utils import get_msmdsrv_info

if TYPE_CHECKING:
    from _typeshed import StrPath
logger = get_logger()
PORT_ACCESS_TRIES = 5


class SSASProcess:
    """Handles the SSAS instance as a OS process.

    Args:
        pid (Optional[int]): The process ID of the SSAS instance. If None, the class will create a new SSAS process
        workspace_directory (StrPath): The path to the workspace corresponding to the pid.
            Should only be included when the pid is not provided.
        kill_on_exit (bool): Specifies whether the SSAS instance should be terminated when the python session exits
            (implemented via atexit lib)

    Examples:
        ```python

           SSASProcess('tmp/workspace')  # generates a new SSAS Process and generates workspace documents at 'tmp/workspace'
           SSASProcess(4321)  # connects to an existing SSAS Process at 4321
           SSASProcess('tmp/workspace', False)  # Generates a new SSAS Process and allows it to run beyond the lifetime of the Python script
        ```

    Raises:
        ValueError: If both or none of ``pid`` and ``workspace_directory`` are specified

    """  # noqa: E501

    _workspace_directory: pathlib.Path
    pid: int = -1
    kill_on_exit: bool
    startup_config: PbiCoreStartupConfig | None

    def __init__(
        self,
        pid: int | None = None,
        workspace_directory: "StrPath | None" = None,
        *,
        kill_on_exit: bool = True,
        startup_config: PbiCoreStartupConfig | None = None,
    ) -> None:
        """__init__ is not intended to be directly called.

        This class is expected to be initialized from the .from_pid or .new_instance methods

        Raises:
            ValueError: when either both or neither of the pid and workspace_directory are specified

        """
        self.kill_on_exit = kill_on_exit
        atexit.register(self._on_exit)

        if pid is None:
            if workspace_directory is None:
                msg = "If the pid is not specified, you must specify a workspace directory"
                raise ValueError(msg)
            self.startup_config = startup_config or get_startup_config()
            self._workspace_directory = pathlib.Path(workspace_directory)
            logger.info(
                "No pid provided. Initializing new SSAS Instance",
                workspace_dir=self._workspace_directory,
                msmdsrv_exe=self.startup_config.msmdsrv_exe,
            )
            self.pid = self._initialize_server()
        else:
            if workspace_directory is not None:
                msg = "If the pid is specified, you must not specify a workspace directory"
                raise ValueError(msg)
            self.startup_config = None
            self.pid = pid
            self._workspace_directory = self._get_workspace_directory()

    def _get_workspace_directory(self) -> pathlib.Path:
        """Gets the workspace of the PBIX DB config.

        Uses the PID and the command used to initialize that PID to identify the
        workspace directory used by the SSAS process

        Raises:
            ValueError: When the PID points to a non-DB process

        """
        proc = psutil.Process(self.pid)
        proc_info = get_msmdsrv_info(proc)
        if proc_info is None:
            msg = "This PID doesn't correspond to a valid SSAS instance"
            raise ValueError(msg)
        return proc_info.workspace_directory.absolute()

    def _create_workspace(self) -> None:
        """Creates the workspace directory and populates the initial config file for the new SSAS instance."""
        assert self.startup_config is not None, "Startup config must be set before creating a workspace"
        logger.debug("initializing SSAS Workspace", directory=self._workspace_directory)
        self._workspace_directory.mkdir(parents=True, exist_ok=True)
        (self._workspace_directory / "msmdsrv.ini").write_text(
            self.startup_config.msmdsrv_ini_template().render(
                data_directory=self._workspace_directory.as_posix().replace("/", "\\"),
                certificate_directory=self.startup_config.cert_dir.absolute().as_posix().replace("/", "\\"),
            ),
        )

    def _run_msmdsrv(self) -> int:
        """Runs the commands to create the DB.

        Commands are explained here: https://stackoverflow.com/q/36458981
        -c: console mode
        -n "instance_name": instance name (the name of the default database)
        -s "workspace_directory": The location of the configuration

        Note:
            ``-s`` points to the workspace created in the method "create_workspace"

        """
        assert self.startup_config is not None, "Startup config must be set before running msmdsrv"
        logger.debug("Running msmdsrv exe")
        command = [  # pbi_core_master is not really used, but a port file isn't generated without it
            self.startup_config.msmdsrv_exe.as_posix(),
            "-c",
            "-n",
            "pbi_core_master",
            "-s",
            self._workspace_directory.as_posix(),
        ]
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        return subprocess.Popen(  # noqa: S603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=flags,
        ).pid  # nosec. It's necessary to run the msmdsrv exe

    @cached_property
    @backoff.on_exception(backoff.expo, FileNotFoundError, max_time=5)
    def _port(self) -> int:
        """Gets the port of the DB.

        We include exponential backoff in this function since it occasionally takes 1-3 seconds for msmdsrv.exe
        to generate the msmdsrv.port.txt file in the workspace

        Raises:
            FileNotFoundError: when ``msmdsrv.port.txt`` cannot be found in the SSAS workspace folder

        """
        try:
            return int((self._workspace_directory / "msmdsrv.port.txt").read_text(encoding="utf-16-le"))
        except FileNotFoundError as e:
            msg = f"Could not find msmdsrv.port.txt file in directory {self._workspace_directory}. This is needed to get the port of the SSAS instance"  # noqa: E501
            raise FileNotFoundError(msg) from e

    def _initialize_server(self) -> int:
        self._create_workspace()
        return self._run_msmdsrv()

    def _on_exit(self) -> None:
        if self.kill_on_exit:
            logger.info("Terminating SSAS Process", pid=self.pid)
            self.terminate()

    @staticmethod
    @backoff.on_exception(backoff.expo, ValueError, max_time=10)
    def _wait_until_terminated(process: psutil.Process) -> None:
        """Takes a process class and checks if the process is still running.

        Raises:
            ValueError: When the process is running

        """
        if process.is_running():
            msg = "The process will not terminate"
            raise ValueError(msg)

    def terminate(self) -> None:
        """Kills the SSAS instance.

        The code performs the following:

        1. Checks the PID. If the PID isn't associated with an active process, we declare the SSAS instance killed
        2. Checks the information associated with the PID (from ``get_msmdsrv_info``).
            If it's not running ``msmdsrv.exe`` with active ports, we consider it killed
        3. We call a terminate command
        4. We wait until the command is in a non-running state
        5. We then remove the corresponding workspace
        """
        try:
            p = psutil.Process(self.pid)
        except psutil.NoSuchProcess:  # something else killed it??
            logger.info("SSAS Proc already terminated", pid=self.pid)
            return
        except ValueError:
            logger.info("SSAS Proc never initialized", pid=self.pid)
            return
        if not get_msmdsrv_info(p):  # indicates another process has already taken this PID
            return
        p.terminate()
        self._wait_until_terminated(p)
        logger.info("Terminated SSAS Proc", pid=self.pid)

        shutil.rmtree(self._workspace_directory, ignore_errors=True)
        logger.info("Workspace Removed", directory=self._workspace_directory.as_posix())
