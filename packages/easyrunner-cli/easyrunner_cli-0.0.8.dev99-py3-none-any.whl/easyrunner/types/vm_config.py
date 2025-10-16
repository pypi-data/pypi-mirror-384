"""Virtual machine configuration type definitions."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VMConfig:
    """Configuration for creating a virtual machine.

    This is a provider-agnostic configuration that gets translated
    to provider-specific parameters when creating VMs.
    """

    name: str
    image: str
    size: str
    location: str
    ssh_keys: list[str]
    labels: Optional[dict[str, str]] = None
    firewall_ids: Optional[list[str]] = None

    def __post_init__(self) -> None:
        """Initialize default values after dataclass initialization."""
        if self.labels is None:
            self.labels = {}
        if self.firewall_ids is None:
            self.firewall_ids = []
