import logging
import sys
from typing import Any

import structlog

from stratum_libs.config import settings


def _configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
    )


def get_logger(**initial_values: Any) -> structlog.BoundLogger:
    return structlog.get_logger(service_name=settings.SERVICE_NAME, **initial_values)


_configure_logging()
