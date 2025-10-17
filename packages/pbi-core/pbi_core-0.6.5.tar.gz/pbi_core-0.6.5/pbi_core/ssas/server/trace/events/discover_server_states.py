from enum import Enum


class ServerStateDiscoverBeginColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    EVENTSUBCLASS = 1  # Event Subclass provides additional information about each event class: 1: DISCOVER_CONNECTIONS 2: DISCOVER_SESSIONS 3: DISCOVER_TRANSACTIONS 6: DISCOVER_DB_CONNECTIONS 7: DISCOVER_JOBS 8: DISCOVER_LOCKS 12: DISCOVER_PERFORMANCE_COUNTERS 13: DISCOVER_MEMORYUSAGE 14: DISCOVER_JOB_PROGRESS 15: DISCOVER_MEMORYGRANT
    CURRENTTIME = 2  # Contains the current time of the server state discover event, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Contains the time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    CONNECTIONID = 25  # Contains the unique connection ID associated with the server state discover event.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTPROCESSID = 36  # Contains the process ID of the client application that created the connection to the server.
    APPLICATIONNAME = 37  # Contains the name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    SESSIONID = 39  # Contains the session ID associated with the server state discover event.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SPID = 41  # Contains the server process ID (SPID) that uniquely identifies the user session associated with the server state discover event. The SPID directly corresponds to the session GUID used by XMLA.
    TEXTDATA = 42  # Contains the text data associated with the event.
    SERVERNAME = 43  # Contains the name of the instance on which the server state discover event occurred.
    REQUESTPROPERTIES = 45  # Contains the properties of the current XMLA request.
    ACTIVITYID = 46
    REQUESTID = 47


class ServerStateDiscoverDataColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    EVENTSUBCLASS = 1  # Event Subclass provides additional information about each event class: 1: DISCOVER_CONNECTIONS 2: DISCOVER_SESSIONS 3: DISCOVER_TRANSACTIONS 6: DISCOVER_DB_CONNECTIONS 7: DISCOVER_JOBS 8: DISCOVER_LOCKS 12: DISCOVER_PERFORMANCE_COUNTERS 13: DISCOVER_MEMORYUSAGE 14: DISCOVER_JOB_PROGRESS 15: DISCOVER_MEMORYGRANT
    CURRENTTIME = 2  # Contains the current time of the server state discover event, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Contains the time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    CONNECTIONID = 25  # Contains the unique connection ID associated with the server state discover event.
    SESSIONID = 39  # Contains the session ID associated with the server state discover event.
    SPID = 41  # Contains the server process ID (SPID) that uniquely identifies the user session associated with the server state discover event. The SPID directly corresponds to the session GUID used by XMLA.
    TEXTDATA = 42  # Contains the text data associated with server response to the discover request.
    SERVERNAME = 43  # Contains the name of the instance on which the server state discover event occurred.


class ServerStateDiscoverEndColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    EVENTSUBCLASS = 1  # Event Subclass provides additional information about each event class: 1: DISCOVER_CONNECTIONS 2: DISCOVER_SESSIONS 3: DISCOVER_TRANSACTIONS 6: DISCOVER_DB_CONNECTIONS 7: DISCOVER_JOBS 8: DISCOVER_LOCKS 12: DISCOVER_PERFORMANCE_COUNTERS 13: DISCOVER_MEMORYUSAGE 14: DISCOVER_JOB_PROGRESS 15: DISCOVER_MEMORYGRANT
    CURRENTTIME = 2  # Contains the current time of the server state discover event, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Contains the time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    ENDTIME = 4  # Contains the time at which the event ended. This column is not populated for starting event classes, such as SQL:BatchStarting or SP:Starting. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    DURATION = 5  # Contains the amount of time (in milliseconds) taken by the event.
    CPUTIME = 6  # Contains the amount of CPU time (in milliseconds) used by the server state discover event.
    CONNECTIONID = 25  # Contains the unique connection ID associated with the server state discover event.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTPROCESSID = 36  # Contains the process ID of the client application that initiated the XMLA request.
    APPLICATIONNAME = 37  # Contains the name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    SESSIONID = 39  # Contains the Windows domain account associated with the server state discover event.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SPID = 41  # Contains the server process ID (SPID) that uniquely identifies the user session associated with the server state discover event. The SPID directly corresponds to the session GUID used by XMLA.
    TEXTDATA = 42  # Contains the text data associated with server response to the discover request.
    SERVERNAME = 43  # Contains the name of the instance on which the server state discover event occurred.
    ACTIVITYID = 46
    REQUESTID = 47
