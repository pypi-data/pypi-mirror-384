from enum import Enum


class FileLoadBeginColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    JOBID = 7  # Job ID for progress.
    SESSIONTYPE = 8  # Session type (what entity caused the operation).
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    SESSIONID = 39  # Session GUID.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class FileLoadEndColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    ENDTIME = 4  # Time at which the event ended. This column is not populated for starting event classes, such as SQL:BatchStarting or SP:Starting. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    DURATION = 5  # Amount of time (in milliseconds) taken by the event.
    JOBID = 7  # Job ID for progress.
    SESSIONTYPE = 8  # Session type (what entity caused the operation).
    INTEGERDATA = 10  # Integer data.
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    SEVERITY = 22  # Severity level of an exception.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    ERROR = 24  # Error number of a given event.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    SESSIONID = 39  # Session GUID.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class FileSaveBeginColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    JOBID = 7  # Job ID for progress.
    SESSIONTYPE = 8  # Session type (what entity caused the operation).
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    SESSIONID = 39  # Session GUID.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event
    ACTIVITYID = 46
    REQUESTID = 47


class FileSaveEndColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    ENDTIME = 4  # Time at which the event ended. This column is not populated for starting event classes, such as SQL:BatchStarting or SP:Starting. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    DURATION = 5  # Amount of time (in milliseconds) taken by the event.
    JOBID = 7  # Job ID for progress.
    SESSIONTYPE = 8  # Session type (what entity caused the operation).
    INTEGERDATA = 10  # Integer data.
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    SEVERITY = 22  # Severity level of an exception.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    ERROR = 24  # Error number of a given event.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    SESSIONID = 39  # Session GUID.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class PageOutBeginColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    JOBID = 7  # Job ID for progress.
    SESSIONTYPE = 8  # Session type (what entity caused the operation).
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    SESSIONID = 39  # Session GUID.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class PageOutEndColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    ENDTIME = 4  # Time at which the event ended. This column is not populated for starting event classes, such as SQL:BatchStarting or SP:Starting. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    DURATION = 5  # Amount of time (in milliseconds) taken by the event.
    JOBID = 7  # Job ID for progress.
    SESSIONTYPE = 8  # Session type (what entity caused the operation).
    INTEGERDATA = 10  # Integer data.
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    SEVERITY = 22  # Severity level of an exception.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    ERROR = 24  # Error number of a given event.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    SESSIONID = 39  # Session GUID.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class PageInBeginColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    JOBID = 7  # Job ID for progress.
    SESSIONTYPE = 8  # Session type (what entity caused the operation).
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    SESSIONID = 39  # Session GUID.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class PageInEndColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    ENDTIME = 4  # Time at which the event ended. This column is not populated for starting event classes, such as SQL:BatchStarting or SP:Starting. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    DURATION = 5  # Amount of time (in milliseconds) taken by the event.
    JOBID = 7  # Job ID for progress.
    SESSIONTYPE = 8  # Session type (what entity caused the operation).
    INTEGERDATA = 10  # Integer data.
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    SEVERITY = 22  # Severity level of an exception.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    ERROR = 24  # Error number of a given event.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    SESSIONID = 39  # Session GUID.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47
