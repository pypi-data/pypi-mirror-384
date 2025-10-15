from typing import List, Optional

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.archive_commands import ArchiveCommands
from ..runnable_command_string import RunnableCommandString
from .os_package_manager_commands_ubuntu import OsPackageManagerCommandsUbuntu


class ArchiveCommandsUbuntu(ArchiveCommands):
    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(os=OS.UBUNTU, cpu_arch=cpu_arch, command_name="tar")

    def install(self) -> RunnableCommandString:
        os_pkg_mgr = OsPackageManagerCommandsUbuntu(cpu_arch=self.cpu_arch)
        return os_pkg_mgr.install(self.pkg_name)

    def create(self, archive_name: str, files: List[str], compress: bool = True) -> RunnableCommandString:
        return super().create(archive_name=archive_name, files=files, compress=compress)

    def extract(self, archive_name: str, target_dir: Optional[str] = None) -> RunnableCommandString:
        return super().extract(archive_name=archive_name, target_dir=target_dir)

    def list_contents(self, archive_name: str) -> RunnableCommandString:
        return super().list_contents(archive_name=archive_name)
        
    def version(self) -> RunnableCommandString:
        return super().version()
