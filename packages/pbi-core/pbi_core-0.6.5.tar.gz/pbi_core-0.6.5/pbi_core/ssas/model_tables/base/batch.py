from typing import TYPE_CHECKING

import jinja2

from pbi_core.ssas.server._commands import BASE_ALTER_TEMPLATE

if TYPE_CHECKING:
    from .ssas_tables import SsasAlter


BATCH_COMMAND = jinja2.Template("""
<Batch Transaction="false" xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
    {{inner_commands}}
</Batch>
""")


class AlterCommand:
    database_id: str
    object_types: dict[str, list["SsasAlter"]]

    def __init__(self, database_id: str, object_types: dict[str, list["SsasAlter"]]) -> None:
        self.database_id = database_id
        self.object_types = object_types

    def render_xml(self) -> str:
        entity_commands: list[str] = []
        for entities in self.object_types.values():
            entity_rows = [
                table._get_row_xml(
                    table.xml_fields(),
                    table._commands.alter,
                )
                for table in entities
            ]
            entity_rows_str = "\n".join(entity_rows)
            entity_command = entities[0]._commands.alter.entity_template.render(rows=entity_rows_str)
            entity_commands.append(entity_command)
        ret = BASE_ALTER_TEMPLATE.render(
            db_name=self.database_id,
            entity_def="\n".join(entity_commands),
        )
        return "\n".join(ret.splitlines()[1:-1])  # the first and last are the batch start/end


class Batch:
    commands: list[AlterCommand]

    def __init__(self, commands: list[AlterCommand]) -> None:
        self.commands = commands

    def render_xml(self) -> str:
        command_strs = [command.render_xml() for command in self.commands]
        return BATCH_COMMAND.render(inner_commands="\n".join(command_strs))
