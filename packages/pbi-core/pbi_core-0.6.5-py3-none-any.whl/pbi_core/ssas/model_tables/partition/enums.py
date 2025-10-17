from enum import Enum


class PartitionMode(Enum):
    """Source: [Microsoft](https://learn.microsoft.com/en-us/analysis-services/tmsl/partitions-object-tmsl?view=asallproducts-allversions)."""

    IMPORT = 0
    DIRECT_QUERY = 1  # not verified
    DEFAULT = 2  # not verified
    PUSH = 3


class PartitionType(Enum):
    """Source: [Microsoft](https://learn.microsoft.com/en-us/analysis-services/tmsl/partitions-object-tmsl?view=asallproducts-allversions)."""

    QUERY = 1
    CALCULATED = 2
    _NONE = 3
    M = 4
    ENTITY = 5
    CALCULATION_GROUP = 7


class DataView(Enum):
    FULL = 0
    SAMPLE = 1
    DEFAULT = 3
