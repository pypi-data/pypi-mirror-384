from enum import Enum


class QueryBeginColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    EVENTSUBCLASS = 1  # Event Subclass provides additional information about each event class. 0: MDXQuery 1: DMXQuery 2: SQLQuery 3: DAXQuery
    CURRENTTIME = 2  # Contains the current time of the event, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Contains the time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    CONNECTIONID = 25  # Contains the unique connection ID associated with the query event.
    DATABASENAME = 28  # Contains the name of the database in which the query is running.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTPROCESSID = 36  # Contains the process ID of the client application.
    APPLICATIONNAME = 37  # Contains the name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    SESSIONID = 39  # Contains the session unique ID of the XMLA request.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SPID = 41  # Contains the server process ID (SPID) that uniquely identifies the user session associated with the query event. The SPID directly corresponds to the session GUID used by XMLA.
    TEXTDATA = 42  # Contains the text data associated with the query event.
    SERVERNAME = 43  # Contains the name of the instance on which the query event occurred.
    REQUESTPARAMETERS = (
        44  # Contains the parameters for parameterized queries and commands associated with the query event.
    )
    REQUESTPROPERTIES = 45  # Contains the properties of the XMLA request.
    ACTIVITYID = 46
    REQUESTID = 47


class QueryEndColumns(Enum):
    EVENTCLASS = 0  # Event Class is used to categorize events.
    EVENTSUBCLASS = 1  # Event Subclass provides additional information about each event class. 0: MDXQuery 1: DMXQuery 2: SQLQuery 3: DAXQuery
    CURRENTTIME = 2  # Contains the current time of the event, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    STARTTIME = 3  # Contains the time at which the event started, when available. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    ENDTIME = 4  # Contains the time at which the event ended. This column is not populated for starting event classes, such as SQL:BatchStarting or SP:Starting. For filtering, expected formats are 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'.
    DURATION = 5  # Contains the amount of elapsed time (in milliseconds) taken by the event.
    CPUTIME = 6  # Contains the amount of CPU time (in milliseconds) used by the event.
    SEVERITY = 22  # Contains the severity level of an exception associated with the query event. Values are: 0 = Success 1 = Informational 2 = Warning 3 = Error
    SUCCESS = 23  # Contains the success or failure of the query event. Values are: 0 = Failure 1 = Success
    ERROR = 24  # Contains the error number of any error associated with the query event.
    CONNECTIONID = 25  # Contains the unique connection ID associated with the query event.
    DATABASENAME = 28  # Contains the name of the database in which the query is running.
    NTUSERNAME = 32  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service  Principal Name (SPN) (appid@tenantid) - Power BI Service Account  (Power BI Service) - Power BI Service on behalf of a UPN or SPN (Power BI Service (UPN/SPN))
    NTDOMAINNAME = 33  # Contains the domain name associated with the user account that triggered the command event.  - Windows domain name for Windows user accounts - AzureAD for Microsoft Entra accounts - NT AUTHORITY accounts without a Windows domain name, such as the Power BI service
    CLIENTPROCESSID = 36  # Contains the process ID of the client application.
    APPLICATIONNAME = 37  # Contains the name of the client application that created the connection to the server. This column is populated with the values passed by the application rather than the displayed name of the program.
    SESSIONID = 39  # Contains the session unique ID of the XMLA request.
    NTCANONICALUSERNAME = 40  # Contains the user name associated with the command event. Depending on the environment, the user name is in the following form: - Windows user account (DOMAIN\UserName) - User Principal Name (UPN) (username@domain.com) - Service Principal Name (SPN) (appid@tenantid) - Power BI Service Account (Power BI Service)
    SPID = 41  # Contains the server process ID (SPID) that uniquely identifies the user session associated with the query event. The SPID directly corresponds to the session GUID used by XMLA.
    TEXTDATA = 42  # Contains the text data associated with the query event.
    SERVERNAME = 43  # Contains the name of the instance on which the query event occurred.
    ACTIVITYID = 46
    REQUESTID = 47
