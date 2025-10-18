from typing import Optional, Self

from ...commands.base.os_package_manager_commands import OsPackageManagerCommands
from ...commands.runnable_command_string import RunnableCommandString
from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS


class OsPackageManagerCommandsUbuntu(OsPackageManagerCommands):
    def __init__(
        self, cpu_arch: CpuArch, silent: bool = True, debug: bool = False
    ) -> None:
        super().__init__(os=OS.UBUNTU, cpu_arch=cpu_arch, command_name="apt-get")
        self.silent: bool = silent
        self.debug: bool = debug
        self.env: dict[str, str] | None = (
            {"DEBIAN_FRONTEND": "noninteractive"} if self.silent else None
        )

    def install(self: Self, package_name: str) -> RunnableCommandString:
        if not package_name:
            raise ValueError("Package name must be specified")

        return RunnableCommandString(
            command=f"{self.command_name} install -y {package_name}",
            sudo=True,
            env=self.env,
        )

    def reinstall(self: Self, package_name: str) -> RunnableCommandString:
        if not package_name:
            raise ValueError("Package name must be specified")

        return RunnableCommandString(
            command=f"{self.command_name} install --reinstall -y {package_name}",
            sudo=True,
            env=self.env,
        )

    def fix_dpkg(self: Self) -> RunnableCommandString:
        return RunnableCommandString(
            command="dpkg --configure -a",
            sudo=True,
            env=self.env,
        )

    def _upgrade(self, package_name: Optional[str] = None) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} upgrade -y {package_name}", sudo=True
        )

    def remove(self, package_name: str) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} remove -y {package_name}", sudo=True
        )

    def update(self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} update", sudo=True)

    def version(self) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} --version", sudo=True
        )

    def version_response_prefix(self) -> str:
        return "apt version"
