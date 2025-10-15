import datetime
import json
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from custom_python_logger import get_logger

logger = get_logger(__name__)


def report_telemetry(
    func: Callable[..., Any], start_time: datetime.datetime, end_time: datetime.datetime, *args: Any, **kwargs: Any
) -> None:
    data = {
        "function_name": func.__name__,
        "args": args,
        "kwargs": kwargs,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "timestamp": time.time(),
    }
    logger.info(
        f"Sending telemetry data with the following data: {json.dumps(data, indent=4, sort_keys=False, default=str)}"
    )


def report_func_telemetry(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # logger.info(f"Calling function: {func.__name__}, with arguments: {args} and keyword arguments: {kwargs}")
        # return func(*args, **kwargs)
        logger.info(f"calling {report_telemetry.__name__} to report the telemetry of {func.__name__}")
        start_time = datetime.datetime.now(datetime.UTC)
        result = func(*args, **kwargs)
        end_time = datetime.datetime.now(datetime.UTC)
        report_telemetry(*args, func=func, start_time=start_time, end_time=end_time, **kwargs)
        return result

    return wrapper
