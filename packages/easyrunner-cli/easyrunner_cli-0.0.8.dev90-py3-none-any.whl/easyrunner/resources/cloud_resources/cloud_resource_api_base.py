from ..resource_base import ResourceBase


class CloudResourceApiBase(ResourceBase):
    """Base class for cloud resources accessed directly via API."""
    def __init__(self) -> None:
        """Initialize a new instance of a cloud API resource."""
        super().__init__()

 