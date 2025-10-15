
from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.dir_commands import DirCommands
from ..runnable_command_string import RunnableCommandString


class DirCommandsUbuntu(DirCommands):
    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(
            os=OS.UBUNTU, cpu_arch=cpu_arch, command_name=""
        )

    def mkdir(self, directory: str) -> RunnableCommandString:
        return super().mkdir(directory=directory)

    def chmod(self, mode: str, directory: str) -> RunnableCommandString:
        return super().chmod(mode=mode, directory=directory)

    def dir_exists(self, directory: str) -> RunnableCommandString:
        return super().dir_exists(directory=directory)
