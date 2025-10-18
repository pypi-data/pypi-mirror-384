from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.utility_commands import UtilityCommands
from ..runnable_command_string import RunnableCommandString


class UtilityCommandsUbuntu(UtilityCommands):
    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(os=OS.UBUNTU, cpu_arch=cpu_arch, command_name="")

    # TODO: command_name empty is a hack. figure out how to represent commands that don't have sub commands.

    def mkdir(self, directory: str) -> RunnableCommandString:
        return super().mkdir(directory=directory)

    def chmod(self, mode: str, file: str) -> RunnableCommandString:
        return super().chmod(mode=mode, file=file)

    def dir_exists(self, directory: str) -> RunnableCommandString:
        return super().dir_exists(directory=directory)
