"""
Abstract base class for OS package manager commands.

This class provides an interface for package management operations such as
installing, upgrading, and removing packages. Subclasses must implement
the following abstract methods:
"""

from abc import abstractmethod
from typing import Optional, Self

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class OsPackageManagerCommands(CommandBase):
    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str):
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name=""
        )

    @abstractmethod
    def install(self: Self, package_name: str) -> RunnableCommandString:
        """The command to install a package."""
        pass

    def upgrade_one(self, package_name: str) -> RunnableCommandString:
        """The command to upgrade a single package."""
        return self._upgrade(package_name=package_name)

    def upgrade_all(self) -> RunnableCommandString:
        """The command to upgrade all installed packages."""
        return self._upgrade()

    @abstractmethod
    def _upgrade(self, package_name: Optional[str] = None) -> RunnableCommandString:
        """The command to actually download and install the latest version
        of package(s) that are *already installed* on the system.

        Args:
            package_name (Optional[str], optional): The name of the package to upgrade.
                If None, all installed packages will be upgraded. Defaults to None.
        """
        pass

    @abstractmethod
    def remove(self, package_name: str) -> RunnableCommandString:
        pass

    @abstractmethod
    def update(self) -> RunnableCommandString:
        """The command to update the local package cache with the latest
        information about available packages and their versions from the
        configured repositories."""
        pass

    @abstractmethod
    def version(self) -> RunnableCommandString:
        """The command to get the version of the package manager."""
        pass
