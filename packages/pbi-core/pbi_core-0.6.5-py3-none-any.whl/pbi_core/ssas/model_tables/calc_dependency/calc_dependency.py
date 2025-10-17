from attrs import field

from pbi_core.attrs import define
from pbi_core.ssas.model_tables.base import SsasReadonlyRecord


@define()
class CalcDependency(SsasReadonlyRecord):
    """Calculation Dependency.

    Represents a dependency between two DAX calculations in the model.
    This is recursive, so it connects non-direct dependencies.
    For instance, if we have three measures (A -> B -> C) there will be a dependency record between A and C.
    This entity is calculated, rather than being "real" like the other entities.


    SSAS spec:
    """

    database_name: str = field(eq=True)
    object_type: str = field(eq=True)
    table: str | None = field(eq=True, default=None)
    object: str = field(eq=True)
    expression: str | None = field(eq=True, default=None)
    referenced_object_type: str = field(eq=True)
    referenced_table: str | None = field(eq=True, default=None)
    referenced_object: str = field(eq=True)
    referenced_expression: str | None = field(eq=True, default=None)

    def pbi_core_name(self) -> str:
        """Returns the name displayed in the PBIX report."""
        return f"{self.object_type}[{self.object}] -> {self.referenced_object_type}[{self.referenced_object}]"
