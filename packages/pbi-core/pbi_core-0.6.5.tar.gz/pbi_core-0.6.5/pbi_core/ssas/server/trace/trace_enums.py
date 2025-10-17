# C:\Program Files\Microsoft SQL Server\MSAS16.MSSQLSERVER\OLAP\bin\Resources\1033\tracedefinition.xml
# ruff: noqa: E501
from enum import Enum

from .events.command_events import CommandBeginColumns, CommandEndColumns
from .events.discover_events import DiscoverBeginColumns, DiscoverEndColumns
from .events.discover_server_states import (
    ServerStateDiscoverBeginColumns,
    ServerStateDiscoverDataColumns,
    ServerStateDiscoverEndColumns,
)
from .events.errors_and_warnings import ErrorColumns
from .events.file_load_and_save import (
    FileLoadBeginColumns,
    FileLoadEndColumns,
    FileSaveBeginColumns,
    FileSaveEndColumns,
    PageInBeginColumns,
    PageInEndColumns,
    PageOutBeginColumns,
    PageOutEndColumns,
)
from .events.locks import (
    DeadlockColumns,
    LockAcquiredColumns,
    LockReleasedColumns,
    LockTimeoutColumns,
    LockWaitingColumns,
)
from .events.m_data_provider_events import ExecuteSourceQueryColumns
from .events.notifications import NotificationColumns, UserDefinedColumns
from .events.progress_reports import (
    ProgressReportBeginColumns,
    ProgressReportCurrentColumns,
    ProgressReportEndColumns,
    ProgressReportErrorColumns,
)
from .events.query_events import QueryBeginColumns, QueryEndColumns
from .events.query_processing import (
    AggregateTableRewriteInfoColumns,
    AggregateTableRewriteQueryColumns,
    CalculationEvaluationColumns,
    CalculationEvaluationDetailedInformationColumns,
    DaxExtensionExecutionBeginColumns,
    DaxExtensionExecutionEndColumns,
    DaxExtensionTraceErrorColumns,
    DaxExtensionTraceInfoColumns,
    DaxExtensionTraceVerboseColumns,
    DaxQueryPlanColumns,
    DirectQueryBeginColumns,
    DirectQueryEndColumns,
    ExecutionMetricsColumns,
    QuerySubcubeColumns,
    VertipaqSeQueryBeginColumns,
    VertipaqSeQueryCacheMatchColumns,
    VertipaqSeQueryCacheMissColumns,
    VertipaqSeQueryEndColumns,
)
from .events.resource_governance import (
    WlgroupCpuThrottlingColumns,
    WlgroupExceedsMemoryLimitColumns,
    WlgroupExceedsProcessingLimitColumns,
)
from .events.security_audit import (
    AuditAdminOperationsEventColumns,
    AuditLoginColumns,
    AuditLogoutColumns,
    AuditObjectPermissionEventColumns,
    AuditServerStartsAndStopsColumns,
)
from .events.sessions import ExistingConnectionColumns, ExistingSessionColumns, SessionInitializeColumns


