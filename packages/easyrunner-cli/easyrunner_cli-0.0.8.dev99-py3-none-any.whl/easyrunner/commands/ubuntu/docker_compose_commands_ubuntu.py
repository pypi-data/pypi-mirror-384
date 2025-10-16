from typing import Optional

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.docker_compose_commands import (
    DockerComposeCommands,
)
from ..runnable_command_string import RunnableCommandString
from .os_package_manager_commands_ubuntu import (
    OsPackageManagerCommandsUbuntu,
)


class DockerComposeCommandsUbuntu(DockerComposeCommands):
    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(os=OS.UBUNTU, cpu_arch=cpu_arch, command_name="docker-compose")
        if self.command_name is None:
            raise ValueError("Package name must be specified for Ubuntu OS")

    def install(self) -> RunnableCommandString:
        return OsPackageManagerCommandsUbuntu(cpu_arch=self.cpu_arch).install(
            package_name=self.__command_name  # type: ignore
        )

    def up(self, compose_file: str, daemon_mode: bool = True) -> RunnableCommandString:
        return super().up(compose_file=compose_file, daemon_mode=daemon_mode)

    def down(self, compose_file: str) -> RunnableCommandString:
        return super().down(compose_file=compose_file)

    def _upgrade(self, package_name: Optional[str] = None) -> RunnableCommandString:
        return OsPackageManagerCommandsUbuntu(cpu_arch=self.cpu_arch)._upgrade(
            package_name=package_name
        )
