from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ComposeNetwork:
    """Data class for a Docker Compose network.
    
    Represents a network definition in a Docker Compose file.
    """
    
    name: str = field()
    """Name of the network."""
    
    project_name: str = field()
    """Name of the compose project this network belongs to."""
    
    driver: Optional[str] = field(default=None)
    """Network driver (e.g., bridge, overlay)."""
    
    external: bool = field(default=False)
    """Whether the network is external."""
    
    driver_opts: Dict[str, str] = field(default_factory=dict)
    """Driver-specific options."""
    
    ipam: Optional[Dict[str, str]] = field(default=None)
    """IP Address Management configuration."""
    
    def systemd_network_name(self) -> str:
        """build the systemd network name

        Returns:
            str: The systemd generated network name for the network.
        """
        return f"systemd-{self.project_name}__{self.name}"
