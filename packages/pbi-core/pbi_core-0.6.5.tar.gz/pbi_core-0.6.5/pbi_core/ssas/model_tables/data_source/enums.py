from enum import Enum


class ImpersonationMode(Enum):
    DEFAULT = 1
    IMPERSONATE_ACCOUNT = 2
    IMPERSONATE_ANONYMOUS = 3
    IMPERSONATE_CURRENT_USER = 4
    IMPERSONATE_SERVICE_ACCOUNT = 5
    IMPERSONATE_UNATTENDED_ACCOUNT = 6


class DataSourceType(Enum):
    PROVIDER = 1
    STRUCTURED = 2


class Isolation(Enum):
    READ_COMMITTED = 1
    SNAPSHOT = 2
