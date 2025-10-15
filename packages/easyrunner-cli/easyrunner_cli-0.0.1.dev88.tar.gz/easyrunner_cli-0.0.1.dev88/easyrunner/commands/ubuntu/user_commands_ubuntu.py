from ...commands.base.user_commands import UserCommands
from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString


class UserCommandsUbuntu(UserCommands):
    """Ubuntu-specific implementation of user management commands."""

    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(os=OS.UBUNTU, cpu_arch=cpu_arch)

    def version(self) -> RunnableCommandString:
        """Get version information for useradd command on Ubuntu."""
        return super().version()

    # Ubuntu uses the same user management commands as other Linux distributions,
    # so no Ubuntu-specific overrides are currently needed.
    # If Ubuntu-specific behaviors were required (like different default paths,
    # special group handling, etc.), they would be implemented here.
