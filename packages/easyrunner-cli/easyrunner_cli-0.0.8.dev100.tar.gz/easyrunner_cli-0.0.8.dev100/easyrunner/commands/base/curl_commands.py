"""
Abstract base class for Curl commands.
"""


from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class CurlCommands(CommandBase):
    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str) -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name="curl"
        )

    def version(self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} version")
