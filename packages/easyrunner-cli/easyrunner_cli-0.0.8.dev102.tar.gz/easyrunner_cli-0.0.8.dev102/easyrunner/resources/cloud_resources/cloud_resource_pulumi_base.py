from ...cloud_providers.cloud_provider_base import CloudProviderBase
from ..resource_base import ResourceBase


class CloudResourcePulumiBase(ResourceBase):
    """Base class for cloud provider resources virtual machines, object storage, load balancers etc. from providers like AWS, Azure, GCP, Hetzner etc."""
    def __init__(self, provider: CloudProviderBase, stack_name: str) -> None:
        """Initialize the virtual machine resource with a cloud provider.

        Args:
            provider: The cloud provider instance
            stack_name: The name of the Pulumi stack
        """
        self._provider: CloudProviderBase = provider
        self._project_name = f"easyrunner-{provider.name}"
        self._stack_name = stack_name
