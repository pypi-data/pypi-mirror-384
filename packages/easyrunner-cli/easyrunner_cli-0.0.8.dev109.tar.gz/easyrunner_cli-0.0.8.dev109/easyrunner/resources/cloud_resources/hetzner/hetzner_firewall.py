from dataclasses import dataclass, field

from ....cloud_providers.cloud_provider_base import CloudProviderBase
from ..cloud_firewall_base import CloudFirewallBase
from .hetzner_firewall_rule import HetznerFirewallRule


@dataclass
class HetznerFirewall(CloudFirewallBase):
    """Hetzner-specific implementation of firewall management using Pulumi.
    
    This resource creates and manages Hetzner Cloud firewalls that can be attached to virtual machines
    to control network traffic. By default, Hetzner Cloud VMs have all inbound traffic blocked
    and all outbound traffic allowed when no firewall is attached.
    """

    provider: CloudProviderBase
    stack_name: str
    name: str
    rules: list[HetznerFirewallRule] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the base class after dataclass initialization."""
        super().__init__(self.provider, self.stack_name)

    # def create(self, firewall_config: FirewallConfig) -> ExecResult[dict[str, Any]]:
    #     """Create a firewall with the specified configuration.

    #     Args:
    #         firewall_config: Configuration for the firewall including rules and labels

    #     Returns:
    #         ExecResult containing firewall creation details:
    #             - firewall_id: ID of the created firewall
    #             - firewall_name: Name of the firewall
    #             - rules_count: Number of rules created
    #     """

    #     def create_firewall_program() -> None:
    #         """Pulumi program to create firewall resources."""
    #         import pulumi_hcloud as hetzner

    #         # Get the provider instance
    #         provider_instance = self._provider.get_provider_instance()

    #         # Convert FirewallRuleConfig to Pulumi format
    #         pulumi_rules = []
    #         for rule in firewall_config.rules:
    #             rule_dict = {
    #                 "direction": rule.direction,
    #                 "protocol": rule.protocol,
    #                 "source_ips": rule.source_ips,
    #             }

    #             # Add optional fields if they exist
    #             if hasattr(rule, 'port') and rule.port is not None:
    #                 rule_dict["port"] = rule.port

    #             if hasattr(rule, 'destination_ips') and rule.destination_ips:
    #                 rule_dict["destination_ips"] = rule.destination_ips

    #             pulumi_rules.append(rule_dict)

    #         # Create the firewall
    #         firewall = hetzner.Firewall(
    #             resource_name=firewall_config.name,
    #             labels=firewall_config.labels or {},
    #             rules=pulumi_rules,
    #             opts=pulumi.ResourceOptions(provider=provider_instance),
    #         )

    #         # Export outputs
    #         pulumi.export("firewall_id", firewall.id.apply(lambda x: str(x)))
    #         pulumi.export("firewall_name", firewall.name)
    #         pulumi.export("rules_count", len(pulumi_rules))

    #     return self._provider.execute_pulumi_program(
    #         program=create_firewall_program,
    #         stack_name=self._stack_name,
    #         backend_url=None,  # Use local backend for Hetzner for now
    #     )
