"""Structured logging configuration for the Worker."""

import logging
import sys

import structlog

stdout_handler = logging.StreamHandler(sys.stdout)
stderr_handler = logging.StreamHandler(sys.stderr)

stdout_handler.setLevel(logging.DEBUG)
stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)

stderr_handler.setLevel(logging.WARNING)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stdout_handler)
root_logger.addHandler(stderr_handler)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.EventRenamer("message"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger()
