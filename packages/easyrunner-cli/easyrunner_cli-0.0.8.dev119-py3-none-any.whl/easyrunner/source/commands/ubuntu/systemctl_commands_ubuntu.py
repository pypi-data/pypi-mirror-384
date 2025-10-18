from ...commands.runnable_command_string import RunnableCommandString
from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.systemctl_commands import SystemctlCommands


class SystemctlCommandsUbuntu(SystemctlCommands):
    """Implementation of systemctl commands for Ubuntu."""

    def __init__(self):
        super().__init__(os=OS.UBUNTU, cpu_arch=CpuArch.X86_64)

    def version(self) -> RunnableCommandString:
        return super().version()

    # Currently, no Ubuntu-specific overrides are needed for the basic systemctl commands.
    # If specific flags or behaviors were required for Ubuntu, they would be implemented here.
