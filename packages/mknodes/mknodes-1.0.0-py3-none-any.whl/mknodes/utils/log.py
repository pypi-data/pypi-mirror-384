from __future__ import annotations

import importlib.util
import io
import logging
import sys
from typing import Any


class Logger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def __getattr__(self, val: Any):
        return getattr(self.logger, val)

    def log_dict(self, dct: dict[str, Any], level: int = logging.INFO):
        for k, v in dct.items():
            self.logger.log(level, "%s: %s", k, v)


def get_logger(name: str | None = None):
    if importlib.util.find_spec("mkdocs"):
        from mkdocs.plugins import get_plugin_logger

        return get_plugin_logger("mknodes")
    return logging.getLogger(name)


def basic():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


log_stream = io.StringIO()
log_handler = logging.StreamHandler(log_stream)
log_handler.setLevel(logging.DEBUG)
fmt = logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log_handler.setFormatter(fmt)
logger = logging.getLogger("mkdocs")
logger.addHandler(log_handler)
