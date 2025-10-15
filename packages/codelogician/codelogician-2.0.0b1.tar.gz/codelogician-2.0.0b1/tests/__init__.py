from pathlib import Path


def find_pyproject(curr_path: Path) -> Path:
    if (curr_path / "pyproject.toml").exists():
        return curr_path
    if curr_path.parent == curr_path:
        raise FileNotFoundError("pyproject.toml not found")
    return find_pyproject(curr_path.parent)
