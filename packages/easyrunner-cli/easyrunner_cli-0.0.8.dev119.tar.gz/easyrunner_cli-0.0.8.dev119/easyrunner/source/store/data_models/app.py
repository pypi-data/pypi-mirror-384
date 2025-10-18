from dataclasses import dataclass, field
from typing import Optional

from ...store.object_id import ObjectId
from .database_dto_base import DatabaseDTOBase


@dataclass
class App(DatabaseDTOBase):
    """Data Transfer Object for the `App` entity.

    An App represents a software application that is hosted/deployed on a server.
    Attributes:
        name (str): Friendly name of the app.
        description (str): Description of the app.
        repo_url (str): URL of the app's repository.
        custom_domain (str): Custom domain for the app.
        id (ObjectId): Unique identifier for the app. Generated if not provided.
    Methods:
        to_json() -> JsonObject: Converts the App instance to a JSON object.
        from_json(data: JsonObject) -> "App": Creates an App instance from a JSON object.
    """

    name: str = field()
    """Friendly name of the app."""

    description: str = field(default="")
    """Description of the app."""

    repo_url: str = field(default="")
    """URL of the app's repository."""

    custom_domain: Optional[str] = field(default=None)
    """Custom domain for the app."""

    id: ObjectId = field(default_factory=ObjectId)
    """Unique identifier for the app. Generated if not provided."""
