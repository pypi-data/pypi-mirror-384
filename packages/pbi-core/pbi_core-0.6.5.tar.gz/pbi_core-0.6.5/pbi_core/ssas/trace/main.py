from typing import TYPE_CHECKING

from .performance_trace import Performance

if TYPE_CHECKING:
    from pbi_core.ssas.server.tabular_model.tabular_model import BaseTabularModel


def get_performance(model: "BaseTabularModel", commands: list[str], *, clear_cache: bool = False) -> list[Performance]:
    """Calculates performance of a DAX query using a Trace.

    Args:
        model (BaseTabularModel): the SSAS instance the DAX should be run against
        commands (list[str]): A list of DAX queries to run against the SSAS model
        clear_cache (bool): Whether to clear the SSAS cache before running the queries.
            Useful to test cold start times for users

    Returns:
        Performance: contains memory and time usage of the DAX query


    """
    with model.get_performance_trace() as perf_trace:
        return perf_trace.get_performance(commands, clear_cache=clear_cache)
