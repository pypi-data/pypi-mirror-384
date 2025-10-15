"""
Abstract base class for Docker Compose commands.

This class defines the interface for Docker Compose commands that must be
implemented by OS specific subclasses. It includes methods for installing Docker Compose,
bringing up services defined in a Docker Compose file, and bringing them down.
"""

from abc import abstractmethod
from typing import Literal, Optional

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class DockerComposeCommands(CommandBase):
    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str) -> None:
        super().__init__(
            os=os,
            cpu_arch=cpu_arch,
            command_name=command_name,
            pkg_name="docker-compose",
        )

    @abstractmethod
    def up(self, compose_file: str, daemon_mode: bool = True) -> RunnableCommandString:
        daemon_flag: Literal[" -d"] | Literal[""] = " -d" if daemon_mode else ""
        return RunnableCommandString(
            command=f"{self.command_name} -f {compose_file} up{daemon_flag}"
        )

    @abstractmethod
    def down(self, compose_file: str) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} -f {compose_file} down"
        )

    def upgrade(self) -> RunnableCommandString:
        return self._upgrade(package_name=self.command_name)

    @abstractmethod
    def _upgrade(self, package_name: Optional[str] = None) -> RunnableCommandString:
        pass

    def version(self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} --version")
