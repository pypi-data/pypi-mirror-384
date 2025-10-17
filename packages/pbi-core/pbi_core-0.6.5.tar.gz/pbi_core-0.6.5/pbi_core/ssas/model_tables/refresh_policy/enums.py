from enum import Enum


class PolicyType(Enum):
    BASIC = 0


class Granularity(Enum):
    INVALID = -1
    DAY = 0
    MONTH = 1
    QUARTER = 2
    YEAR = 3


class RefreshMode(Enum):
    IMPORT = 0
    HYBRID = 1
