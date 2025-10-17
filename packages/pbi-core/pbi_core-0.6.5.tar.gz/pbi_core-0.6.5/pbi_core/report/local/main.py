from typing import TYPE_CHECKING, Literal, overload

from pbi_core.logging import get_logger
from pbi_core.report.base.main import BaseReport
from pbi_core.ssas.model_tables import Column, Measure
from pbi_core.ssas.server import LocalTabularModel
from pbi_core.static_files import StaticFiles

from .ssas import LocalSsasReport
from .static_files import LocalStaticReport

logger = get_logger()

if TYPE_CHECKING:
    from _typeshed import StrPath

    from pbi_core.ssas.model_tables import Table


class LocalReport(LocalSsasReport, LocalStaticReport, BaseReport):  # pyright: ignore[reportIncompatibleVariableOverride]
    """An instance of a PowerBI report from a local PBIX file.

    Args:
        static_files (StaticElements): An instance of all the static files (except DataModel) in the PBIX file

    Examples:
        ```python
        from pbi_core import LocalReport

        report = LocalReport.load_pbix("example.pbix")
        report.save_pbix("example_out.pbix")
        ```

    """

    def __init__(self, ssas: LocalTabularModel, static_files: StaticFiles) -> None:
        self.ssas = ssas
        self.static_files = static_files

    @overload
    @staticmethod
    def load_pbix(
        path: "StrPath",
        *,
        kill_ssas_on_exit: bool = True,
        load_ssas: Literal[True] = True,
        load_static_files: Literal[True] = True,
    ) -> "LocalReport": ...

    @overload
    @staticmethod
    def load_pbix(  # pyright: ignore[reportOverlappingOverload]
        path: "StrPath",
        *,
        kill_ssas_on_exit: bool = True,
        load_ssas: Literal[False] = False,
        load_static_files: Literal[True] = True,
    ) -> "LocalStaticReport": ...

    @overload
    @staticmethod
    def load_pbix(
        path: "StrPath",
        *,
        kill_ssas_on_exit: bool = True,
        load_ssas: Literal[True] = True,
        load_static_files: Literal[False] = False,
    ) -> "LocalSsasReport": ...

    @overload
    @staticmethod
    def load_pbix(
        path: "StrPath",
        *,
        kill_ssas_on_exit: bool = True,
        load_ssas: bool = True,
        load_static_files: bool = False,
    ) -> "LocalReport": ...

    # If the above overloads are not used, this will be the default implementation, assuming both sides are loaded

    @staticmethod
    def load_pbix(  # pyright: ignore[reportIncompatibleMethodOverride]
        path: "StrPath",
        *,
        kill_ssas_on_exit: bool = True,
        load_ssas: bool = True,
        load_static_files: bool = True,
    ) -> "LocalReport | LocalSsasReport | LocalStaticReport":
        """Creates a ``LocalReport`` instance from a PBIX file.

        Args:
            path (StrPath): The absolute or local path to the PBIX report
            kill_ssas_on_exit (bool, optional): The LocalReport object depends on a ``msmdsrv.exe`` process that is
                independent of the Python session process. If this function creates a new ``msmdsrv.exe`` instance
                and kill_ssas_on_exit is true, the process will be killed on exit.
            load_ssas (bool, optional): Indicates if the report should load any objects within the report.ssas
                attribute
            load_static_files (bool, optional): Indicates if the report should load any objects within the
                report.static_files attribute

        Raises:
            ValueError: Occurs when neither the load_ssas nor load_static_files parameters are true,
                so there's nothing to load.

        Examples:
            ```python

               from pbi_core import LocalReport

               report = LocalReport.load_pbix("example.pbix")
            ```

        Returns:
                LocalReport: the local PBIX class

        """
        logger.info(
            "Loading PBIX report",
            path=path,
            load_ssas=load_ssas,
            load_static_files=load_static_files,
        )
        if load_ssas & load_static_files:
            ssas_content = LocalSsasReport.load_pbix(path, kill_ssas_on_exit=kill_ssas_on_exit)
            static_content = LocalStaticReport.load_pbix(path)
            logger.info("Loaded PBIX report", components="ssas+static")
            return LocalReport(ssas=ssas_content.ssas, static_files=static_content.static_files)
        if load_ssas:
            logger.info("Loaded PBIX report", components="ssas")
            return LocalSsasReport.load_pbix(path, kill_ssas_on_exit=kill_ssas_on_exit)
        if load_static_files:
            logger.info("Loaded PBIX report", components="static")
            return LocalStaticReport.load_pbix(path)
        msg = "At least one of load_ssas or load_static_files must be True"
        raise ValueError(msg)

    def save_pbix(self, path: "StrPath", *, sync_ssas_changes: bool = True) -> None:
        """Creates a new PBIX with the information in this class to the given path.

        Examples:
            ```python

               from pbi_core import LocalReport

               report = LocalReport.load_pbix("example.pbix")
            ```
               report.save_pbix("example_out.pbix")

        Args:
            path (StrPath): the path (relative or absolute) to save the PBIX to
            sync_ssas_changes (bool, optional): whether to sync changes made in the SSAS model back to the PBIX file

        """
        logger.info("Saving PBIX report", path=path, sync_ssas_changes=sync_ssas_changes)
        # Dev note: DO NOT call save_pbix of LocalSsasReport or LocalStaticReport, as they are implemented assuming the
        # other doesn't exist, causing changes to be overwritten by them copying the source file
        if sync_ssas_changes:
            self.ssas.sync_to()
        self.ssas.save_pbix(path)
        self.static_files.save_pbix(path)
        logger.info("Saved PBIX report", path=path)

    def cleanse_ssas_model(self) -> None:
        """Removes all unused tables, columns, and measures in an SSAS model.

        1. Uses the layout to identify all Measures and Columns being used by the report visuals and filters.
        2. Uses SSAS relationships to identify additional columns and tables used for cross-table filtering.
        3. Traces calculation dependencies (on measures and calculated columns) to identify measures and columns used
             to create report fields
        4. Removes any measure/column that is:
            1. Not in results of 1-3
            2. Not part of a system table
        5. Removes any table that has no column/measure used in the report and no active relationship with a reporting
            table
        """
        report_references = self.static_files.layout.get_ssas_elements()
        model_values = (
            [x.to_model(self.ssas) for x in report_references]
            + [relationship.to_column() for relationship in self.ssas.relationships]
            + [relationship.from_column() for relationship in self.ssas.relationships]
        )
        ret: list[Measure | Column] = []
        for val in model_values:
            ret.append(val)
            ret.extend(val.parents(recursive=True))

        used_tables = {x.table() for x in ret}
        used_measures = {
            x
            for x in ret
            if isinstance(
                x,
                Measure,
            )
        }
        used_columns = {x for x in ret if isinstance(x, Column)}

        # In the examples I've seen, there's a table named "DateTableTemplate_<UUID>" that doesn't seem used,
        # but breaks the system when removed
        tables_to_drop = {t for t in self.ssas.tables if t not in used_tables and not t.is_private}
        columns_to_drop = {
            c
            for c in self.ssas.columns
            if c not in used_columns
            and not c.table().name.startswith("DateTableTemplate")
            and c.table() not in tables_to_drop
        }
        logger.info(
            "Dropping unused SSAS elements",
            tables_to_drop=len(tables_to_drop),
            columns_to_drop=len(columns_to_drop),
        )
        affected_tables: dict[Table, list[Column]] = {}
        for c in columns_to_drop:
            t = c.table()
            if t not in tables_to_drop:
                affected_tables.setdefault(t, []).append(c)

        measures_to_drop = {m for m in self.ssas.measures if m not in used_measures}
        for t in tables_to_drop:
            t.delete()
        for c in columns_to_drop:
            c.delete()
        for m in measures_to_drop:
            m.delete()
        for affected_table, table_columns_to_drop in affected_tables.items():
            for partition in affected_table.partitions():
                partition.remove_columns(table_columns_to_drop)
        logger.info(
            "SSAS model cleansed",
            tables_dropped=len(tables_to_drop),
            columns_dropped=len(columns_to_drop),
            measures_dropped=len(measures_to_drop),
        )
