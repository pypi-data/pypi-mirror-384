from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.git_commands import GitCommands
from ..runnable_command_string import RunnableCommandString


class GitCommandsUbuntu(GitCommands):
    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(os=OS.UBUNTU, cpu_arch=cpu_arch, command_name="git")

    def init(self) -> RunnableCommandString:
        return super().init()

    def remote_add_origin(self, repo_url: str) -> RunnableCommandString:
        return super().remote_add_origin(repo_url=repo_url)

    def config_sparse_checkout(self) -> RunnableCommandString:
        return super().config_sparse_checkout()

    def sparse_checkout_add_dirs(self, sub_dir: str) -> RunnableCommandString:
        return super().sparse_checkout_add_dirs(sub_dir=sub_dir)

    def version(self) -> RunnableCommandString:
        return super().version()
