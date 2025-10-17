from abc import ABC

from .cloud_resource_pulumi_base import CloudResourcePulumiBase


class CloudFirewallBase(CloudResourcePulumiBase, ABC):
    """Abstract base class for cloud firewall resources.
    
    Each cloud provider must implement this interface to provide firewall management
    capabilities using their specific APIs and Pulumi providers.
    """
