from enum import Enum


class ExistingConnectionColumns(Enum):
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    CONNECTIONID = 25  # Unique connection ID.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTHOSTNAME = 35  # Name of the computer on which the client is running. This data column is populated if the host name is provided by the client.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    APPLICATIONNAME = 37  # Name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    SPID = 41  # Server process ID. This uniquely identifies a user session. This directly corresponds to the session GUID used by XML/A.
    SERVERNAME = 43  # Name of the server producing the event.
    ACTIVITYID = 46
    REQUESTID = 47


class ExistingSessionColumns(Enum):
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    DURATION = 5  # Amount of time (in milliseconds) taken by the event.
    CPUTIME = 6  # Amount of CPU time (in milliseconds) used by the event.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTHOSTNAME = 35  # Name of the computer on which the client is running. This data column is populated if the host name is provided by the client.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    APPLICATIONNAME = 37  # Name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SPID = 41  # Server process ID. This uniquely identifies a user session. This directly corresponds to the session GUID used by XML/A.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    REQUESTPROPERTIES = 45  # XMLA request properties.
    ACTIVITYID = 46
    REQUESTID = 47


class SessionInitializeColumns(Enum):
    CURRENTTIME = 2  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    CONNECTIONID = 25  # Unique connection ID.
    DATABASENAME = 28  # Name of the database in which the statement of the user is running.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTHOSTNAME = 35  # Name of the computer on which the client is running. This data column is populated if the host name is provided by the client.
    CLIENTPROCESSID = 36  # The process ID of the client application.
    APPLICATIONNAME = 37  # Name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SPID = 41  # Server process ID. This uniquely identifies a user session. This directly corresponds to the session GUID used by XML/A.
    TEXTDATA = 42  # Text data associated with the event.
    SERVERNAME = 43  # Name of the server producing the event.
    REQUESTPROPERTIES = 45  # XMLA request properties.
    ACTIVITYID = 46
    REQUESTID = 47
