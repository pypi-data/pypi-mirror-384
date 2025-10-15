"""Utilities for configuring bitagere logging.

This module provides a small helper so applications embedding bitagere can
customise logging behaviour without having to remember logger names.
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional

DEFAULT_LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(module)s.%(funcName)s:%(lineno)d - %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    *,
    level: int = logging.INFO,
    handlers: Optional[Iterable[logging.Handler]] = None,
    format: str = DEFAULT_LOG_FORMAT,
    datefmt: str = DEFAULT_DATE_FORMAT,
    propagate: bool = False,
) -> logging.Logger:
    """Configure the root ``bitagere`` logger.

    Parameters
    ----------
    level:
        Logging level to apply to the package logger. Defaults to ``INFO``.
    handlers:
        Optional iterable of pre-configured ``logging.Handler`` instances. When
        omitted a single ``StreamHandler`` targeting ``sys.stderr`` is created
        automatically. Handlers are attached in the order provided.
    format:
        Format string applied to each handler if the handler does not already
        have a formatter configured.
    datefmt:
        Date format string passed to :class:`logging.Formatter` for timestamps.
    propagate:
        Whether the ``bitagere`` logger should propagate to the root logger.
        Defaults to ``False`` so that applications can opt in explicitly.

    Returns
    -------
    logging.Logger
        The configured ``bitagere`` package logger so callers can tweak it
        further if needed.
    """
    logger = logging.getLogger("bitagere")
    logger.setLevel(level)

    # Clear existing handlers before attaching new ones to avoid duplicate logs.
    logger.handlers.clear()

    if handlers is None:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(format, datefmt))
        handlers_to_use = [stream_handler]
    else:
        handlers_to_use = list(handlers)
        for handler in handlers_to_use:
            if handler.formatter is None:
                handler.setFormatter(logging.Formatter(format, datefmt))

    for handler in handlers_to_use:
        logger.addHandler(handler)

    logger.propagate = propagate
    return logger


__all__ = ["configure_logging", "DEFAULT_LOG_FORMAT", "DEFAULT_DATE_FORMAT"]
