import typing

if typing.TYPE_CHECKING:
    from pbi_core.ssas.model_tables.base import SsasTable

from ._group import Group, RowNotFoundError
from .alternate_of import AlternateOf
from .annotation import Annotation
from .attribute_hierarchy import AttributeHierarchy
from .calc_dependency import CalcDependency
from .calculation_group import CalculationGroup
from .calculation_item import CalculationItem
from .column import Column
from .column_permission import ColumnPermission
from .culture import Culture
from .data_source import DataSource
from .detail_row_definition import DetailRowDefinition
from .expression import Expression
from .extended_property import ExtendedProperty
from .format_string_definition import FormatStringDefinition
from .group_by_column import GroupByColumn
from .hierarchy import Hierarchy
from .kpi import KPI
from .level import Level
from .linguistic_metadata import LinguisticMetadata
from .measure import Measure
from .model import Model
from .object_translation import ObjectTranslation
from .partition import Partition
from .perspective import Perspective
from .perspective_column import PerspectiveColumn
from .perspective_hierarchy import PerspectiveHierarchy
from .perspective_measure import PerspectiveMeasure
from .perspective_set import PerspectiveSet
from .perspective_table import PerspectiveTable
from .query_group import QueryGroup
from .refresh_policy import RefreshPolicy
from .related_column_detail import RelatedColumnDetail
from .relationship import Relationship
from .role import Role
from .role_membership import RoleMembership
from .set import Set
from .table import Table
from .table_permission import TablePermission
from .variation import Variation

__all__ = [
    "KPI",
    "AlternateOf",
    "Annotation",
    "AttributeHierarchy",
    "CalcDependency",
    "CalculationGroup",
    "CalculationItem",
    "Column",
    "ColumnPermission",
    "Culture",
    "DataSource",
    "DetailRowDefinition",
    "Expression",
    "ExtendedProperty",
    "FormatStringDefinition",
    "Group",
    "GroupByColumn",
    "Hierarchy",
    "Level",
    "LinguisticMetadata",
    "Measure",
    "Model",
    "ObjectTranslation",
    "Partition",
    "Perspective",
    "PerspectiveColumn",
    "PerspectiveHierarchy",
    "PerspectiveMeasure",
    "PerspectiveSet",
    "PerspectiveTable",
    "QueryGroup",
    "RefreshPolicy",
    "RelatedColumnDetail",
    "Relationship",
    "Role",
    "RoleMembership",
    "RowNotFoundError",
    "Set",
    "Table",
    "TablePermission",
    "Variation",
]

FIELD_TYPES: dict[str, type["SsasTable"]] = {
    "alternate_ofs": AlternateOf,
    "annotations": Annotation,
    "attribute_hierarchies": AttributeHierarchy,
    "calc_dependencies": CalcDependency,
    "calculation_groups": CalculationGroup,
    "calculation_items": CalculationItem,
    "column_permissions": ColumnPermission,
    "columns": Column,
    "cultures": Culture,
    "data_sources": DataSource,
    "detail_row_definitions": DetailRowDefinition,
    "expressions": Expression,
    "extended_properties": ExtendedProperty,
    "format_string_definitions": FormatStringDefinition,
    "group_by_columns": GroupByColumn,
    "hierarchies": Hierarchy,
    "kpis": KPI,
    "levels": Level,
    "linguistic_metadata": LinguisticMetadata,
    "measures": Measure,
    "model": Model,
    "object_translations": ObjectTranslation,
    "partitions": Partition,
    "perspective_columns": PerspectiveColumn,
    "perspective_hierarchies": PerspectiveHierarchy,
    "perspective_measures": PerspectiveMeasure,
    "perspective_sets": PerspectiveSet,
    "perspective_tables": PerspectiveTable,
    "perspectives": Perspective,
    "query_groups": QueryGroup,
    "relationships": Relationship,
    "refresh_policies": RefreshPolicy,
    "related_column_details": RelatedColumnDetail,
    "role_memberships": RoleMembership,
    "roles": Role,
    "sets": Set,
    "table_permissions": TablePermission,
    "tables": Table,
    "variations": Variation,
}
