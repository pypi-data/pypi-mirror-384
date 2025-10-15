from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.command_base import CommandBase
from ..runnable_command_string import RunnableCommandString


class DirCommands(CommandBase):
    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str) -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name="null_pkg"
        )

    def mkdir(self, directory: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"mkdir -p {directory}", sudo=True)

    def rm(self, directory: str) -> RunnableCommandString:
        """Runs `rm -rf` so blows away the directory and all it's content with no further warning or confirmation."""
        return RunnableCommandString(command=f"rm -rf {directory}", sudo=True)

    def install(
        self, directory: str, owner: str, group: str, mode: str = "750"
    ) -> RunnableCommandString:
        # sudo false and owner required so that we can always create dir with the correct permissions.
        return RunnableCommandString(
            command=f"install -d -o {owner} -g {group} -m {mode} {directory}",
            sudo=False,
        )

    def chmod(self, mode: str, directory: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"chmod {mode} {directory}", sudo=True)

    def chown(
        self, owner: str, directory: str, recursive: bool = False
    ) -> RunnableCommandString:
        recursive_flag: str = ""
        if recursive:
            recursive_flag = " -R"
        return RunnableCommandString(
            command=f"chown{recursive_flag} {owner} {directory}", sudo=True
        )

    def dir_exists(self, directory: str) -> RunnableCommandString:
        # return RunnableCommandString(command=f"test -d {directory}")
        return RunnableCommandString(
            command=f"[ -d {directory} ] && echo 'exists true' || echo 'exists false';"
        )

    def ls(self, directory: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"ls -als {directory}", sudo=False)

    def version(self) -> RunnableCommandString:
        return super().version()
