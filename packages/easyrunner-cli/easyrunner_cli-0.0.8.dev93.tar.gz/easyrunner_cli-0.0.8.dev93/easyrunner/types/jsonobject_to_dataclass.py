from dataclasses import fields, is_dataclass
from typing import Any, Dict, Type, TypeVar, get_args, get_origin, get_type_hints

T = TypeVar('T')

def jsonobject_to_dataclass(data: Dict[str, Any], cls: Type[T]) -> T:
    """
    Convert a JSON object to a dataclass instance with proper type conversions of nested dataclasses.
    This function handles lists of dataclasses, nested dataclasses, and None values.
    
    Args:
        data: The JSON data to convert
        cls: The target dataclass type T

    Returns:
        An instance of the target dataclass with properly converted values
    """
    if not is_dataclass(cls):
        raise TypeError(f"{cls.__name__} is not a dataclass")

    if data is None:
        return None

    converted_data = {}
    type_hints: Dict[str, Any] = get_type_hints(
        cls
    )  # this method of getting types supports forward references

    import datetime
    from typing import Union

    for field_info in fields(cls):
        field_name: str = field_info.name
        field_type: Any = type_hints[field_name]

        # Skip if field is not in data
        if field_name not in data:
            continue

        field_value = data[field_name]

        # Handle None values
        if field_value is None:
            converted_data[field_name] = None
            continue

        # Handle lists
        if get_origin(field_type) is list:
            item_type = get_args(field_type)[0]
            if isinstance(field_value, list):
                if is_dataclass(item_type):
                    actual_type = item_type if isinstance(item_type, type) else type(item_type)
                    converted_data[field_name] = [jsonobject_to_dataclass(data=item, cls=actual_type) for item in field_value]
                else:
                    converted_data[field_name] = field_value
            else:
                converted_data[field_name] = []
            continue

        # Handle nested dataclasses
        if isinstance(field_value, dict):
            if is_dataclass(field_type):
                actual_type = field_type if isinstance(field_type, type) else type(field_type)
                converted_data[field_name] = jsonobject_to_dataclass(data=field_value, cls=actual_type)
                continue

        # Handle datetime fields (including Optional[datetime])
        origin_type = get_origin(field_type)
        is_datetime = False
        if field_type is datetime.datetime:
            is_datetime = True
        elif origin_type is Union:
            args = get_args(field_type)
            if datetime.datetime in args and type(None) in args:
                is_datetime = True

        if is_datetime and isinstance(field_value, str):
            # Handle 'Z' suffix for UTC
            dt_str = field_value.replace("Z", "+00:00")
            try:
                converted_data[field_name] = datetime.datetime.fromisoformat(dt_str)
            except Exception:
                converted_data[field_name] = field_value  # fallback to raw value
            continue

        # For all other cases, use the field value directly
        converted_data[field_name] = field_value

    # Create a new instance of the dataclass with the converted data
    return cls(**converted_data)
