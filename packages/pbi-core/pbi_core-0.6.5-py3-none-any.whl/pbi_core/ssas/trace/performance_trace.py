import datetime
import json
import math
import textwrap
import threading
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any

import jinja2
from attrs import frozen
from pbi_pyadomd import Connection, Reader

from pbi_core.logging import get_logger
from pbi_core.ssas.server.trace.trace_enums import TraceEvents

if TYPE_CHECKING:
    from pbi_core.ssas.server.tabular_model.tabular_model import BaseTabularModel

logger = get_logger()
TRACE_DIR = Path(__file__).parent / "templates"
TRACE_TEMPLATES: dict[str, jinja2.Template] = {
    f.name: jinja2.Template(f.read_text()) for f in TRACE_DIR.iterdir() if f.is_file()
}

TRACE_DEFAULT_EVENTS = (
    TraceEvents.DISCOVER_BEGIN,
    TraceEvents.COMMAND_BEGIN,
    TraceEvents.QUERY_END,
    TraceEvents.QUERY_SUBCUBE,
    TraceEvents.VERTIPAQ_SE_QUERY_BEGIN,
    TraceEvents.VERTIPAQ_SE_QUERY_END,
    TraceEvents.VERTIPAQ_SE_QUERY_CACHE_MATCH,
    TraceEvents.VERTIPAQ_SE_QUERY_CACHE_MISS,
    TraceEvents.AGGREGATE_TABLE_REWRITE_QUERY,
    TraceEvents.DIRECT_QUERY_END,
    TraceEvents.QUERY_BEGIN,
    TraceEvents.EXECUTION_METRICS,
)


def pretty_size(n: int) -> str:
    """Convert a number of bytes into a human-readable format."""
    units = ["B"] + [f"{p}iB" for p in "KMGTPEZY"]

    prefix = int(math.log(max(n, 1), 1024))
    prefix = min(prefix, len(units) - 1)
    pretty_n = round(n / 1024**prefix, 1)
    return f"{pretty_n} {units[prefix]}"


@frozen()
class ThreadResult:
    command: str
    rows_returned: int
    error: Exception | None = None

    def get_performance(self, trace_records: list[dict[str, Any]]) -> "Performance":
        event_info = {}
        for record in trace_records:
            event_info[record["EventClass"]] = record

        command_text = event_info["QUERY_END"]["TextData"]
        server_name = event_info["QUERY_END"]["ServerName"]
        database_name = event_info["QUERY_END"]["DatabaseName"]

        execution_metrics = json.loads(event_info["EXECUTION_METRICS"]["TextData"])
        start_datetime = datetime.datetime.strptime(execution_metrics["timeStart"], "%Y-%m-%dT%H:%M:%S.%f%z")
        end_datetime = datetime.datetime.strptime(execution_metrics["timeEnd"], "%Y-%m-%dT%H:%M:%S.%f%z")
        total_duration = execution_metrics["durationMs"]
        total_cpu_time = execution_metrics["totalCpuTimeMs"]
        query_cpu_time = execution_metrics["queryProcessingCpuTimeMs"]
        # Trivial DAX commands like EVALUATE {1} don't have vertipaqJobCpuTimeMs since they don't touch any tables
        vertipaq_cpu_time = execution_metrics.get("vertipaqJobCpuTimeMs", 0)
        execution_delay = execution_metrics["executionDelayMs"]
        approximate_peak_consumption_kb = execution_metrics["approximatePeakMemConsumptionKB"]

        for record in trace_records:
            if record.get("EventClass") == "QUERY_END":
                return Performance(
                    command_text=command_text,
                    server_name=server_name,
                    database_name=database_name,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    total_duration=total_duration,
                    total_cpu_time=total_cpu_time,
                    query_cpu_time=query_cpu_time,
                    vertipaq_cpu_time=vertipaq_cpu_time,
                    execution_delay=execution_delay,
                    approximate_peak_consumption_kb=approximate_peak_consumption_kb,
                    rows_returned=self.rows_returned,
                    full_trace_log=trace_records,
                )
        msg = f"Command '{self.command}' not found in trace records."
        raise ValueError(msg)


