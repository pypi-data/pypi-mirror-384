import pathlib
import socket
from typing import Any
from xml.sax.saxutils import escape  # nosec

import attrs
import jinja2
import psutil

from ._commands import BaseCommands, ModelCommands, RefreshCommands, RenameCommands

COMMAND_DIR: pathlib.Path = pathlib.Path(__file__).parent / "command_templates"

COMMAND_TEMPLATES: dict[str, jinja2.Template] = {
    f.name: jinja2.Template(f.read_text()) for f in COMMAND_DIR.iterdir() if f.is_file()
}
commands: dict[str, dict[str, str]] = {
    folder.name: {f.name: f.read_text() for f in folder.iterdir() if f.is_file()}
    for folder in (COMMAND_DIR / "schema").iterdir()
    if folder.is_dir()
}


class SsasCommands:
    annotation = RenameCommands.new(commands["Annotations"])
    calculation_group = BaseCommands.new(commands["CalculationGroup"])
    calculation_item = RenameCommands.new(commands["CalculationItems"])
    column = RenameCommands.new(commands["Columns"])
    column_permission = BaseCommands.new(commands["ColumnPermissions"])
    culture = RenameCommands.new(commands["Cultures"])
    data_source = RenameCommands.new(commands["DataSources"])
    detail_row_definition = BaseCommands.new(commands["DetailRowsDefinition"])
    expression = RenameCommands.new(commands["Expressions"])
    extended_property = RenameCommands.new(commands["ExtendedProperties"])
    format_string_definition = BaseCommands.new(commands["FormatStringDefinitions"])
    hierarchy = RenameCommands.new(commands["Hierarchies"])
    kpi = BaseCommands.new(commands["Kpis"])
    level = RenameCommands.new(commands["Levels"])
    linguistic_metadata = BaseCommands.new(commands["LinguisticMetadata"])
    measure = RenameCommands.new(commands["Measures"])
    model = ModelCommands.new(commands["Model"])
    object_translation = BaseCommands.new(commands["ObjectTranslations"])
    partition = RefreshCommands.new(commands["Partitions"])
    perspective_column = BaseCommands.new(commands["PerspectiveColumns"])
    perspective_hierarchy = BaseCommands.new(commands["PerspectiveHierarchies"])
    perspective_measure = BaseCommands.new(commands["PerspectiveMeasures"])
    perspective = RenameCommands.new(commands["Perspectives"])
    perspective_table = BaseCommands.new(commands["PerspectiveTables"])
    query_group = BaseCommands.new(commands["QueryGroups"])
    refresh_policy = BaseCommands.new(commands["RefreshPolicy"])
    relationship = RenameCommands.new(commands["Relationships"])
    role_membership = BaseCommands.new(commands["RoleMemberships"])
    role = RenameCommands.new(commands["Roles"])
    table_permission = BaseCommands.new(commands["TablePermissions"])
    table = RefreshCommands.new(commands["Tables"])
    variation = RenameCommands.new(commands["Variations"])


ROOT_FOLDER = pathlib.Path(__file__).parents[2]
SKU_ERROR = "ImageLoad/ImageSave commands supports loading/saving data for Excel, Power BI Desktop or Zip files. File extension can be only .XLS?, .PBIX or .ZIP."  # noqa: E501


@attrs.frozen()
class ServerInfo:
    """Basic information about an SSAS instance from its PID."""

    port: int
    workspace_directory: pathlib.Path


def get_msmdsrv_info(process: psutil.Process) -> ServerInfo | None:
    """Parses ``ServerInfo`` information from PID information.

    Note:
        This function currently assumes that the SSAS Process is called like
        ``pbi_core`` calls it. If you don't include the ``-s`` flag in the command,
        this function will fail

    """

    def check_ports(proc: psutil.Process) -> int | None:
        ports = [
            conn.laddr.port
            for conn in proc.net_connections()
            if conn.status == "LISTEN"
            and conn.family == socket.AF_INET  # to only get the IPV4, not IPV6 version of the connection
        ]
        if len(ports) != 1:
            return None
        return ports[0]

    def check_workspace(proc: psutil.Process) -> pathlib.Path | None:
        try:
            exe_start_command: list[str] = proc.cmdline()
        except psutil.AccessDenied:
            return None

        if "-s" not in exe_start_command:
            return None
        return pathlib.Path(exe_start_command[exe_start_command.index("-s") + 1])

    if process.name() != "msmdsrv.exe":
        return None
    if (port := check_ports(process)) is None:
        return None
    if (workspace_dir := check_workspace(process)) is None:
        return None
    return ServerInfo(port, workspace_dir)


def python_to_xml(text: Any) -> str:
    """Implements basic XML transformation when returning data to SSAS backend.

    Converts:

    - True/False to true/false

    Args:
        text (Any): a value to be sent to SSAS

    Returns:
        str: A stringified, xml-safe version of the value

    """
    if text in {True, False}:
        return str(text).lower()
    if not isinstance(text, str):
        text = str(text)
    return escape(text)


ROW_TEMPLATE = jinja2.Template(
    """
<row xmlns="urn:schemas-microsoft-com:xml-analysis:rowset">
{%- for k, v in fields %}
    <{{k}}>{{v}}</{{k}}>
{%- endfor %}
</row>
""",
)
