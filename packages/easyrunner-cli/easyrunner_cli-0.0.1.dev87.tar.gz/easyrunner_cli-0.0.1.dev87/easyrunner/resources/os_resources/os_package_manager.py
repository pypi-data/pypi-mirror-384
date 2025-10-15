from ...command_executor import CommandExecutor
from ...commands.base.command_base import CommandBase
from ...commands.base.os_package_manager_commands import OsPackageManagerCommands
from ...commands.ubuntu.os_package_manager_commands_ubuntu import (
    OsPackageManagerCommandsUbuntu,
)
from ...types.exec_result import ExecResult
from ...types.os_type import OS
from .os_resource_base import OsResourceBase


class OsPackageManager(OsResourceBase):
    def __init__(self, commands: OsPackageManagerCommands, executor: CommandExecutor):
        super().__init__(commands, executor)

        if commands.os == OS.UBUNTU and isinstance(
            commands, OsPackageManagerCommandsUbuntu
        ):
            self.commands: OsPackageManagerCommandsUbuntu = commands
        else:
            raise ValueError("Unsupported OS Package Manager Commands")

    def install_package(self, package_name: str) -> ExecResult:
        """Install a package using the system package manager."""
        result = self.executor.execute(self.commands.install(package_name))
        return result

    def reinstall_package(self, package_name: str) -> ExecResult:
        """Reinstall an already installed package using the system package manager."""
        result = self.executor.execute(self.commands.reinstall(package_name))
        return result

    def remove_package(self, package_name: str) -> ExecResult:
        """Remove a package using the system package manager"""
        result = self.executor.execute(self.commands.remove(package_name))
        return result

    def update_packages(self) -> ExecResult:
        """Retrieve new lists of packages"""
        result = self.executor.execute(self.commands.update())
        return result

    def is_package_installed(self, package_commands: CommandBase) -> bool:
        """Check if a package is installed"""
        self._logger.debug(
            "Checking if package '%s' is installed by running version command",
            package_commands.pkg_name,
        )
        result = self.executor.execute(package_commands.version())
        return (
            result.return_code == 0
            and result.stdout is not None
            and result.stdout.startswith(package_commands.version_response_prefix())
        )

    def fix_dpkg(self) -> ExecResult:
        """Fix dpkg issues"""
        result = self.executor.execute(self.commands.fix_dpkg())
        return result
