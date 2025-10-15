import json
from dataclasses import is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd
from custom_python_logger import get_logger

logger = get_logger(__name__)


def default_serialize(obj: object) -> object:
    if isinstance(obj, type):
        return obj.__name__
    if is_dataclass(obj) and not isinstance(obj, type):
        return obj.__dict__
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, tuple):
        return list(obj)
    if isinstance(obj, datetime | date | time):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, Path):
        return str(obj)
    if obj is pd.NA:
        return None
    logger.error(f"Object is not serializable: {obj}")
    raise TypeError(f"Type {type(obj)} not serializable")


def to_json_serializable(obj: Any) -> Any:
    """Convert an object to a JSON-serializable structure."""
    serialized_json = json.dumps(obj, default=default_serialize)
    return json.loads(serialized_json)
