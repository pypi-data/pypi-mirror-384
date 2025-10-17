import json
from typing import Dict, Optional, Union

JsonValue = Union[str, int, float, bool, None]
"""A JSON value."""

JsonObject = Dict[str, Union["JsonObject", "JsonArray", JsonValue]]
"""A JSON object."""

JsonArray = list[Union["JsonArray", JsonObject, JsonValue]]
"""A JSON array."""


# Helper functions for runtime type checking
def is_json_value(value: object) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def is_json_object(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return all(
        isinstance(k, str)
        and (is_json_value(v) or is_json_object(v) or is_json_array(v))
        for k, v in value.items()
    )


def is_json_array(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return all(is_json_value(v) or is_json_object(v) or is_json_array(v) for v in value)


def to_json_object(json_str: str) -> JsonObject:
    """Converts a JSON string to a JsonObject with validation."""
    if not json_str or not json_str.strip():
        raise ValueError("Empty or whitespace-only JSON string")

    try:
        parsed = json.loads(json_str)
        if not is_json_object(parsed):
            raise ValueError(
                f"JSON does not represent an object, got {type(parsed).__name__}"
            )
        return parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON syntax: {e}") from e


def to_json_object_safe(json_str: str) -> Optional[JsonObject]:
    """Safely converts a JSON string to JsonObject, returns None on error."""
    try:
        return to_json_object(json_str)
    except ValueError:
        return None


def to_json_array(json_str: str) -> JsonArray:
    """Converts a JSON string to a JsonArray with validation."""
    if not json_str or not json_str.strip():
        raise ValueError("Empty or whitespace-only JSON string")

    try:
        parsed = json.loads(json_str)
        if not is_json_array(parsed):
            raise ValueError(
                f"JSON does not represent an array, got {type(parsed).__name__}"
            )
        return parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON syntax: {e}") from e


def to_json_array_safe(json_str: str) -> Optional[JsonArray]:
    """Safely converts a JSON string to JsonArray, returns None on error."""
    try:
        return to_json_array(json_str)
    except ValueError:
        return None
