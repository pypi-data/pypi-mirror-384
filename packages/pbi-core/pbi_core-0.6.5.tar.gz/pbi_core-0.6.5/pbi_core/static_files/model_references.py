from typing import TYPE_CHECKING

from pbi_core.attrs import BaseValidation, define

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables import Column, Measure, Table
    from pbi_core.ssas.server.tabular_model.tabular_model import BaseTabularModel


@define()
class ModelColumnReference(BaseValidation):
    column: str
    table: str

    def to_model(self, tabular_model: "BaseTabularModel") -> "Column":
        return tabular_model.columns.find(lambda c: (c.explicit_name == self.column) and (c.table().name == self.table))


@define()
class ModelTableReference(BaseValidation):
    table: str

    def to_model(self, tabular_model: "BaseTabularModel") -> "Table":
        return tabular_model.tables.find(lambda t: (t.name == self.table))


@define()
class ModelMeasureReference(BaseValidation):
    measure: str
    table: str

    def to_model(self, tabular_model: "BaseTabularModel") -> "Measure":
        return tabular_model.measures.find(lambda m: (m.name == self.measure) and (m.table().name == self.table))
