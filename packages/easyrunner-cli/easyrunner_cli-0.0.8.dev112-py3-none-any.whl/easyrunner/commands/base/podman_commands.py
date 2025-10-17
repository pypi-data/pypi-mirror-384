"""
An abstract base class for executing Podman-related commands. It inherits from the CommandsBase class and
provides abstract methods that must be implemented by any subclass OS specific sub classes.

Classes:
    PodmanCommands: An abstract base class for Podman commands.
"""


from typing import Optional

from ...commands.base.systemctl_commands import SystemctlCommands
from ...types import OS, CpuArch, PodmanNetworkDriver
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class PodmanCommands(CommandBase):
    _version_response_prefix: str = "podman version"

    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str) -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name="podman"
        )

    def compose_up(self, compose_file: str) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} compose -f {compose_file} up -d"
        )

    def compose_down(self, compose_file: str) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} compose -f {compose_file} down"
        )

    def network_create(
        self, name: str, driver: PodmanNetworkDriver = PodmanNetworkDriver.BRIDGE
    ) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} network create --driver {driver.value} {name}"
        )

    def network_ls(self, filter_name: Optional[str] = None) -> RunnableCommandString:
        cmd = f"{self.command_name} network ls"
        if filter_name:
            cmd += f" --filter name={filter_name}"
        return RunnableCommandString(command=cmd)

    def network_inspect(self, name: str) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} network inspect {name}"
        )

    def network_rm(self, name: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} network rm {name}")

    def build(
        self,
        containerfile: Optional[str],
        context: Optional[str],
        tags: Optional[list[str]] = None,
        no_cache: bool = False,
    ) -> RunnableCommandString:

        cf_cmds: str = ""
        if containerfile is not None:
            cf_cmds = f" -f {containerfile}"

        if context is None:
            context = "."

        tags_cmd: str = ""
        if tags is not None and len(tags) > 0:
            tags_cmd = " -t " + " -t ".join(tags)

        no_cache_cmd: str = ""
        if no_cache:
            no_cache_cmd = " --no-cache"
        cmd: str = (
            f"{self.command_name} build{no_cache_cmd}{cf_cmds}{tags_cmd} {context}"
        )

        return RunnableCommandString(command=cmd)

    def generate_systemd(
        self,
        container_or_pod: str,
        use_name: bool = False,
        new: bool = False,
        files: bool = False,
        restart_policy: Optional[str] = None,
        stop_timeout: Optional[int] = None,
    ) -> RunnableCommandString:
        """Generate systemd unit files for a container or pod."""
        cmd_parts = [f"{self.command_name}", "generate", "systemd"]
        if use_name:
            cmd_parts.append("--name")
        if new:
            cmd_parts.append("--new")
        if files:
            cmd_parts.append("--files")
        if restart_policy:
            # Add validation for allowed restart policies if needed
            cmd_parts.append(f"--restart-policy={restart_policy}")
        if stop_timeout is not None:
            cmd_parts.append(
                f"--time={stop_timeout}"
            )  # Podman uses --time for stop timeout

        cmd_parts.append(container_or_pod)
        cmd = " ".join(cmd_parts)
        return RunnableCommandString(command=cmd)

    def enable_socket(self) -> RunnableCommandString:
        """
        Generate the command to enable and start the Podman systemd user socket.

        This socket (`podman.socket`) listens for connections to the Podman API.
        When a connection is made (e.g., by podman-compose), systemd activates
        the main Podman service (`podman.service`) to handle the request.
        Enabling this socket is necessary for tools like podman-compose to
        interact with Podman via its API.

        The generated command uses `systemctl --user enable --now` to ensure
        the socket is started immediately and also configured to start
        automatically with the user's session.

        Returns:
            RunnableCommandString: The command string to enable the socket.
        """
        systemctl_cmd = SystemctlCommands(os=self.os, cpu_arch=self.cpu_arch)
        return systemctl_cmd.enable_now(service_name="podman.socket", user_mode=True)

    def ps(
        self, all_containers: bool = False, format_output: Optional[str] = None
    ) -> RunnableCommandString:
        """List containers."""
        cmd = f"{self.command_name} ps"
        if all_containers:
            cmd += " -a"
        if format_output:
            cmd += f" --format '{format_output}'"
        return RunnableCommandString(command=cmd)

    def version(self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} --version")
