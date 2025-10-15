import os
import sys


def get_venv_details() -> dict:
    return {
        "python_executable_path": sys.executable,
        "python_version": sys.version,
        "venv_path": os.getenv("VIRTUAL_ENV"),
    }
