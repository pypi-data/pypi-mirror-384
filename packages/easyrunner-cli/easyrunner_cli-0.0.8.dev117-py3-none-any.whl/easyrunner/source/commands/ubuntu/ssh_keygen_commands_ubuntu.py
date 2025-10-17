from typing import Optional

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ...types.ssh_key_type import SshKeyType
from ..base.ssh_keygen_commands import SshKeygenCommands
from ..runnable_command_string import RunnableCommandString


class SshKeygenCommandsUbuntu(SshKeygenCommands):
    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(os=OS.UBUNTU, cpu_arch=cpu_arch, command_name="ssh-keygen")

    def generate_key(
        self,
        key_type: SshKeyType = SshKeyType.ED25519,
        comment: Optional[str] = None,
        output_file: Optional[str] = None,
        passphrase: Optional[str] = None,
        force: bool = False
    ) -> RunnableCommandString:
        return super().generate_key(
            key_type=key_type,
            comment=comment,
            output_file=output_file,
            passphrase=passphrase,
            force=force
        )

    def version(self) -> RunnableCommandString:
        return super().version()
