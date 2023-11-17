import logging

from src.config.settings import settings


def configure_logging(level=None):
    if level is None:
        level = logging.DEBUG if settings.DEBUG else logging.INFO

    # from loguru_logging_intercept import setup_loguru_logging_intercept
    # setup_loguru_logging_intercept(level)
