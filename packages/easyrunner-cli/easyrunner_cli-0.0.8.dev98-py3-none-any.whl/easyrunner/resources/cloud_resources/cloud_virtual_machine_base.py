from abc import ABC

from ...cloud_providers.cloud_provider_base import CloudProviderBase
from .cloud_resource_pulumi_base import CloudResourcePulumiBase


class CloudVirtualMachineBase(CloudResourcePulumiBase, ABC):
    """Abstract base class for cloud virtual machine resources.
    
    Each cloud provider must implement this interface to provide VM management
    capabilities using their specific APIs and Pulumi providers.
    """

    def __init__(self, provider: CloudProviderBase, stack_name: str) -> None:
        """Initialize the virtual machine resource with a cloud provider.

        Args:
            provider: The cloud provider instance
        """
        super().__init__(provider, stack_name)
