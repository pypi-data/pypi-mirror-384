import attrs
import bs4
import jinja2

BASE_ALTER_TEMPLATE = jinja2.Template(
    """
<Batch Transaction="false" xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
  <Alter xmlns="http://schemas.microsoft.com/analysisservices/2014/engine">
    <DatabaseID>{{db_name}}</DatabaseID>
    {{entity_def}}
  </Alter>
</Batch>
""".strip(),
)

# note that Transaction = true. I think it's necessary, not very tested tbqh
BASE_REFRESH_TEMPLATE = jinja2.Template(
    """
<Batch Transaction="false" xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
  <Refresh xmlns="http://schemas.microsoft.com/analysisservices/2014/engine">
	<DatabaseID>{{db_name}}</DatabaseID>
    {{entity_def}}
  </Refresh>
</Batch>
""".strip(),
)
BASE_RENAME_TEMPLATE = jinja2.Template(
    """
<Batch Transaction="false" xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
  <Alter xmlns="http://schemas.microsoft.com/analysisservices/2014/engine">
    <DatabaseID>{{db_name}}</DatabaseID>
  </Alter>
  <Rename xmlns="http://schemas.microsoft.com/analysisservices/2014/engine">
    <DatabaseID>{{db_name}}</DatabaseID>
    {{entity_def}}
  </Rename>
</Batch>
""".strip(),
)
BASE_DELETE_TEMPLATE = jinja2.Template(
    """
<Batch Transaction="false" xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
  <Delete xmlns="http://schemas.microsoft.com/analysisservices/2014/engine">
    <DatabaseID>{{db_name}}</DatabaseID>
    {{entity_def}}
  </Delete>
</Batch>
""".strip(),
)
BASE_CREATE_TEMPLATE = jinja2.Template(
    """
<Batch Transaction="false" xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
  <Create xmlns="http://schemas.microsoft.com/analysisservices/2014/engine">
    <DatabaseID>{{db_name}}</DatabaseID>
    {{entity_def}}
  </Create>
</Batch>
""".strip(),
)
base_commands = {
    "alter": BASE_ALTER_TEMPLATE,
    "create": BASE_CREATE_TEMPLATE,
    "delete": BASE_DELETE_TEMPLATE,
    "refresh": BASE_REFRESH_TEMPLATE,
    "rename": BASE_RENAME_TEMPLATE,
}


@attrs.define()
class Command:
    entity_template: jinja2.Template
    base_template: jinja2.Template
    field_order: list[str]

    def sort(self, fields: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return sorted(fields, key=lambda k: self.field_order.index(k[0]))


class NoCommands:
    def __init__(self, **kwargs: str) -> None:
        for field_name, template_text in kwargs.items():
            v = Command(
                entity_template=jinja2.Template(template_text),
                base_template=base_commands[field_name],
                field_order=self.get_field_order(template_text),
            )
            self.__setattr__(field_name, v)

    @staticmethod
    def get_field_order(text: str) -> list[str]:
        """Gets the order of the fields for the command, based on the ``xs:sequence`` section of the XML command."""
        tree = bs4.BeautifulSoup(text, "xml")
        row = tree.find("xs:complexType", {"name": "row"})
        assert isinstance(row, bs4.element.Tag)
        ret: list[str] = []
        for e in row.find_all("xs:element"):
            assert isinstance(e, bs4.element.Tag)
            val = e["name"]
            assert isinstance(val, str)
            ret.append(val)
        return ret


class BaseCommands(NoCommands):
    alter: Command
    create: Command
    delete: Command

    def __repr__(self) -> str:
        return "BaseCommands(alter, create, delete)"

    @staticmethod
    def new(data: dict[str, str]) -> "BaseCommands":
        return BaseCommands(
            alter=data["alter.xml"],
            create=data["create.xml"],
            delete=data["delete.xml"],
        )


class RenameCommands(BaseCommands):
    rename: Command

    def __repr__(self) -> str:
        return "RenameCommands(alter, create, delete, rename)"

    @staticmethod
    def new(data: dict[str, str]) -> "RenameCommands":
        return RenameCommands(
            alter=data["alter.xml"],
            create=data["create.xml"],
            delete=data["delete.xml"],
            rename=data["rename.xml"],
        )


class RefreshCommands(RenameCommands):
    refresh: Command

    def __repr__(self) -> str:
        return "RefreshCommands(alter, create, delete, rename, refresh)"

    @staticmethod
    def new(data: dict[str, str]) -> "RefreshCommands":
        return RefreshCommands(
            alter=data["alter.xml"],
            create=data["create.xml"],
            delete=data["delete.xml"],
            rename=data["rename.xml"],
            refresh=data["refresh.xml"],
        )


class ModelCommands(NoCommands):
    alter: Command
    refresh: Command
    rename: Command

    def __repr__(self) -> str:
        return "ModelCommands(alter, refresh, rename)"

    @staticmethod
    def new(data: dict[str, str]) -> "ModelCommands":
        return ModelCommands(
            alter=data["alter.xml"],
            refresh=data["refresh.xml"],
            rename=data["rename.xml"],
        )


Commands = BaseCommands | RenameCommands | RefreshCommands | ModelCommands