class TraceEvents(Enum):
    AUDIT_LOGIN = 1  # Collects all new connection events since the trace was started, such as when a client requests a connection to a server running an instance of SQL Server.
    AUDIT_LOGOUT = 2  # Collects all new disconnect events since the trace was started, such as when a client issues a disconnect command.
    AUDIT_SERVER_STARTS_AND_STOPS = 4  # Records service shut down, start, and pause activities.

    PROGRESS_REPORT_BEGIN = 5  # Progress report begins.
    PROGRESS_REPORT_END = 6  # Progress report end.
    PROGRESS_REPORT_CURRENT = 7  # Progress report current.
    PROGRESS_REPORT_ERROR = 8  # Progress report error.
    QUERY_BEGIN = 9  # Query begins.
    QUERY_END = 10  # Query end.
    QUERY_SUBCUBE = 11  # Query subcube, for Usage Based Optimization.
    QUERY_SUBCUBE_VERBOSE = 12  # Query subcube with detailed information. This event may have a negative impact on performance when turned on.

    COMMAND_BEGIN = 15  # Command begin.
    COMMAND_END = 16  # Command end.
    ERROR = 17  # Server error.
    AUDIT_OBJECT_PERMISSION_EVENT = 18  # Records object permission changes.
    AUDIT_ADMIN_OPERATIONS_EVENT = 19  # Records server backup/restore/synchronize/attach/detach/imageload/imagesave.

    SERVER_STATE_DISCOVER_BEGIN = 33  # Start of Server State Discover.
    SERVER_STATE_DISCOVER_DATA = 34  # Contents of the Server State Discover Response.
    SERVER_STATE_DISCOVER_END = 35  # End of Server State Discover.
    DISCOVER_BEGIN = 36  # Start of Discover Request.
    DISCOVER_END = 38  # End of Discover Request.
    NOTIFICATION = 39  # Notification event.
    USER_DEFINED = 40  # User defined Event.
    EXISTING_CONNECTION = 41  # Existing user connection.
    EXISTING_SESSION = 42  # Existing session.
    SESSION_INITIALIZE = 43  # Session Initialize.

    DEADLOCK = 50  # Metadata locks deadlock.
    LOCK_TIMEOUT = 51  # Metadata lock timeout.
    LOCK_ACQUIRED = 52  # Lock Acquired
    LOCK_RELEASED = 53  # Lock Released
    LOCK_WAITING = 54  # Lock Waiting
    GET_DATA_FROM_AGGREGATION = 60  # Answer query by getting data from aggregation. This event may have a negative impact on performance when turned on.
    GET_DATA_FROM_CACHE = 61  # Answer query by getting data from one of the caches. This event may have a negative impact on performance when turned on.

    QUERY_CUBE_BEGIN = 70  # Query cube begin.
    QUERY_CUBE_END = 71  # Query cube end.
    CALCULATE_NON_EMPTY_BEGIN = 72  # Calculate non empty begin.
    CALCULATE_NON_EMPTY_CURRENT = 73  # Calculate non empty current.
    CALCULATE_NON_EMPTY_END = 74  # Calculate non empty end.
    SERIALIZE_RESULTS_BEGIN = 75  # Serialize results begin.
    SERIALIZE_RESULTS_CURRENT = 76  # Serialize results current.
    SERIALIZE_RESULTS_END = 77  # Serialize results end.
    EXECUTE_MDX_SCRIPT_BEGIN = 78  # Execute MDX script begin.
    EXECUTE_MDX_SCRIPT_CURRENT = 79  # Execute MDX script current. Deprecated.
    EXECUTE_MDX_SCRIPT_END = 80  # Execute MDX script end.
    QUERY_DIMENSION = 81  # Query dimension.
    VERTIPAQ_SE_QUERY_BEGIN = 82  # VertiPaq SE query
    VERTIPAQ_SE_QUERY_END = 83  # VertiPaq SE query
    RESOURCE_USAGE = 84  # Reports reads, writes, cpu usage after end of commands and queries.
    VERTIPAQ_SE_QUERY_CACHE_MATCH = 85  # VertiPaq SE query cache use
    VERTIPAQ_SE_QUERY_CACHE_MISS = 86  # VertiPaq SE Query Cache Miss

    FILE_LOAD_BEGIN = 90  # File Load Begin.
    FILE_LOAD_END = 91  # File Load End.
    FILE_SAVE_BEGIN = 92  # File Save Begin.
    FILE_SAVE_END = 93  # File Save End
    PAGEOUT_BEGIN = 94  # PageOut Begin.
    PAGEOUT_END = 95  # PageOut End
    PAGEIN_BEGIN = 96  # PageIn Begin.
    PAGEIN_END = 97  # PageIn End
    DIRECT_QUERY_BEGIN = 98  # Direct Query Begin.
    DIRECT_QUERY_END = 99  # Direct Query End.

    CALCULATION_EVALUATION = 110  # Information about the evaluation of calculations. This event will have a negative impact on performance when turned on.
    CALCULATION_EVALUATION_DETAILED_INFORMATION = 111  # Detailed information about the evaluation of calculations. This event will have a negative impact on performance when turned on.
    DAX_QUERY_PLAN = 112  # DAX logical/physical plan tree for VertiPaq and DirectQuery modes.
    WLGROUP_CPU_THROTTLING = 113  # Workload Group is throttled on CPU usage
    WLGROUP_EXCEEDS_MEMORY_LIMIT = 114  # Workload group exceeds the memory limit
    WLGROUP_EXCEEDS_PROCESSING_LIMIT = 115  # Workload group exceeds the processing limit
    DAX_EXTENSION_EXECUTION_BEGIN = 120  # DAX extension function execution begin event.
    DAX_EXTENSION_EXECUTION_END = 121  # DAX extension function execution end event.
    DAX_EXTENSION_TRACE_ERROR = 122  # DAX extension function error trace event directly traced by extension authors.
    DAX_EXTENSION_TRACE_INFO = (
        123  # DAX extension function informational/telemetry trace event directly traced by extension authors.
    )
    DAX_EXTENSION_TRACE_VERBOSE = (
        124  # DAX extension function verbose trace event directly traced by extension authors.
    )
    EXECUTE_SOURCE_QUERY = 130  # Collection of all queries that are executed against the data source
    AGGREGATE_TABLE_REWRITE_QUERY = 131  # A query was rewritten according to available aggregate tables
    AGGREGATE_TABLE_REWRITE_INFO = 132  # Aggregate Table Rewrite Info

    JOB_GRAPH = 134  # Collection of Job Graph related events.
    EXECUTION_METRICS = 136

    def get_columns(self) -> type[Enum]:
        return event_column_mapping[self]


