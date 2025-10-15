from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ComposeVolume:
    """Data class for a Docker Compose volume.
    
    Represents a volume definition in a Docker Compose file.
    """
    
    name: str = field()
    """Name of the volume."""
    
    driver: Optional[str] = field(default=None)
    """Volume driver."""
    
    driver_opts: Dict[str, str] = field(default_factory=dict)
    """Driver-specific options."""
    
    external: bool = field(default=False)
    """Whether the volume is external."""
