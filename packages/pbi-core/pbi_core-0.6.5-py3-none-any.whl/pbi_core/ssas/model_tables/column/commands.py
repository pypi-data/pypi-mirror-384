from bs4 import BeautifulSoup
from structlog import BoundLogger

from pbi_core.logging import get_logger

from .dependencies import DependencyMixin

logger: BoundLogger = get_logger()


class CommandMixin(DependencyMixin):
    def delete(
        self,
        *,
        remote_from_partition_query: bool = False,
    ) -> list[BeautifulSoup] | None:
        """Removes column from the SSAS model.

        Args:
            remote_from_partition_query (bool): If this is True, updates the PowerQuery to drop the column so it doesn't repopulate on data refresh. If the column is calculated (meaning it is not part of the PowerQuery), an info record is logged and nothing else happens.

        """  # noqa: E501
        rets: list[BeautifulSoup] = []
        if remote_from_partition_query:
            if self._column_type() == "CALC_COLUMN":
                logger.info("Column is calculated, there is nothing to remove from the PowerQuery", column=self)
                return None
            name = self.explicit_name
            if name is None:
                logger.warning("Column has no name to include in the PowerQuery", column=self)
                return None
            rets.extend(partition.remove_columns([name]) for partition in self.table().partitions())
        rets.append(super().delete())  # pyright: ignore[reportAttributeAccessIssue]
        return rets
