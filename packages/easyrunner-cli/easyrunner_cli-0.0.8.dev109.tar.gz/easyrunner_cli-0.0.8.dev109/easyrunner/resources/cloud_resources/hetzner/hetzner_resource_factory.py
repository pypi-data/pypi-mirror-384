from ....cloud_providers.cloud_provider_base import CloudProviderBase
from .hetzner_firewall_rule import HetznerFirewallRule
from .hetzner_virtual_machine import HetznerVirtualMachine


class HetznerResourceFactory:
    """Factory class for creating default Hetzner resource configurations."""

    @staticmethod
    def create_default_firewall_rules() -> list["HetznerFirewallRule"]:
        """Generate a default firewall configuration with hardcoded values."""

        default_rules = [
            # SSH access
            HetznerFirewallRule(
                direction="in",
                protocol="tcp",
                source_ips=["0.0.0.0/0", "::/0"],
                port="22",
                description="SSH access",
            ),
            # HTTP access
            HetznerFirewallRule(
                direction="in",
                protocol="tcp",
                source_ips=["0.0.0.0/0", "::/0"],
                port="80",
                description="HTTP access",
            ),
            # HTTPS access
            HetznerFirewallRule(
                direction="in",
                protocol="tcp",
                source_ips=["0.0.0.0/0", "::/0"],
                port="443",
                description="HTTPS access",
            ),
            # Allow all outbound traffic
            HetznerFirewallRule(
                direction="out",
                protocol="tcp",
                source_ips=[],
                destination_ips=["0.0.0.0/0", "::/0"],
                port="any",
                description="All outbound TCP traffic",
            ),
        ]

        return default_rules

    @staticmethod
    def create_default_virtual_machine(
        name: str,
        provider: CloudProviderBase,
        stack_name: str,
        ssh_public_key: str,
    ) -> "HetznerVirtualMachine":
        """Generate a default VM configuration with hardcoded values.

        Args:
            provider: The cloud provider instance
            stack_name: The Pulumi stack name
            ssh_public_key: The SSH public key to add to the VM
        """

        return HetznerVirtualMachine(
            provider=provider,
            stack_name=stack_name,
            name=name,
            image="ubuntu-24.04",
            size="cx22",  # Hetzner: 2 vCPU, 4 GB RAM
            location="fsn1",
            ssh_keys=[ssh_public_key],
            labels={},
            firewalls=[],  # No firewalls by default
        )
