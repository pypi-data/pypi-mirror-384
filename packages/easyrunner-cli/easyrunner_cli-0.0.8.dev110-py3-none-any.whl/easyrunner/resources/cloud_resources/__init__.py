"""Cloud resource abstractions for EasyRunner.

This module provides provider-agnostic interfaces for cloud resources like virtual machines
and firewalls. The actual implementations are provider-specific and handled through the
factory pattern.

Main classes:
- CloudResourceFactory: Creates provider-specific implementations

Abstract base classes:
- CloudVirtualMachineBase: Abstract interface for VM implementations
- CloudFirewallBase: Abstract interface for firewall implementations

Provider implementations:
- hetzner/: Hetzner Cloud specific implementations
"""

from .cloud_firewall_base import CloudFirewallBase
from .cloud_resource_api_base import CloudResourceApiBase
from .cloud_resource_pulumi_base import CloudResourcePulumiBase
from .cloud_virtual_machine_base import CloudVirtualMachineBase

__all__ = [
    "CloudFirewallBase",
    "CloudResourcePulumiBase",
    "CloudVirtualMachineBase",
    "CloudResourceApiBase",
]
