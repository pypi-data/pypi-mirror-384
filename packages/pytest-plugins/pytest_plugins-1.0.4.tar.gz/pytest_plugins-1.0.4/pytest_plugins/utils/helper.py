import json
from collections.abc import Callable
from pathlib import Path

from custom_python_logger import get_logger
from python_base_toolkit.utils.data_serialization import default_serialize

logger = get_logger("pytest_plugins.utils")


def get_project_root(marker: str = ".git") -> Path | None:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / marker).exists():
            return parent
    return None


def serialize_data(obj: object) -> object:  # default_serialize
    return default_serialize(obj=obj)


def open_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as json_file:
        return json.load(json_file)


def save_as_json(path: Path, data: dict, default: Callable | None = None) -> None:
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as json_file:
        text = json.dumps(data, indent=4, default=default) if default else json.dumps(data, indent=4)
        json_file.write(text)


def save_as_markdown(path: Path, data: str) -> None:
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as md_file:
        md_file.write(data)
