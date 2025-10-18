from typing import Optional

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class SshAgentCommands(CommandBase):
    """Base class for ssh-agent commands common across Unix/Linux distributions."""

    def __init__(
        self, os: OS, cpu_arch: CpuArch, command_name: str = "ssh-agent"
    ) -> None:
        super().__init__(
            os=os,
            cpu_arch=cpu_arch,
            command_name=command_name,
            pkg_name="openssh-client",
        )

    def start_background(
        self, socket_path: Optional[str] = None
    ) -> RunnableCommandString:
        """Start ssh-agent in background mode."""
        if socket_path:
            cmd = f"{self.command_name} -s -a {socket_path}"
        else:
            cmd = f"{self.command_name} -s"
        return RunnableCommandString(command=cmd)

    def kill(self, pid: Optional[str] = None) -> RunnableCommandString:
        """Kill ssh-agent process.

        Args:
            pid: Optional PID of the ssh-agent process. If not provided,
                uses the SSH_AGENT_PID environment variable.

        Returns:
            RunnableCommandString: Command to kill ssh-agent
        """
        if pid:
            cmd = f"{self.command_name} -k {pid}"
        else:
            cmd = f"{self.command_name} -k"
        return RunnableCommandString(command=cmd)

    def check_running(self) -> RunnableCommandString:
        # Keep simple; resource sets SSH_AUTH_SOCK env and runs ssh-add -l itself
        return RunnableCommandString(command="ssh-add -l")

    def get_agent_pid(self) -> RunnableCommandString:
        """Get the SSH agent process ID from environment or process list.

        Returns:
            RunnableCommandString: Command to get SSH agent PID
        """
        # First try to get from environment variable, then fallback to process search
        return RunnableCommandString(
            command="echo ${SSH_AGENT_PID:-$(pgrep ssh-agent | head -1)}"
        )

    def get_socket_path(self) -> RunnableCommandString:
        """Get the SSH agent socket path from environment.

        Returns:
            RunnableCommandString: Command to get SSH agent socket path
        """
        return RunnableCommandString(command="echo $SSH_AUTH_SOCK")

    def kill_all_agents(self) -> RunnableCommandString:
        """Kill all ssh-agent processes for the current user.

        Returns:
            RunnableCommandString: Command to kill all ssh-agent processes
        """
        return RunnableCommandString(command="pkill -u $USER ssh-agent")

    def add_key_from_content(
        self, private_key_content: str, comment_content: Optional[str] = None
    ) -> RunnableCommandString:
        """Add a private key to ssh-agent from content.

        Args:
            private_key_content: The content of the private key to add
            comment_content: Optional comment to associate with the key. Use to store metadata.

        Returns:
            RunnableCommandString: Command to add the key to ssh-agent
        """        
        # Only add key to the agent pointed by SSH_AUTH_SOCK
        return RunnableCommandString(command=f"ssh-add - <<'EOF'\n{private_key_content}\nEOF")

    def add_key_from_file(self, key_file_path: str) -> RunnableCommandString:
        """Add a private key to ssh-agent from file.

        Args:
            key_file_path: Path to the private key file

        Returns:
            RunnableCommandString: Command to add the key file to ssh-agent
        """
        return RunnableCommandString(command=f"ssh-add {key_file_path}")

    def list_keys(self) -> RunnableCommandString:
        """List all keys currently loaded in ssh-agent.

        Returns:
            RunnableCommandString: Command to list keys in ssh-agent
        """
        return RunnableCommandString(command="ssh-add -l")

    def remove_key(self, key_file_path: str) -> RunnableCommandString:
        """Remove a specific key from ssh-agent.

        Args:
            key_file_path: Path to the private key file to remove

        Returns:
            RunnableCommandString: Command to remove the key from ssh-agent
        """
        return RunnableCommandString(command=f"ssh-add -d {key_file_path}")

    def remove_all_keys(self) -> RunnableCommandString:
        """Remove all keys from ssh-agent.

        Returns:
            RunnableCommandString: Command to remove all keys from ssh-agent
        """
        # Ensure ssh-agent is available before removing keys
        cmd = "ssh-add -D 2>/dev/null || (eval $(ssh-agent -s) && ssh-add -D)"
        return RunnableCommandString(command=cmd)

    def version(self) -> RunnableCommandString:
        """Get ssh-agent version information.

        Returns:
            RunnableCommandString: Command to get version information
        """
        # ssh-agent doesn't have a version flag, but we can check ssh version
        return RunnableCommandString(command="ssh -V")
