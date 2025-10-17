from typing import Any, ClassVar, Literal, Self, cast

from attrs import Attribute, field, fields, setters
from bs4 import BeautifulSoup
from structlog import get_logger

from pbi_core.attrs import BaseValidation, define
from pbi_core.lineage import LineageNode
from pbi_core.ssas.model_tables._group import IdBase
from pbi_core.ssas.server._commands import Command
from pbi_core.ssas.server.tabular_model import BaseTabularModel
from pbi_core.ssas.server.utils import ROW_TEMPLATE, python_to_xml

logger = get_logger()


@define()
class SsasTable(BaseValidation, IdBase):
    id: int = field(eq=True, repr=True, on_setattr=setters.frozen)
    """Unique identifier of the object."""

    _delete_on_next_sync: bool = field(default=False, eq=False, repr=False)
    """Marks the object to be deleted on the next sync to SSAS."""

    _tabular_model: BaseTabularModel = field(repr=False, eq=False, init=False)

    _db_field_names: ClassVar[dict[str, str]] = {}
    """Mapping of python attribute names to database field names.

    Example:
        For the Column class:
        {"ExplicitName": "explicit_name"...}
    """
    _repr_name_field: str = field(default="name", repr=False, eq=False)

    @classmethod
    def _db_type_name(cls) -> str:
        return cls.__name__

    @classmethod
    def model_validate(cls, data: dict) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        formatted_data = cls.to_snake_case(data)

        return super().model_validate(formatted_data)

    @classmethod
    def _db_command_obj_name(cls) -> str:
        """Returns the name of the object expected by their XMLA commands.

        Generally a simple pluralization, but occasionally different in subclasses.
        """
        return cls.__name__ + "s"

    def pbi_core_name(self) -> str:
        """Returns the name displayed in the PBIX report.

        Uses the _repr_name_field to determine the field to use.
        Defaults to self.name
        """
        return str(getattr(self, self._repr_name_field))

    def __str__(self) -> str:
        display_fields = []
        for f in cast("list[Attribute]", fields(self.__class__)):
            if f.repr:
                val = getattr(self, f.name)
                if val != f.default:
                    if f.repr is True:
                        display_fields.append(f"{f.name}={val}")
                    else:
                        display_fields.append(f"{f.name}={f.repr(val)}")

        field_text = ", ".join(display_fields)
        return f"{self.__class__.__name__}({field_text})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id}: {self.pbi_core_name()})"

    @classmethod
    def to_snake_case(cls: type[Self], raw_values: dict[str, Any]) -> dict[str, Any]:
        """Converts SnakeCase to snake_case.

        If a "special_cases" example appears, that transformation is applied.
        If the first character is capitalized, it is lower cased
        If any other character is capitalized, it is lower cased and prefixed with a "_"
        """

        def update_char(char: str, prev_char: str) -> str:
            if char.isupper() and prev_char.islower() and prev_char != "_":
                return f"_{char.lower()}"
            return char.lower()

        def case_helper(field_name: str) -> str:
            SPECIAL_CASES = {  # noqa: N806
                "owerBI": "owerbi",
                "KPIID": "KpiId",
            }
            for old_segment, new_segment in SPECIAL_CASES.items():
                field_name = field_name.replace(old_segment, new_segment)
            return "".join(
                update_char(curr, prev) for prev, curr in zip(" " + field_name[:-1], field_name, strict=False)
            ).strip("_")

        ret: dict[str, Any] = {}
        for field_name, field_value in raw_values.items():
            formatted_field_name = case_helper(field_name)
            if formatted_field_name != field_name:
                cls._db_field_names[formatted_field_name] = field_name
            ret[formatted_field_name] = field_value
        return ret

    def query_dax(self, query: str, db_name: str | None = None) -> None:
        """Helper function to remove the ``._tabular_model.server`` required to run a DAX query from an SSAS element."""
        logger.debug("Executing DAX query", query=query, db_name=db_name)
        self._tabular_model.server.query_dax(query, db_name=db_name)

    def query_xml(self, query: str, db_name: str | None = None) -> BeautifulSoup:
        """Helper function to remove the ``._tabular_model.server`` required to run an XML query in SSAS."""
        logger.debug("Executing XML query", query=query, db_name=db_name)
        return self._tabular_model.server.query_xml(query, db_name)

    @staticmethod
    def _get_row_xml(values: dict[str, Any], command: Command) -> str:
        fields: list[tuple[str, str]] = []
        for field_name, field_value in values.items():
            if field_name not in command.field_order:
                continue
            if field_value is None:
                continue
            fields.append((field_name, python_to_xml(field_value)))
        fields = command.sort(fields)
        return ROW_TEMPLATE.render(fields=fields)

    @staticmethod
    def render_xml_command(values: dict[str, Any], command: Command, db_name: str) -> str:
        """XMLA commands: create/alter/delete/rename/refresh.

        Commands are generally in the form:
        <batch>
            <create/alter...>
                <db>
            </create/alter...>
            <entity-schema.../>
            <records.../>
        </batch>

        Entity schemas can be found at `pbi_core/ssas/server/command_templates/schema`
        """
        logger.debug(
            "Rendering XML command",
            db_name=db_name,
            fields=list(values.keys()),
        )
        xml_row = SsasTable._get_row_xml(values, command)
        xml_entity_definition = command.entity_template.render(rows=xml_row)
        return command.base_template.render(db_name=db_name, entity_def=xml_entity_definition)

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        """Creates a lineage node tracking the data parents/children of a record."""
        return LineageNode(self, lineage_type)

    def get_altered_fields(self) -> list[Attribute]:
        """Returns a list of fields that have been altered since the last sync from SSAS."""
        ret = []
        for f in fields(self.__class__):
            if f.on_setattr is setters.frozen or f.name.startswith("_"):
                continue

            if self._original_data is None:
                ret.append(f)
                continue

            old_val = getattr(self._original_data, f.name)
            new_val = getattr(self, f.name)
            if old_val != new_val:
                ret.append(f)
        return ret

    def xml_fields(self) -> dict[str, Any]:
        base = self.model_dump()

        # All update/create commands require the ID field
        ret: dict[str, Any] = {
            "ID": self.id,
        }
        for f in self.get_altered_fields():
            db_name = self._db_field_names.get(f.name, f.name)
            ret[db_name] = base.get(f.name)
        return ret
