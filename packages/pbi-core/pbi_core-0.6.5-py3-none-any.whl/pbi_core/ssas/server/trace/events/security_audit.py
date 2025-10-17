from enum import Enum


class AuditLoginColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    SEVERITY = 22  # Severity level of an exception.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    ERROR = 24  # Error number of a given event.
    CONNECTIONID = 25  # Unique connection ID.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTHOSTNAME = 35  # Name of the computer on which the client is running. This data column is populated if the host name is provided by the client.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    APPLICATIONNAME = 37  # Name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class AuditLogoutColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    ENDTIME = 4  # Time at which the event ended. This column is not populated for starting event classes, such as SQL:BatchStarting or SP:Starting. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    DURATION = 5  # Amount of time (in milliseconds) taken by the event.
    CPUTIME = 6  # Amount of CPU time (in milliseconds) used by the event.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    CONNECTIONID = 25  # Unique connection ID.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTHOSTNAME = 35  # Name of the computer on which the client is running. This data column is populated if the host name is provided by the client.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    APPLICATIONNAME = 37  # Name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class AuditServerStartsAndStopsColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    EVENTSUBCLASS = 1  # Event Subclass provides additional information about each event class: 1: Instance Shutdown 2: Instance Started 3: Instance Paused 4: Instance Continued
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    SEVERITY = 22  # Severity level of an exception.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    ERROR = 24  # Error number of a given event.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class AuditObjectPermissionEventColumns(Enum):
    OBJECTID = 11  # Object ID (note this is a string).
    OBJECTTYPE = 12  # Object type.
    OBJECTNAME = 13  # Object name.
    OBJECTPATH = 14  # Object path. A comma-separated list of parents, starting with the object's parent.
    OBJECTREFERENCE = 15  # Object reference. Encoded as XML for all parents, using tags to describe the object.
    SEVERITY = 22  # Severity level of an exception.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    ERROR = 24  # Error number of a given event.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTHOSTNAME = 35  # Name of the computer on which the client is running. This data column is populated if the host name is provided by the client.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    APPLICATIONNAME = 37  # Name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    SESSIONID = 39  # Session GUID.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SPID = 41  # Server process ID. This uniquely identifies a user session. This directly corresponds to the session GUID used by XML/A.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class AuditAdminOperationsEventColumns(Enum):
    EVENTSUBCLASS = 1  # Event Subclass provides additional information about each event class: 1: Backup 2: Restore 3: Synchronize 4: Detach 5: Attach 6: ImageLoad 7: ImageSave
    SEVERITY = 22  # Severity level of an exception.
    SUCCESS = 23  # 1 = success. 0 = failure (for example, a 1 means success of a permissions check and a 0 means a failure of that check).
    ERROR = 24  # Error number of a given event.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTHOSTNAME = 35  # Name of the computer on which the client is running. This data column is populated if the host name is provided by the client.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    APPLICATIONNAME = 37  # Name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    SESSIONID = 39  # Session GUID.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SPID = 41  # Server process ID. This uniquely identifies a user session. This directly corresponds to the session GUID used by XML/A.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47
