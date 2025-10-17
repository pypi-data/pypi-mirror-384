from typing import Optional

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ...types.ssh_key_type import SshKeyType
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class SshKeygenCommands(CommandBase):
    _version_response_prefix: str = "usage: ssh-keygen"

    def __init__(
        self, os: OS, cpu_arch: CpuArch, command_name: str = "ssh-keygen"
    ) -> None:
        super().__init__(
            os=os,
            cpu_arch=cpu_arch,
            command_name=command_name,
            pkg_name="openssh-client",
        )

    def generate_key(
        self,
        key_type: SshKeyType = SshKeyType.ED25519,
        comment: Optional[str] = None,
        output_file: Optional[str] = None,
        passphrase: Optional[str] = None,
        force: bool = False,
    ) -> RunnableCommandString:
        """Generate an SSH key pair.
        Args:
            key_type (SshKeyType): The type of key to generate (e.g., SshKeyType.ED25519, SshKeyType.RSA).
            comment (Optional[str]): A comment to associate with the key.
            output_file (Optional[str]): The file to save the key to.
            passphrase (Optional[str]): A passphrase to encrypt the private key.
            force (bool): Whether to overwrite existing keys.
        Returns:
            RunnableCommandString: The command to run.
        """

        cmd: str = f"{self.command_name} -t {key_type.value}"
        if comment:
            cmd += f" -C '{comment}'"
        if output_file:
            cmd += f" -f '{output_file}'"
        if passphrase is not None:
            cmd += f" -N '{passphrase}'"
        else:
            cmd += " -N ''"
        if force:
            cmd += " -q -y"
        return RunnableCommandString(command=cmd)

    def remove_host_key(self, hostname_or_ip: str) -> RunnableCommandString:
        """Remove a host key from the known_hosts file."""
        return RunnableCommandString(command=f"{self.command_name} -R {hostname_or_ip}")

    def version(self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} -V")
