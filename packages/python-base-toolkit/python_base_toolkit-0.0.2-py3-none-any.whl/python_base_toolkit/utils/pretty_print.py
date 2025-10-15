import json
import logging
from collections.abc import Callable
from typing import Any

from custom_python_logger import get_logger

logger = get_logger(__name__)


def log_in_format(
    data: Any, log_level: int = logging.INFO, indent: int = 4, sort_keys: bool = True, default: Callable = None
) -> None:
    formatted_data = json.dumps(data, indent=indent, sort_keys=sort_keys, default=default)

    level_name = logging.getLevelName(log_level).lower()
    log_method = getattr(logger, level_name, logger.debug)

    log_method("\n%s", formatted_data)