event_column_mapping: dict[TraceEvents, type[Enum]] = {
    TraceEvents.AGGREGATE_TABLE_REWRITE_INFO: AggregateTableRewriteInfoColumns,
    TraceEvents.AGGREGATE_TABLE_REWRITE_QUERY: AggregateTableRewriteQueryColumns,
    TraceEvents.AUDIT_ADMIN_OPERATIONS_EVENT: AuditAdminOperationsEventColumns,
    TraceEvents.AUDIT_LOGIN: AuditLoginColumns,
    TraceEvents.AUDIT_LOGOUT: AuditLogoutColumns,
    TraceEvents.AUDIT_OBJECT_PERMISSION_EVENT: AuditObjectPermissionEventColumns,
    TraceEvents.AUDIT_SERVER_STARTS_AND_STOPS: AuditServerStartsAndStopsColumns,
    TraceEvents.CALCULATION_EVALUATION: CalculationEvaluationColumns,
    TraceEvents.CALCULATION_EVALUATION_DETAILED_INFORMATION: CalculationEvaluationDetailedInformationColumns,
    TraceEvents.COMMAND_BEGIN: CommandBeginColumns,
    TraceEvents.COMMAND_END: CommandEndColumns,
    TraceEvents.DAX_EXTENSION_EXECUTION_BEGIN: DaxExtensionExecutionBeginColumns,
    TraceEvents.DAX_EXTENSION_EXECUTION_END: DaxExtensionExecutionEndColumns,
    TraceEvents.DAX_EXTENSION_TRACE_ERROR: DaxExtensionTraceErrorColumns,
    TraceEvents.DAX_EXTENSION_TRACE_INFO: DaxExtensionTraceInfoColumns,
    TraceEvents.DAX_EXTENSION_TRACE_VERBOSE: DaxExtensionTraceVerboseColumns,
    TraceEvents.DIRECT_QUERY_BEGIN: DirectQueryBeginColumns,
    TraceEvents.DIRECT_QUERY_END: DirectQueryEndColumns,
    TraceEvents.DAX_QUERY_PLAN: DaxQueryPlanColumns,
    TraceEvents.DEADLOCK: DeadlockColumns,
    TraceEvents.DISCOVER_BEGIN: DiscoverBeginColumns,
    TraceEvents.DISCOVER_END: DiscoverEndColumns,
    TraceEvents.ERROR: ErrorColumns,
    TraceEvents.EXISTING_CONNECTION: ExistingConnectionColumns,
    TraceEvents.EXISTING_SESSION: ExistingSessionColumns,
    TraceEvents.EXECUTE_SOURCE_QUERY: ExecuteSourceQueryColumns,
    TraceEvents.EXECUTION_METRICS: ExecutionMetricsColumns,
    TraceEvents.FILE_SAVE_BEGIN: FileSaveBeginColumns,
    TraceEvents.FILE_SAVE_END: FileSaveEndColumns,
    TraceEvents.FILE_LOAD_BEGIN: FileLoadBeginColumns,
    TraceEvents.FILE_LOAD_END: FileLoadEndColumns,
    TraceEvents.LOCK_ACQUIRED: LockAcquiredColumns,
    TraceEvents.LOCK_RELEASED: LockReleasedColumns,
    TraceEvents.LOCK_TIMEOUT: LockTimeoutColumns,
    TraceEvents.LOCK_WAITING: LockWaitingColumns,
    TraceEvents.NOTIFICATION: NotificationColumns,
    TraceEvents.PAGEIN_BEGIN: PageInBeginColumns,
    TraceEvents.PAGEIN_END: PageInEndColumns,
    TraceEvents.PAGEOUT_BEGIN: PageOutBeginColumns,
    TraceEvents.PAGEOUT_END: PageOutEndColumns,
    TraceEvents.PROGRESS_REPORT_BEGIN: ProgressReportBeginColumns,
    TraceEvents.PROGRESS_REPORT_CURRENT: ProgressReportCurrentColumns,
    TraceEvents.PROGRESS_REPORT_END: ProgressReportEndColumns,
    TraceEvents.PROGRESS_REPORT_ERROR: ProgressReportErrorColumns,
    TraceEvents.QUERY_BEGIN: QueryBeginColumns,
    TraceEvents.QUERY_END: QueryEndColumns,
    TraceEvents.QUERY_SUBCUBE: QuerySubcubeColumns,
    TraceEvents.SERVER_STATE_DISCOVER_BEGIN: ServerStateDiscoverBeginColumns,
    TraceEvents.SERVER_STATE_DISCOVER_DATA: ServerStateDiscoverDataColumns,
    TraceEvents.SERVER_STATE_DISCOVER_END: ServerStateDiscoverEndColumns,
    TraceEvents.SESSION_INITIALIZE: SessionInitializeColumns,
    TraceEvents.USER_DEFINED: UserDefinedColumns,
    TraceEvents.VERTIPAQ_SE_QUERY_BEGIN: VertipaqSeQueryBeginColumns,
    TraceEvents.VERTIPAQ_SE_QUERY_END: VertipaqSeQueryEndColumns,
    TraceEvents.VERTIPAQ_SE_QUERY_CACHE_MATCH: VertipaqSeQueryCacheMatchColumns,
    TraceEvents.VERTIPAQ_SE_QUERY_CACHE_MISS: VertipaqSeQueryCacheMissColumns,
    TraceEvents.WLGROUP_CPU_THROTTLING: WlgroupCpuThrottlingColumns,
    TraceEvents.WLGROUP_EXCEEDS_MEMORY_LIMIT: WlgroupExceedsMemoryLimitColumns,
    TraceEvents.WLGROUP_EXCEEDS_PROCESSING_LIMIT: WlgroupExceedsProcessingLimitColumns,
}
