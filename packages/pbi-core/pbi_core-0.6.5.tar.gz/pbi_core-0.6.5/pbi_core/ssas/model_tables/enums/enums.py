from enum import Enum


class DataState(Enum):
    """Source: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/93d1844f-a6c7-4dda-879b-2e26ed5cd297)."""

    READY = 1
    NO_DATA = 3
    CALCULATION_NEEDED = 4
    SEMANTIC_ERROR = 5
    EVALUATION_ERROR = 6
    DEPENDENCY_ERROR = 7
    INCOMPLETE = 8
    SYNTAX_ERROR = 9


class ObjectType(Enum):
    """Source: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/7a16a837-cb88-4cb2-a766-a97c4d0e1f43)."""

    MODEL = 1
    DATASOURCE = 2
    TABLE = 3
    COLUMN = 4
    ATTRIBUTE_HIERARCHY = 5
    PARTITION = 6
    RELATIONSHIP = 7
    MEASURE = 8
    HIERARCHY = 9
    LEVEL = 10
    KPI = 12
    CULTURE = 13
    LINGUISTIC_METADATA = 15
    PERSPECTIVE = 29
    PERSPECTIVE_TABLE = 30
    PERSPECTIVE_COLUMN = 31
    PERSPECTIVE_HIERARCHY = 32
    PERSPECTIVE_MEASURE = 33
    ROLE = 34
    ROLE_MEMBERSHIP = 35
    TABLE_PERMISSION = 36
    VARIATION = 37
    EXPRESSION = 41
    COLUMN_PERMISSION = 42
    CALCULATION_GROUP = 46
    CALCULATION_ITEM = 47
    QUERY_GROUP = 51


class DataType(Enum):
    """Source: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/00a9ec7a-5f4d-4517-8091-b370fe2dc18b)."""

    AUTOMATIC = 1
    STRING = 2
    INT64 = 6
    DOUBLE = 8
    DATE_TIME = 9
    DECIMAL = 10
    BOOLEAN = 11
    BINARY = 17
    UNKNOWN = 19
    UNKNOWNER = 20


class DataCategory(Enum):
    """Source: [Microsoft](https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t/6360ac84-0717-4170-bce0-284cbef419ca).

    Note:
        Only used for table, the Column and Measure DataCategories are just strings

    """

    UNKNOWN = 0
    REGULAR = 1
    TIME = 2
    GEOGRAPHY = 3
    ORGANIZATION = 4
    BILL_OF_MATERIALS = 5
    ACCOUNTS = 6
    CUSTOMERS = 7
    PRODUCTS = 8
    SCENARIO = 9
    QUANTITATIVE = 10
    UTILITY = 11
    CURRENCY = 12
    RATES = 13
    CHANNEL = 14
    PROMOTION = 15
    TIME_STR = "Time"  # TODO: I think we're accidentally merging two enums. sometimes it's a string in the pbix??
