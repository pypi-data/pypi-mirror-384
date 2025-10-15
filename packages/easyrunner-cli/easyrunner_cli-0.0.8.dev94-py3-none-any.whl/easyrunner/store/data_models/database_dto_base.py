from ...types.dto_base import DTOBase
from ...types.json import JsonObject
from ..object_id import ObjectId


class DatabaseDTOBase(DTOBase):
    """Base class for database-related DTOs."""

    def to_json(self) -> JsonObject:
        data_dict = super().to_json()
        # Add any database-specific fields or transformations here
        self._process_object_id(data_dict)
        return data_dict

    def _process_object_id(self, data: JsonObject) -> None:
        """Process any ObjectId instances in the data dictionary and convert them to strings."""
        for key, value in list(data.items()):
            if isinstance(value, dict):
                self._process_object_id(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._process_object_id(item)
                    elif isinstance(item, ObjectId):
                        value[i] = str(item)
            elif isinstance(value, ObjectId):
                data[key] = str(value)
