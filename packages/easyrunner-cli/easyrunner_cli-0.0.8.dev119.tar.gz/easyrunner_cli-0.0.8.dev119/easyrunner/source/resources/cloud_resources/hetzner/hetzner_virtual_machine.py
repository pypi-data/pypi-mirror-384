from dataclasses import dataclass, field

from ....cloud_providers.cloud_provider_base import CloudProviderBase
from ..cloud_virtual_machine_base import CloudVirtualMachineBase
from .hetzner_firewall import HetznerFirewall


@dataclass
class HetznerVirtualMachine(CloudVirtualMachineBase):
    """Hetzner-specific implementation of virtual machine management using Pulumi."""
    provider: CloudProviderBase
    stack_name: str
    name: str
    size: str
    image: str
    location: str
    ssh_keys: list[str] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    firewalls: list[HetznerFirewall] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize the base class after dataclass initialization."""
        super().__init__(self.provider, self.stack_name)

    # def create(self, vm_config: dict[str, Any]) -> ExecResult[dict[str, Any]]:
    #     """Create a virtual machine with hardcoded defaults."""

    #     def create_vm_program() -> None:
    #         """Pulumi program to create VM resources."""
    #         import pulumi_hcloud as hetzner

    #         # Get the provider instance
    #         provider_instance = self._provider.get_provider_instance()

    #         # Create SSH key if provided
    #         ssh_key = None
    #         if vm_config.ssh_keys:
    #             ssh_key = hetzner.SshKey(
    #                 resource_name=f"{vm_config.name}-key",
    #                 public_key=vm_config.ssh_keys[0],  # Use first key
    #                 opts=pulumi.ResourceOptions(provider=provider_instance),
    #             )

    #         # Create server
    #         server_args = {
    #             "image": vm_config.image,
    #             "server_type": vm_config.size,
    #             "location": vm_config.location or self._provider.region,
    #             "ssh_keys": [ssh_key.id] if ssh_key else [],
    #             "labels": vm_config.labels,
    #         }

    #         # Add firewall IDs if provided
    #         if vm_config.firewall_ids:
    #             server_args["firewall_ids"] = [int(fw_id) for fw_id in vm_config.firewall_ids]

    #         server = hetzner.Server(
    #             resource_name=vm_config.name,
    #             **server_args,
    #             opts=pulumi.ResourceOptions(provider=provider_instance),
    #         )

    #         # Export outputs properly - ensure they're resolved as native types
    #         pulumi.export("server_id", server.id.apply(lambda x: str(x)))
    #         pulumi.export("server_ip", server.ipv4_address.apply(lambda x: str(x)))

    #     return self._provider.execute_pulumi_program(
    #         program=create_vm_program,
    #         stack_name=self._stack_name,
    #         backend_url=None,  # Use local backend for Hetzner for now because there's no Pulumi support yet.
    #         # TODO: switch to manual bucket creation etc. for release
    #     )
