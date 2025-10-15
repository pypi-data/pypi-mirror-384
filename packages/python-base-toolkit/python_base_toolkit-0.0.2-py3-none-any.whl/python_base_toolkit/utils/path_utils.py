from pathlib import Path


def get_project_path_by_name(project_name: str) -> str:
    current_path = Path(__file__).parent
    while current_path != current_path.parent:  # pylint: disable=W0149
        if str(current_path).endswith(f"/{project_name}"):
            return str(current_path)
        current_path = current_path.parent
    raise FileNotFoundError(
        f'Project "{project_name}" not found in any parent directories.\n' f"Current path: {Path(__file__)}",
    )


def get_project_path_by_file(markers: set = None) -> Path:
    markers = markers or {".git", ".gitignore", "setup.py", "pyproject.toml", "LICENSE", "README.md"}
    for marker in markers:
        path = Path(__file__).resolve()
        for parent in path.parents:
            if (parent / marker).exists():
                return parent
    raise RuntimeError(f'Project root with markers "{markers}" not found.')
