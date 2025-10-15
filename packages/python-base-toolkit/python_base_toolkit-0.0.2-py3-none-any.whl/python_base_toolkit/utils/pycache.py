import shutil
from pathlib import Path

from custom_python_logger.logger import get_logger

from python_base_toolkit.utils.path_utils import get_project_path_by_file

logger = get_logger(__name__)


def delete_pycache_folder(root_dir: Path = None, ignored_dirs: set = None) -> None:
    root_dir = Path(root_dir) if root_dir else get_project_path_by_file()
    ignored_dirs = ignored_dirs or {".venv"}

    for path in root_dir.rglob("__pycache__"):
        if any(ignored in path.parts for ignored in ignored_dirs):
            continue

        logger.info(f"Cleaning: {path}")
        try:
            shutil.rmtree(path)
            logger.info(f"Deleted: {path}")
        except FileNotFoundError:
            logger.exception(f"Already removed: {path}")
        except Exception as e:
            logger.exception(f"Failed to delete {path}: {e}")
    logger.info("Finished cleaning __pycache__ folders.")
