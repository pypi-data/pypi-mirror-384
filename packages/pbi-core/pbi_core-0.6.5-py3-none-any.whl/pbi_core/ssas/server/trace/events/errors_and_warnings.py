from enum import Enum


class ErrorColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    STARTTIME = 3  # Contains the time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    SESSIONTYPE = 8  # Contains the type of the entity that caused the error.
    SEVERITY = 22  # Contains the severity level of an exception associated with the error event. Values are: 0 = Success 1 = Informational 2 = Warning 3 = Error
    SUCCESS = 23  # Contains the success or failure of the error event. Values are: 0 = Failure 1 = Success
    ERROR = 24  # Contains the error number of any error associated with the error event.
    CONNECTIONID = 25  # Contains the unique connection ID associated with the error event.
    DATABASENAME = 28  # Contains the name of the Analysis Services instance on which the error event occurred.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTHOSTNAME = 35  # Contains the name of the computer on which the client is running. This data column is populated if the host name is provided by the client.
    CLIENTPROCESSID = 36  # Contains the process ID of the client application.
    APPLICATIONNAME = 37  # Contains the name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    SESSIONID = 39  # Contains the server process ID (SPID) that uniquely identifies the user session associated with the error event. The SPID directly corresponds to the session GUID used by XML for Analysis (XMLA).
    SPID = 41  # Contains the server process ID (SPID) that uniquely identifies the user session associated with the error event. The SPID directly corresponds to the session GUID used by XML for Analysis (XMLA).
    TEXTDATA = 42  # Contains the text data associated with the error event.
    SERVERNAME = (
        43  # Contains the name of the server running Analysis Services instance on which the error event occurred.
    )
    ACTIVITYID = 46
    REQUESTID = 47
