from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.command_base import CommandBase
from ..runnable_command_string import RunnableCommandString


class UtilityCommands(CommandBase):
    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str) -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name=""
        )

    def mkdir(self, directory: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"mkdir -p {directory}", sudo=True)

    def chmod(self, mode: str, file: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"chmod {mode} {file}", sudo=True)

    def dir_exists(self, directory: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"test -d {directory}")

    def version(self) -> RunnableCommandString:
        raise NotImplementedError(
            "version command is not implemented for this OS and CPU architecture"
        )