@frozen()
class Performance:
    command_text: str
    """The text of the command being executed"""
    server_name: str
    """The name of the server where the command was executed"""
    database_name: str
    """The name of the database where the command was executed

    Note:
        When the pbyx was loaded by this library, the database name will match the name of the pbix file."""
    start_datetime: datetime.datetime
    """When the query started"""
    end_datetime: datetime.datetime
    """When the query ended"""
    query_cpu_time: int
    """Total Query CPU Time (i.e. the sum of the time each core involved was used)"""
    total_duration: int
    """Total duration is the total time in milliseconds"""
    total_cpu_time: int
    """Total CPU Time (i.e. the sum of the time each core involved was used)"""
    vertipaq_cpu_time: int
    """CPU Time spent by the vertipaq engine"""
    execution_delay: int
    """Delay between the query start and processing due to other competing queries"""
    approximate_peak_consumption_kb: int
    """The max memory used by the query throughout its execution"""
    rows_returned: int
    """The number of rows returned by the query"""
    full_trace_log: list[dict[str, Any]]

    def __repr__(self) -> str:
        total_duration = round(self.total_duration / 1000, 2)
        total_cpu_time = round(self.total_cpu_time / 1000, 2)
        approximate_peak_consumption = pretty_size(self.approximate_peak_consumption_kb * 1024)
        return f"Performance(rows={self.rows_returned}, total_duration={total_duration}, total_cpu_time={total_cpu_time}, peak_consumption={approximate_peak_consumption}"  # noqa: E501

    def pprint(self) -> str:
        """Pretty print the performance metrics."""
        command_text = textwrap.indent(self.command_text, " " * 8)
        return f"""Performance(
    Command:

{command_text}

    Start Time: {self.start_datetime.isoformat()}
    End Time: {self.end_datetime.isoformat()}
    Total Duration: {self.total_duration} ms
    Total CPU Time: {self.total_cpu_time} ms
    Query CPU Time: {self.query_cpu_time} ms
    Vertipaq CPU Time: {self.vertipaq_cpu_time} ms
    Execution Delay: {self.execution_delay} ms
    Approximate Peak Consumption: {pretty_size(self.approximate_peak_consumption_kb * 1024)}
    Rows Returned: {self.rows_returned}
)"""


class SubscriberState(Enum):
    INITIALIZED = "initialized"
    SUBSCRIBED = "subscribed"


class Subscriber:
    _state: SubscriberState = SubscriberState.INITIALIZED
    """The state is only used to manage the _pinger method"""

    trace_records: dict[str, list[dict[str, Any]]]
    reader: Reader

    def __init__(self, subscription_create_command: str, conn: Connection, events: Iterable[TraceEvents]) -> None:
        """Initializes the Subscriber in Python and SSAS.

        Note:
            Without the self.pinger on a separate doing a trivial ping, the subscription occasionally
            (10% in tests) takes forever (1-5 minutes vs 1-2 seconds) to be created. Although hopefully
            we solve the root cause, this workaround appears to solve the issue for now.

        """
        ping_thread = threading.Thread(target=self.pinger, args=(conn.clone(),), daemon=True)
        ping_thread.start()
        self.reader = conn.execute_dax(
            subscription_create_command,
        )  # occasionally seems to take forever (1-5 minutes vs 1-2 seconds)
        self._state = SubscriberState.SUBSCRIBED

        self.events = events
        self.trace_records = {}
        self.command_request_ids: dict[str, str] = {}
        self.thread = threading.Thread(target=self.poll_cursor, daemon=True)
        self.thread.start()

    def pinger(self, conn: Connection) -> None:
        """Only used to remind the SSAS that there's a Subscription waiting to be created."""
        conn.open()
        while self._state != SubscriberState.SUBSCRIBED:
            time.sleep(1)
            conn.execute_dax(
                "EVALUATE {1}",
            ).close()  # simple ping to keep the connection alive. We don't actually care about the output
        conn.close()

    def poll_cursor(self) -> None:
        event_mapping = {e.value: e.name for e in self.events}
        for record in self.reader.fetch_stream():
            if "EventClass" in record:
                record["EventClass"] = event_mapping[record["EventClass"]]
            self.trace_records.setdefault(record["RequestID"], []).append(record)
            if "TextData" in record:
                self.command_request_ids[record["TextData"]] = record["RequestID"]

    def kill_polling(self) -> None:
        if self.thread.is_alive():
            self.thread.join(timeout=1)

    def __repr__(self) -> str:
        return f"Subscriber(records={len(self.trace_records)})"


