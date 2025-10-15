import random
import string
from datetime import datetime

from custom_python_logger import get_logger

logger = get_logger(__name__)


def generate_id(length: int = 8) -> str:
    # helper function for generating an id
    id_ = "".join(random.choices(string.ascii_uppercase, k=length))
    logger.info(f"id is: {id_}")
    return id_


def generate_id_by_date() -> str:
    timestamp = datetime.now()
    id_ = timestamp.strftime("%Y%m%d")
    logger.info(f"id is: {id_}")
    return id_


def generate_id_by_time() -> str:
    timestamp = datetime.now()
    id_ = timestamp.strftime("%H%M%S%m")
    logger.info(f"id is: {id_}")
    return id_


def generate_id_by_date_and_time() -> str:
    timestamp = datetime.now()
    id_ = timestamp.strftime("%Y%m%d%H%M%S%m")
    logger.info(f"id is: {id_}")
    return id_
