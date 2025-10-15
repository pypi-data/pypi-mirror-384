import json
from typing import Any

from .object_id import ObjectId


class EasyRunnerJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for EasyRunner-specific types."""
    
    def default(self, o: Any) -> Any:
        # Handle ObjectId serialization
        if isinstance(o, ObjectId):
            return str(o)

        # Let the parent class handle everything else
        return super().default(o)
