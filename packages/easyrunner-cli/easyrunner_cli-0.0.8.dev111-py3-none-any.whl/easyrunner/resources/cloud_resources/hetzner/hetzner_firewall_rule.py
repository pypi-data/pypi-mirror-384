from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class HetznerFirewallRule:
    """Represents a firewall rule for Hetzner Cloud."""

    direction: Literal["in", "out"]
    protocol: Literal["tcp", "udp", "icmp", "esp", "gre"]
    source_ips: list[str]
    port: Optional[str] = None  # Port number, range (e.g., "80-85"), or "any"
    destination_ips: list[str] = field(default_factory=list)
    description: Optional[str] = None
