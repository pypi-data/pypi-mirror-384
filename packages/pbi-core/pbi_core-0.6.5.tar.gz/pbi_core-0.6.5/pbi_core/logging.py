import logging
from typing import cast

import structlog


def get_logger(log_level: int = logging.INFO) -> structlog.BoundLogger:
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )
    return cast("structlog.BoundLogger", structlog.get_logger())
