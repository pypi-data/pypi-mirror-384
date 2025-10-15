import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from custom_python_logger import get_logger

logger = get_logger(__name__)


class Timer:
    def __init__(self) -> None:
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        logger.info("Timer started.")
        return self

    def __exit__(self, exc_type: type, exc_value: Exception, exc_traceback: object) -> None:
        # logger.info(exc_type, exc_value, exc_traceback)
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time
        logger.info(f"Timer stopped. Elapsed time: {self.elapsed_time:.2f} seconds.")


def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with Timer():
            return func(*args, **kwargs)

    return wrapper
