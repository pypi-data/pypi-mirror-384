from typing import Literal, Optional, Union

from ...command_executor import CommandExecutor
from ...command_executor_local import CommandExecutorLocal
from ...commands.base.ip_tables_commands import IpTablesCommands
from ...commands.ubuntu.dir_commands_ubuntu import DirCommandsUbuntu
from ...commands.ubuntu.ip_tables_persistent_commands_ubuntu import (
    IpTablesPersistentCommandsUbuntu,
)
from ...types.exec_result import ExecResult
from .directory import Directory
from .os_resource_base import OsResourceBase


class IpTables(OsResourceBase):
    def __init__(self, commands: IpTablesCommands, executor: CommandExecutor):
        self.commands = commands
        self.executor = executor

        self._ip_tables_persistent_commands = IpTablesPersistentCommandsUbuntu(
            cpu_arch=self.commands.cpu_arch,
        )

    def check_port_redirect_exists(
        self, source_port: int, dest_port: int
    ) -> ExecResult:
        """Check if a port redirect rule exists in iptables.

        Args:
            source_port: Source port to check
            dest_port: Destination port to check
        Return:
            ExecResult of the command
        """
        return self.executor.execute(
            self.commands.check_port_redirect_exists(source_port, dest_port)
        )

    def check_inbound_rule_exists(
        self,
        protocol: Literal["tcp", "udp", "all"],
        dport: int | None,
        action: Literal["DROP", "ACCEPT"],
        source_ip: str,
        negate_source: bool = False,
        state: Optional[list[Literal["NEW", "ESTABLISHED", "RELATED"]]] = None,
    ) -> ExecResult:
        """Check if an inbound rule exists in iptables.

        Args:
            protocol: Protocol (e.g., 'tcp', 'udp')
            dport: Destination port (None if not applicable)
            action: Action to take (e.g., 'DROP', 'ACCEPT')
            source_ip: Source IP
            negate_source: If True, negates the source IP match i.e. not from the source_ip
            state: Optional list of connection states to match (e.g., ['ESTABLISHED', 'RELATED'])
        Return:
            ExecResult of the command
        """
        return self.executor.execute(
            self.commands.check_inbound_rule_exists(
                protocol, dport, action, source_ip, negate_source, state
            )
        )

    def add_port_redirect(self, source_port: int, dest_port: int) -> ExecResult:
        """Add a port redirect rule (REDIRECT) to iptables if it doesn't already exist."""
        exists = self.check_port_redirect_exists(source_port, dest_port)
        if exists.return_code != 0:
            return self.executor.execute(self.commands.add_port_redirect(source_port, dest_port))
        else:
            return exists

    def check_port_dnat_exists(
        self, source_port: int, dest_ip: str, dest_port: int
    ) -> ExecResult:
        """Check if a port DNAT rule exists in iptables."""
        return self.executor.execute(
            self.commands.check_port_dnat_exists(source_port, dest_ip, dest_port)
        )

    def add_port_dnat(
        self, source_port: int, dest_ip: str, dest_port: int
    ) -> ExecResult:
        """Add a port DNAT rule to iptables if it doesn't already exist."""
        exists = self.check_port_dnat_exists(source_port, dest_ip, dest_port)
        if exists.return_code != 0:
            return self.executor.execute(
                self.commands.add_port_dnat(source_port, dest_ip, dest_port)
            )
        else:
            return exists

    def add_inbound_rule(
        self,
        protocol: Literal["tcp", "udp", "all"],
        dport: int | None,
        action: Literal["DROP", "ACCEPT"],
        source_ip: str,
        negate_source: bool = False,
        state: Optional[list[Literal["NEW", "ESTABLISHED", "RELATED"]]] = None,
    ) -> ExecResult:
        """Add a generic inbound rule to iptables.

        Args:
            protocol: Protocol (e.g., 'tcp', 'udp', 'all')
            dport: Destination port
            action: Action to take (e.g., 'DROP', 'ACCEPT')
            source_ip: Source IP
            negate_source: If True, negates the source IP match i.e. not from the source_ip
            state: Optional list of connection states to match (e.g., ['ESTABLISHED', 'RELATED'])
        Return:
            ExecResult of the command
        """
        exists = self.check_inbound_rule_exists(
            protocol, dport, action, source_ip, negate_source, state
        )
        if exists.return_code != 0:
            return self.executor.execute(
                self.commands.add_inbound_rule(
                    protocol, dport, action, source_ip, negate_source, state
                )
            )
        else:
            return exists

    def save(self, ip_version: Literal["ipv4", "ipv6"] = "ipv4") -> ExecResult:
        """Save iptables rules to a file. Will auto load on reboot."""
        dir = Directory(
            path="/etc/iptables",
            executor=self.executor,
            commands=DirCommandsUbuntu(cpu_arch=self.commands.cpu_arch),
        )
        if not dir.exists():
            dir.create(owner="root", group="root", mode="755")
        return self.executor.execute(self._ip_tables_persistent_commands.save_ipv4() if ip_version == "ipv4" else self._ip_tables_persistent_commands.save_ipv6())

    def set_default_policy(
        self,
        chain: Literal["INPUT", "OUTPUT", "FORWARD"],
        policy: Literal["ACCEPT", "DROP"],
    ) -> ExecResult:
        """Set the default policy for an iptables chain.

        Args:
            chain: The chain to set policy for (INPUT, OUTPUT, FORWARD)
            policy: The default policy (ACCEPT or DROP)
        Return:
            ExecResult of the command
        """
        return self.executor.execute(self.commands.set_default_policy(chain, policy))

    def version(self) -> ExecResult:
        return self.executor.execute(self.commands.version())

    def check_accept_redirected_port_tcp_exists(self, port: int) -> ExecResult:
        """Check if a rule to accept TCP traffic on a port that has been redirected by NAT exists.

        This uses the conntrack module to check for traffic that has been DNATed or REDIRECTed.

        Args:
            port: The port number to check for redirected traffic acceptance
        Return:
            ExecResult of the check command (return_code 0 if rule exists, non-zero if not)
        """
        return self.executor.execute(
            self.commands.check_accept_redirected_port_tcp_exists(port)
        )

    def add_accept_redirected_port_tcp(self, port: int) -> ExecResult:
        """Add a rule to accept TCP traffic on a port that has been redirected by NAT if it doesn't already exist.

        This uses the conntrack module to only accept traffic that has been DNATed or REDIRECTed.

        Args:
            port: The port number to accept redirected traffic on
        Return:
            ExecResult of the command
        """
        exists = self.check_accept_redirected_port_tcp_exists(port)
        if exists.return_code != 0:
            return self.executor.execute(
                self.commands.add_accept_redirected_port_tcp(port)
            )
        else:
            return exists

    def test_external_http_access(
        self,
        server_ip: str,
        local_executor: Union[CommandExecutor, CommandExecutorLocal],
    ) -> ExecResult:
        """Test external HTTP access (port 80) to verify it works.

        Args:
            server_ip: IP address of the server to test
            local_executor: Local command executor to run curl from external perspective
        Return:
            ExecResult of the connectivity test
        """
        from ...commands.runnable_command_string import RunnableCommandString

        http_test_cmd = RunnableCommandString(
            command=f"curl -s --connect-timeout 5 --max-time 10 http://{server_ip}/caddyfile-static-hello",
            sudo=False,
        )
        return local_executor.execute(http_test_cmd)

    def test_external_port_blocked(
        self,
        server_ip: str,
        port: int,
        local_executor: Union[CommandExecutor, CommandExecutorLocal],
        protocol: str = "http",
    ) -> ExecResult:
        """Test that a port is blocked from external access.

        Args:
            server_ip: IP address of the server to test
            port: Port number to test blocking
            local_executor: Local command executor to run curl from external perspective
            protocol: Protocol to test (http or https)
        Return:
            ExecResult of the connectivity test (success=False means port is properly blocked)
        """
        from ...commands.runnable_command_string import RunnableCommandString

        if protocol == "https":
            url = f"https://{server_ip}:{port}/caddyfile-static-hello"
            extra_args = "-k"  # Accept self-signed certificates
        else:
            url = f"http://{server_ip}:{port}/caddyfile-static-hello"
            extra_args = ""

        test_cmd = RunnableCommandString(
            command=f"curl -s --connect-timeout 3 --max-time 5 {url} {extra_args}".strip(),
            sudo=False,
        )
        return local_executor.execute(test_cmd)

    def test_external_caddy_api_blocked(
        self,
        server_ip: str,
        local_executor: Union[CommandExecutor, CommandExecutorLocal],
    ) -> ExecResult:
        """Test that Caddy API (port 2019) is blocked from external access.

        Args:
            server_ip: IP address of the server to test
            local_executor: Local command executor to run curl from external perspective
        Return:
            ExecResult of the connectivity test (success=False means API is properly blocked)
        """
        from ...commands.runnable_command_string import RunnableCommandString

        caddy_api_cmd = RunnableCommandString(
            command=f"curl -s --connect-timeout 3 --max-time 5 http://{server_ip}:2019/config",
            sudo=False,
        )
        return local_executor.execute(caddy_api_cmd)
