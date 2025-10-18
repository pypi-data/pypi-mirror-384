from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

# Type alias for YAML values that can appear in dictionaries
YamlValue = Union[str, int, float, bool, None]


@dataclass
class ComposeService:
    """Data class for a Docker Compose service.
    
    Represents a single service definition in a Docker Compose file.
    """

    name: str = field()
    """Name of the service."""

    image: str = field()
    """Container image to use for the service."""

    ports: List[str] = field(default_factory=list)
    """List of port mappings (e.g., ["3000:3000"])."""

    environment: Union[List[str], Dict[str, str]] = field(default_factory=list)
    """Environment variables as list of strings or dict."""

    volumes: List[str] = field(default_factory=list)
    """List of volume mappings."""

    networks: List[str] = field(default_factory=list)
    """List of networks the service is connected to."""

    labels: Dict[str, YamlValue] = field(default_factory=dict)
    """Dictionary of labels as key-value pairs with YAML-compatible values (e.g., {"easyrunner.domain": "myapp.example.com", "easyrunner.enabled": true})."""

    restart: Optional[str] = field(default=None)
    """Restart policy for the service."""

    user: Optional[str] = field(default=None)
    """User to run the container as."""

    command: Optional[Union[str, List[str]]] = field(default=None)
    """Command to run in the container."""

    depends_on: List[str] = field(default_factory=list)
    """List of services this service depends on."""
