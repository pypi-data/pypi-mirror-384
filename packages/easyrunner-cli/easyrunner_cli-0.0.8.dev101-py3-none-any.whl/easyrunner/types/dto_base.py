import json
from abc import ABC
from dataclasses import asdict, dataclass
from typing import Type, TypeVar

from .json import JsonObject
from .jsonobject_to_dataclass import jsonobject_to_dataclass

T = TypeVar('T', bound='DTOBase')


@dataclass
class DTOBase(ABC):
    """Base class for all DTOs."""
    def to_json(self) -> JsonObject:
        """Converts this Server instance to a JSON object."""
        # Get the dictionary from asdictfrom ...types.json import JsonObject
        data_dict = asdict(self)
        # Convert ObjectId instances to strings
        # self._process_object_id(data_dict)
        return data_dict

    # def _process_object_id(self, data: Dict[str, Any]) -> None:
    #     """Process any ObjectId instances in the data dictionary and convert them to strings."""
    #     for key, value in list(data.items()):
    #         if isinstance(value, dict):
    #             self._process_object_id(value)
    #         elif isinstance(value, list):
    #             for i, item in enumerate(value):
    #                 if isinstance(item, dict):
    #                     self._process_object_id(item)
    #                 elif isinstance(item, ObjectId):
    #                     value[i] = str(item)
    #         elif isinstance(value, ObjectId):
    #             data[key] = str(value)

    def to_json_str(self) -> str:
        """Converts this Server instance to a JSON string."""
        return json.dumps(self.to_json(), indent=2)

    @classmethod
    def from_json(cls: Type[T], data: JsonObject) -> T:
        """Creates a Server instance from a JSON object."""
        return jsonobject_to_dataclass(data=data, cls=cls)

    @classmethod
    def from_json_str(cls: Type[T], data: str) -> T:
        """Creates a Server instance from a JSON string."""
        return cls.from_json(json.loads(data))