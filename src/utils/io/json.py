"""JSON utilities for reading and writing data."""

import json
from pathlib import Path
from typing import Any, Union


def load_json(path: Union[str, Path]) -> Any:
    """Load data from a JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Loaded JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Union[str, Path], data: Any) -> None:
    """Save data to a JSON file.

    Args:
        path: Path to save JSON file
        data: Data to save

    Raises:
        TypeError: If data is not JSON serializable
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