class PerformanceTrace:
    """Context manager to manage the lifecycle of a trace in SSAS.

    Once initialized, this class can be used to run DAX commands and get performance metrics on them.
    """

    events: Iterable[TraceEvents]
    """A list of events to capture in the trace. Defaults to TRACE_DEFAULT_EVENTS"""
    db: "BaseTabularModel"
    trace_create_command: str
    subscription_create_command: str
    trace_delete_command: str
    clear_cache_command: str

    def __init__(
        self,
        db: "BaseTabularModel",
        events: Iterable[TraceEvents] = TRACE_DEFAULT_EVENTS,
    ) -> None:
        self.events = events
        self.db: BaseTabularModel = db

        next_day = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        trace_name = f"pbi_core_{next_day.replace(':', '_')}"
        subscription_name = f"pbi_core_subscription_{next_day.replace(':', '_')}"
        self.trace_create_command = TRACE_TEMPLATES["trace_create.xml"].render(
            trace_name=trace_name,
            stop_time=next_day,
            events=self.events,
        )
        self.subscription_create_command = TRACE_TEMPLATES["subscription_create.xml"].render(
            trace_name=trace_name,
            subscription_name=subscription_name,
        )
        self.trace_delete_command = TRACE_TEMPLATES["trace_delete.xml"].render(
            trace_name=trace_name,
        )
        self.clear_cache_command = TRACE_TEMPLATES["clear_cache.xml"].render(database_name=self.db.db_name)

    def __enter__(self) -> "PerformanceTrace":
        return self.initialize_tracing()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.terminate_tracing()

    def initialize_tracing(self) -> "PerformanceTrace":
        """Creates the SSAS trace and starts the subscriber thread to poll for records.

        Note:
            Currently, the subscriber also creates a thread that does a trivial ping every second to keep
            the subscription stream alive. See the Subscription class for more details.

        """
        logger.info("Beginning trace")
        self.db.server.query_xml(self.trace_create_command)
        self.subscriber = Subscriber(
            self.subscription_create_command,
            self.get_conn(),
            self.events,
        )
        return self

    def terminate_tracing(self) -> None:
        """Deletes the SSAS trace and stops the subscriber thread from polling."""
        logger.info("Terminating trace")
        with self.db.server.conn(db_name=self.db.db_name) as conn:
            conn.execute_xml(self.trace_delete_command)
        self.subscriber.kill_polling()

    @staticmethod
    def _normalize_command(command: str) -> str:
        """Normalize commands to ensure that we can match them to trace records."""
        return command.replace("\r\n", "\n").strip()

    def get_performance(self, commands: str | list[str], *, clear_cache: bool = False) -> list[Performance]:
        def thread_func(command: str) -> ThreadResult:
            try:
                with self.get_conn() as conn:
                    reader = conn.execute_dax(command)
                    # The limit of 500 is to mimic the behavior of PowerBI, which returns by defult 500 rows
                    rows_returned = len(reader.fetch_many(limit=500))

                    # See note in Reader.fetch_stream() documentation for why we do this
                    reader.close()

            except ValueError as e:
                return ThreadResult(
                    command=command,
                    rows_returned=-1,
                    error=e,
                )
            return ThreadResult(
                command=command,
                rows_returned=rows_returned,
            )

        if clear_cache:
            logger.info("Clearing cache before performance testing")
            with self.db.server.conn(db_name=self.db.db_name) as conn:
                conn.execute_xml(self.clear_cache_command)
        if isinstance(commands, str):
            commands = [commands]
        commands = [self._normalize_command(cmd) for cmd in commands]

        with ThreadPoolExecutor() as dax_executor:
            logger.info("Running DAX commands")
            command_results = list(dax_executor.map(thread_func, commands))

        missing_subscription_records = command_results
        for _ in range(5):
            # Testing for 15 seconds to check that all commands have an entry in the trace
            new_missing_subscription_records = []
            for command in missing_subscription_records:
                request_id = self.subscriber.command_request_ids.get(command.command)
                if request_id is None:
                    new_missing_subscription_records.append(command)
                    continue
                command_events = self.subscriber.trace_records.get(request_id, [])
                if not any(x["EventClass"] == "QUERY_END" for x in command_events):
                    new_missing_subscription_records.append(command)

            if not new_missing_subscription_records:
                break
            time.sleep(1)
            missing_subscription_records = new_missing_subscription_records
        else:
            missing_commands = ", ".join(cmd.command for cmd in missing_subscription_records)
            msg = f"Some commands did not have trace records: {missing_commands}"
            raise ValueError(msg)

        return [
            command_result.get_performance(
                self.subscriber.trace_records[self.subscriber.command_request_ids[command_result.command]],
            )
            for command_result in command_results
        ]

    def get_conn(self) -> Connection:
        return self.db.server.conn(db_name=self.db.db_name).open()
