from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.ssh_agent_commands import SshAgentCommands
from ..runnable_command_string import RunnableCommandString


class SshAgentCommandsUbuntu(SshAgentCommands):
    """Ubuntu-specific implementation of ssh-agent commands."""

    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(os=OS.UBUNTU, cpu_arch=cpu_arch, command_name="ssh-agent")

    def version(self) -> RunnableCommandString:
        """Get ssh-agent version information for Ubuntu."""
        return super().version()

    # Ubuntu uses the same ssh-agent commands as other Linux distributions,
    # so no Ubuntu-specific overrides are currently needed.
    # If Ubuntu-specific behaviors were required (like different default paths,
    # special environment handling, etc.), they would be implemented here.
