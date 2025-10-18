from typing import Literal, Self

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class IpTablesCommands(CommandBase):

    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str = "iptables") -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name="null_pkg"
        )

    def add_port_redirect(self: Self, source_port: int, dest_port: int) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} -t nat -A PREROUTING -p tcp --dport {source_port} -j REDIRECT --to-port {dest_port}", sudo=True)

    def check_port_redirect_exists(self: Self, source_port: int, dest_port: int) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} -t nat -C PREROUTING -p tcp --dport {source_port} -j REDIRECT --to-port {dest_port}", sudo=True)

    def add_port_dnat(
        self: Self, source_port: int, dest_ip: str, dest_port: int
    ) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} -t nat -A PREROUTING -p tcp --dport {source_port} -j DNAT --to-destination {dest_ip}:{dest_port}",
            sudo=True,
        )

    def check_port_dnat_exists(
        self: Self, source_port: int, dest_ip: str, dest_port: int
    ) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} -t nat -C PREROUTING -p tcp --dport {source_port} -j DNAT --to-destination {dest_ip}:{dest_port}",
            sudo=True,
        )

    def add_inbound_rule(
        self: Self,
        protocol: Literal["tcp", "udp", "all"],
        dport: int | None,
        action: Literal["DROP", "ACCEPT"],
        source_ip: str,
        negate_source: bool = False,
        state: list[Literal["NEW", "ESTABLISHED", "RELATED"]] | None = None,
    ) -> RunnableCommandString:
        """
        Add a generic inbound rule to iptables.

        Args:
            protocol: Protocol (e.g., 'tcp', 'udp', 'all')
            dport: Destination port (None if not applicable)
            action: Action to take (e.g., 'DROP', 'ACCEPT')
            source_ip: Source IP
            negate_source: If True, negates the source IP match
            state: Optional list of connection states to match (e.g., ['ESTABLISHED', 'RELATED'])
        Return:
            RunnableCommandString for the command
        """
        src_part = f"{'! ' if negate_source else ''}-s {source_ip}" if source_ip else ""
        dport_part = f"--dport {dport}" if dport is not None else ""
        state_part = f"-m state --state {','.join(state)}" if state else ""

        # Build command with conditional parts
        cmd_parts = [
            self.command_name,
            "-A INPUT",
            f"-p {protocol}",
            dport_part,
            src_part,
            state_part,
            f"-j {action}"
        ]

        # Filter out empty parts and join with spaces
        cmd = " ".join(part for part in cmd_parts if part.strip())
        return RunnableCommandString(command=cmd, sudo=True)

    def check_inbound_rule_exists(
        self: Self,
        protocol: Literal["tcp", "udp", "all"],
        dport: int | None,
        action: Literal["DROP", "ACCEPT"],
        source_ip: str,
        negate_source: bool = False,
        state: list[Literal["NEW", "ESTABLISHED", "RELATED"]] | None = None,
    ) -> RunnableCommandString:
        """
        Check if a generic inbound rule exists in iptables.

        Args:
            protocol: Protocol (e.g., 'tcp', 'udp', 'all')
            dport: Destination port
            action: Action to take (e.g., 'DROP', 'ACCEPT')
            source_ip: Source IP
            negate_source: If True, negates the source IP match
            state: Optional list of connection states to match (e.g., ['ESTABLISHED', 'RELATED'])
        Return:
            RunnableCommandString for the command
        """
        src_part = f"{'! ' if negate_source else ''}-s {source_ip}" if source_ip else ""
        dport_part = f"--dport {dport}" if dport is not None else ""
        state_part = f"-m state --state {','.join(state)}" if state else ""

        # Build command with conditional parts
        cmd_parts = [
            self.command_name,
            "-C INPUT",
            f"-p {protocol}",
            dport_part,
            src_part,
            state_part,
            f"-j {action}"
        ]

        # Filter out empty parts and join with spaces
        cmd = " ".join(part for part in cmd_parts if part.strip())
        return RunnableCommandString(command=cmd, sudo=True)

    def set_default_policy(
        self: Self,
        chain: Literal["INPUT", "OUTPUT", "FORWARD"],
        policy: Literal["ACCEPT", "DROP"]
    ) -> RunnableCommandString:
        """
        Set the default policy for an iptables chain.

        Args:
            chain: The chain to set policy for (INPUT, OUTPUT, FORWARD)
            policy: The default policy (ACCEPT or DROP)
        Return:
            RunnableCommandString for the command
        """
        cmd = f"{self.command_name} -P {chain} {policy}"
        return RunnableCommandString(command=cmd, sudo=True)

    def version(self: Self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} --version")

    def version_response_prefix(self: Self) -> str:
        return f"{self.command_name} v"

    def check_accept_redirected_port_tcp_exists(
        self: Self, port: int
    ) -> RunnableCommandString:
        """Check if a rule to accept TCP traffic on a port that has been redirected by NAT exists.
        This uses the conntrack module to check for traffic that has been DNATed or REDIRECTed.
        """
        return RunnableCommandString(
            command=f"{self.command_name} -C INPUT -p tcp --dport {port} -m conntrack --ctstate DNAT -j ACCEPT",
            sudo=True,
        )

    def add_accept_redirected_port_tcp(self: Self, port: int) -> RunnableCommandString:
        """Add a rule to accept TCP traffic on a port that has been redirected by NAT.
        This uses the conntrack module to only accept traffic that has been DNATed or REDIRECTed.
        """
        return RunnableCommandString(
            command=f"{self.command_name} -A INPUT -p tcp --dport {port} -m conntrack --ctstate DNAT -j ACCEPT",
            sudo=True,
        )
