from enum import Enum


class MetadataPermission(Enum):
    """Source: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/ac2ceeb3-a54e-4bf5-85b0-a770d4b1716e)."""

    DEFAULT = 0
    _NONE = 1
    READ = 2
