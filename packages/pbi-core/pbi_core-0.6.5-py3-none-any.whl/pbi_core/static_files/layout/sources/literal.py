from datetime import UTC, datetime

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode

PrimitiveValue = int | str | datetime | bool | None
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def parse_literal(literal_val: str) -> PrimitiveValue:
    if literal_val == "null":
        return None

    if literal_val.endswith("L"):
        return int(literal_val[:-1])

    if literal_val in {"true", "false"}:
        return literal_val == "true"

    if literal_val.startswith("datetime"):
        return datetime.strptime(literal_val[9:-1], DATETIME_FORMAT).replace(tzinfo=UTC)

    return literal_val[1:-1]


def serialize_literal(value: PrimitiveValue) -> str:
    if value is None:
        return "null"

    # int check needs to be before bool since bool is a subclass of int in Python
    if isinstance(value, int):
        return f"{value}L"

    if value in {True, False}:
        return "true" if value else "false"

    if isinstance(value, datetime):
        return f"datetime'{value.strftime(DATETIME_FORMAT)}'"

    return f"'{value}'"


@define()
class _LiteralSourceHelper(LayoutNode):
    Value: str


@define()
class LiteralSource(LayoutNode):
    Literal: _LiteralSourceHelper

    def value(self) -> PrimitiveValue:
        return parse_literal(self.Literal.Value)

    def __repr__(self) -> str:
        return f"LiteralSource({self.Literal.Value})"

    @staticmethod
    def new(value: PrimitiveValue) -> "LiteralSource":
        return LiteralSource(Literal=_LiteralSourceHelper(Value=serialize_literal(value)))
