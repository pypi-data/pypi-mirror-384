from typing import Self

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class IpTablesPersistentCommands(CommandBase):

    def __init__(
        self, os: OS, cpu_arch: CpuArch, command_name: str = "iptables-save"
    ) -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name="iptables-save"
        )

    def save_ipv4(self: Self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} > /etc/iptables/rules.v4", sudo=True)

    def save_ipv6(self: Self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} > /etc/iptables/rules.v6", sudo=True)

    def verify_ipv4_rules_loaded(self: Self) -> RunnableCommandString:
        return RunnableCommandString(command="iptables -L", sudo=True)

    def verify_ipv6_rules_loaded(self: Self) -> RunnableCommandString:
        return RunnableCommandString(command="ip6tables -L", sudo=True)

    def version(self: Self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} --version")

    def version_response_prefix(self: Self) -> str:
        return f"{self.command_name} v"
