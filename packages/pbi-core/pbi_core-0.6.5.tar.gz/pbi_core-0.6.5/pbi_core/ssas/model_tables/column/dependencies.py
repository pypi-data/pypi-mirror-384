from typing import TYPE_CHECKING, Literal

from pbi_core.lineage import LineageNode

from .helpers import HelpersMixin

if TYPE_CHECKING:
    from pbi_core.ssas.model_tables.attribute_hierarchy import AttributeHierarchy
    from pbi_core.ssas.model_tables.base import SsasTable
    from pbi_core.ssas.model_tables.measure import Measure
    from pbi_core.ssas.model_tables.table_permission import TablePermission

    from .column import Column


class DependencyMixin(HelpersMixin):
    explicit_name: str | None
    expression: str | int | None

    def get_lineage(self, lineage_type: Literal["children", "parents"]) -> LineageNode:
        if lineage_type == "children":
            children_nodes: list[Column | Measure | AttributeHierarchy] = [
                self.attribute_hierarchy(),
                *self.child_measures(),
                *self.sorting_columns(),
                *self.child_columns(),
            ]
            children_lineage = [p.get_lineage(lineage_type) for p in children_nodes if p is not None]
            return LineageNode(self, lineage_type, children_lineage)
        parent_nodes: list[SsasTable | None] = [
            self.table(),
            self.sort_by_column(),
            *self.parent_columns(),
            *self.parent_measures(),
        ]
        parent_lineage = [p.get_lineage(lineage_type) for p in parent_nodes if p is not None]
        return LineageNode(self, lineage_type, parent_lineage)

    def child_measures(self, *, recursive: bool = False) -> set["Measure"]:
        """Returns measures dependent on this Column."""
        object_type = self._column_type()
        dependent_measures = self._tabular_model.calc_dependencies.find_all({
            "referenced_object_type": object_type,
            "referenced_table": self.table().name,
            "referenced_object": self.explicit_name,
            "object_type": "MEASURE",
        })
        child_keys: list[tuple[str | None, str]] = [(m.table, m.object) for m in dependent_measures]
        full_dependencies = [m for m in self._tabular_model.measures if (m.table().name, m.name) in child_keys]

        if recursive:
            recursive_dependencies: set[Measure] = set()
            for dep in full_dependencies:
                if f"[{self.explicit_name}]" in str(dep.expression):
                    recursive_dependencies.add(dep)
                    recursive_dependencies.update(dep.child_measures(recursive=True))
            return recursive_dependencies

        return {x for x in full_dependencies if f"[{self.explicit_name}]" in str(x.expression)}

    def parent_measures(self, *, recursive: bool = False) -> set["Measure"]:
        """Returns measures this column is dependent on.

        Note:
            Calculated columns can use Measures too :(.

        """
        object_type = self._column_type()
        dependent_measures = self._tabular_model.calc_dependencies.find_all({
            "object_type": object_type,
            "table": self.table().name,
            "object": self.explicit_name,
            "referenced_object_type": "MEASURE",
        })
        parent_keys = [(m.referenced_table, m.referenced_object) for m in dependent_measures]
        full_dependencies = [m for m in self._tabular_model.measures if (m.table().name, m.name) in parent_keys]

        if recursive:
            recursive_dependencies: set[Measure] = set()
            for dep in full_dependencies:
                if f"[{dep.name}]" in str(self.expression):
                    recursive_dependencies.add(dep)
                    recursive_dependencies.update(dep.parent_measures(recursive=True))
            return recursive_dependencies

        return {x for x in full_dependencies if f"[{x.name}]" in str(self.expression)}

    def child_columns(self, *, recursive: bool = False) -> set["Column"]:
        """Returns columns dependent on this Column.

        Note:
            Only occurs when the dependent column is calculated (expression is not None).

        """
        object_type = self._column_type()
        dependent_measures = self._tabular_model.calc_dependencies.find_all({
            "referenced_object_type": object_type,
            "referenced_table": self.table().name,
            "referenced_object": self.explicit_name,
        })
        assert all(m.table is not None for m in dependent_measures)
        child_keys: list[tuple[str, str]] = [  # pyright: ignore reportAssignmentType
            (m.table, m.object) for m in dependent_measures if m.object_type in {"CALC_COLUMN", "COLUMN"}
        ]
        full_dependencies = [m for m in self._tabular_model.columns if (m.table().name, m.explicit_name) in child_keys]

        if recursive:
            recursive_dependencies: set[Column] = set()
            for dep in full_dependencies:
                if f"[{self.explicit_name}]" in str(dep.expression):
                    recursive_dependencies.add(dep)
                    recursive_dependencies.update(dep.child_columns(recursive=True))
            return recursive_dependencies

        return {x for x in full_dependencies if f"[{self.explicit_name}]" in str(x.expression)}

    def parent_columns(self, *, recursive: bool = False) -> set["Column"]:
        """Returns Columns this Column is dependent on.

        Note:
            Parent columns are non-empty only when the column is calculated.
            Columns defined by a PowerQuery import or DirectQuery do not have parent columns.

        """
        object_type = self._column_type()
        if object_type == "COLUMN":
            return set()
        dependent_measures = self._tabular_model.calc_dependencies.find_all({
            "object_type": object_type,
            "table": self.table().name,
            "object": self.explicit_name,
        })
        parent_keys = {
            (m.referenced_table, m.referenced_object)
            for m in dependent_measures
            if m.referenced_object_type in {"CALC_COLUMN", "COLUMN"}
        }
        full_dependencies = [c for c in self._tabular_model.columns if (c.table().name, c.explicit_name) in parent_keys]

        if recursive:
            recursive_dependencies: set[Column] = set()
            for dep in full_dependencies:
                if f"[{dep.explicit_name}]" in str(self.expression):
                    recursive_dependencies.add(dep)
                    recursive_dependencies.update(dep.parent_columns(recursive=True))
            return recursive_dependencies

        return {x for x in full_dependencies if f"[{x.explicit_name}]" in str(self.expression)}

    def child_table_permissions(self) -> set["TablePermission"]:
        """Returns table permissions dependent via DAX on this Column."""
        object_type = self._column_type()
        dependent_permissions = self._tabular_model.calc_dependencies.find_all({
            "referenced_object_type": object_type,
            "referenced_table": self.table().name,
            "referenced_object": self.explicit_name,
            "object_type": "ROWS_ALLOWED",
        })

        full_dependencies: list[TablePermission] = []
        for dp in dependent_permissions:
            table, rls_name = dp.table, dp.object
            role = self._tabular_model.roles.find({"name": rls_name})
            full_dependencies.extend(
                tp
                for tp in role.table_permissions()
                if tp.table().name == table and f"[{self.explicit_name}]" in str(tp.filter_expression)
            )

        return set(full_dependencies)

    def parents(self, *, recursive: bool = False) -> "set[Column | Measure]":
        """Returns all columns and measures this Column is dependent on."""
        full_dependencies = self.parent_columns() | self.parent_measures()
        if recursive:
            recursive_dependencies: set[Column | Measure] = set()
            for dep in full_dependencies:
                recursive_dependencies.add(dep)
                recursive_dependencies.update(dep.parents(recursive=True))
            return recursive_dependencies

        return full_dependencies

    def children(self, *, recursive: bool = False) -> "set[Column | Measure]":
        """Returns all columns and measures dependent on this Column."""
        full_dependencies = self.child_columns() | self.child_measures()
        if recursive:
            recursive_dependencies: set[Column | Measure] = set()
            for dep in full_dependencies:
                recursive_dependencies.add(dep)
                recursive_dependencies.update(dep.children(recursive=True))
            return recursive_dependencies
        return full_dependencies
