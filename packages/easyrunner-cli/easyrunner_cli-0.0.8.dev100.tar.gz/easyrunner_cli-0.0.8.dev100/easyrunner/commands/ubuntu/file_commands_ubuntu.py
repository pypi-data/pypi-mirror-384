from ...commands.base.file_commands import FileCommands
from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS


class FileCommandsUbuntu(FileCommands):
    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(
            os=OS.UBUNTU, cpu_arch=cpu_arch, command_name=""
        )

