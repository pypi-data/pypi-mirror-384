from enum import Enum


class WlgroupCpuThrottlingColumns(Enum):
    EVENTCLASS = 0
    CURRENTTIME = 2
    INTEGERDATA = 10
    OBJECTID = 11
    SERVERDATA = 43
    ACTIVITYID = 46
    REQUESTID = 47
    APPLICATIONCONTEXT = 52


class WlgroupExceedsMemoryLimitColumns(Enum):
    EVENTCLASS = 0
    CURRENTTIME = 2
    STARTTIME = 3
    INTEGERDATA = 10
    OBJECTID = 11
    TEXTDATA = 42
    SERVERDATA = 43
    ACTIVITYID = 46
    REQUESTID = 47
    APPLICATIONCONTEXT = 52


class WlgroupExceedsProcessingLimitColumns(Enum):
    EVENTCLASS = 0
    CURRENTTIME = 2
    INTEGERDATA = 10
    OBJECTID = 11
    SERVERDATA = 43
    ACTIVITYID = 46
    REQUESTID = 47
    APPLICATIONCONTEXT = 52
