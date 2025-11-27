"""
Serialization utilities for Pydantic models.

This module provides functions to save and load Pydantic models to/from JSON files,
with proper handling of datetime fields and pretty-printing support.
"""

from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel


def save_to_file(
    model: BaseModel, file_path: Union[str, Path], indent: int = 2
) -> None:
    """
    Save a Pydantic model to a JSON file.

    Uses Pydantic's built-in serialization with proper datetime handling.
    Creates parent directories if they don't exist.

    Args:
        model: The Pydantic model instance to save
        file_path: Path to the output JSON file
        indent: Number of spaces for JSON indentation (default: 2)

    Raises:
        OSError: If file cannot be written
        ValueError: If model cannot be serialized

    Example:
        >>> from skillforge.models import Course, Difficulty
        >>> course = Course(
        ...     id="1", topic="Python",
        ...     description="Learn Python",
        ...     difficulty=Difficulty.BEGINNER
        ... )
        >>> save_to_file(course, "course.json")
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Use Pydantic's model_dump_json with proper serialization
    json_str = model.model_dump_json(indent=indent)

    path.write_text(json_str, encoding="utf-8")


def load_from_file(
    model_class: type[BaseModel], file_path: Union[str, Path]
) -> BaseModel:
    """
    Load a Pydantic model from a JSON file.

    Uses Pydantic's built-in validation and deserialization.

    Args:
        model_class: The Pydantic model class to instantiate
        file_path: Path to the JSON file to load

    Returns:
        An instance of model_class populated with data from the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        pydantic.ValidationError: If the data doesn't match the model schema

    Example:
        >>> from skillforge.models import Course
        >>> course = load_from_file(Course, "course.json")
        >>> print(course.topic)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    json_str = path.read_text(encoding="utf-8")

    # Use Pydantic's model_validate_json for validation and deserialization
    return model_class.model_validate_json(json_str)


def to_dict(model: BaseModel, exclude_none: bool = False) -> dict[str, Any]:
    """
    Convert a Pydantic model to a dictionary.

    Args:
        model: The Pydantic model instance to convert
        exclude_none: If True, exclude fields with None values (default: False)

    Returns:
        Dictionary representation of the model

    Example:
        >>> from skillforge.models import Course, Difficulty
        >>> course = Course(
        ...     id="1", topic="Python",
        ...     description="Learn Python",
        ...     difficulty=Difficulty.BEGINNER
        ... )
        >>> data = to_dict(course)
        >>> print(data["topic"])
        'Python'
    """
    return model.model_dump(exclude_none=exclude_none)


def to_json(
    model: BaseModel, indent: Optional[int] = None, exclude_none: bool = False
) -> str:
    """
    Convert a Pydantic model to a JSON string.

    Args:
        model: The Pydantic model instance to convert
        indent: Number of spaces for indentation (None for compact, default: None)
        exclude_none: If True, exclude fields with None values (default: False)

    Returns:
        JSON string representation of the model

    Example:
        >>> from skillforge.models import Course, Difficulty
        >>> course = Course(
        ...     id="1", topic="Python",
        ...     description="Learn Python",
        ...     difficulty=Difficulty.BEGINNER
        ... )
        >>> json_str = to_json(course, indent=2)
        >>> print(json_str)
    """
    return model.model_dump_json(indent=indent, exclude_none=exclude_none)


def from_dict(model_class: type[BaseModel], data: dict[str, Any]) -> BaseModel:
    """
    Create a Pydantic model instance from a dictionary.

    Args:
        model_class: The Pydantic model class to instantiate
        data: Dictionary containing the model data

    Returns:
        An instance of model_class

    Raises:
        pydantic.ValidationError: If the data doesn't match the model schema

    Example:
        >>> from skillforge.models import Course
        >>> data = {
        ...     "id": "1", "topic": "Python",
        ...     "description": "Learn Python",
        ...     "difficulty": "beginner"
        ... }
        >>> course = from_dict(Course, data)
        >>> print(course.topic)
        'Python'
    """
    return model_class.model_validate(data)


def from_json(model_class: type[BaseModel], json_str: str) -> BaseModel:
    """
    Create a Pydantic model instance from a JSON string.

    Args:
        model_class: The Pydantic model class to instantiate
        json_str: JSON string containing the model data

    Returns:
        An instance of model_class

    Raises:
        json.JSONDecodeError: If json_str is not valid JSON
        pydantic.ValidationError: If the data doesn't match the model schema

    Example:
        >>> from skillforge.models import Course
        >>> json_str = '{"id": "1", "topic": "Python"}'
        >>> course = from_json(Course, json_str)
        >>> print(course.topic)
        'Python'
    """
    return model_class.model_validate_json(json_str)
