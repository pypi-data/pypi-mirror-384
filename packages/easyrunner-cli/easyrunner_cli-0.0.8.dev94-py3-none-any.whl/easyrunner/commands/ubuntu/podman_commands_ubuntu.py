from typing import Optional

from ...types import cpu_arch_types
from ...types.os_type import OS
from ..base.podman_commands import PodmanCommands
from ..runnable_command_string import RunnableCommandString


class PodmanCommandsUbuntu(PodmanCommands):
    def __init__(self) -> None:
        super().__init__(
            os=OS.UBUNTU, cpu_arch=cpu_arch_types.CpuArch.X86_64, command_name="podman"
        )
        if self.command_name is None:
            raise ValueError("Package name must be specified for Ubuntu OS")

    def compose_up(self, compose_file: str) -> RunnableCommandString:
        return super().compose_up(compose_file=compose_file)

    def compose_down(self, compose_file: str) -> RunnableCommandString:
        return super().compose_down(compose_file=compose_file)

    def enable_socket(self) -> RunnableCommandString:
        return super().enable_socket()

    def ps(
        self, all_containers: bool = False, format_output: Optional[str] = None
    ) -> RunnableCommandString:
        return super().ps(all_containers=all_containers, format_output=format_output)
