from dataclasses import dataclass, field
from typing import List

from ...store.data_models.app import App
from ...store.object_id import ObjectId
from .database_dto_base import DatabaseDTOBase


@dataclass
class Server(DatabaseDTOBase):
    """Data Transfer Object for the `Server` entity.

    Attributes:
        name (str): Friendly name of the server.
        hostname_or_ip (str): Hostname or IP address of the server. Hostname need to resolve to an IP address.
        id (ObjectId): Unique identifier for the server. Generated if not provided.
        apps (List[App]): List of apps associated with the server.

    Methods:
        to_json() -> JsonObject: Converts the Server instance to a JSON object.
        from_json(data: JsonObject) -> "Server": Creates a Server instance from a JSON object.
    """

    name: str = field()
    """Friendly name of the server."""

    hostname_or_ip: str = field()
    """Hostname or IP address of the server. Hostname need to resolve to an IP address."""

    description: str = field(default="")
    """Description of the server."""

    id: ObjectId = field(default_factory=ObjectId)  # Generate a new UUID if None
    """Unique identifier for the server. Generated if not provided."""

    apps: List["App"] = field(default_factory=list)
    """List of apps hosted/deployed on the server."""
