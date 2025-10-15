from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class SystemctlCommands(CommandBase):
    """Base class for systemctl commands common across systemd distributions."""

    def __init__(self, os: OS, cpu_arch: CpuArch):
        # systemctl is part of systemd, not a separate package usually.
        super().__init__(os=os, cpu_arch=cpu_arch, command_name="systemctl", pkg_name="no pkg")

    def _build_command(
        self,
        action: str,
        service_name: str,
        user_mode: bool,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Helper method to build a systemctl command."""
        command_parts: list[str] = ["systemctl"]
        if user_mode:
            command_parts.append("--user")
        command_parts.extend([action, service_name])
        command_str: str = " ".join(command_parts)

        # Handle user mode commands with target username (for remote user session management)
        if user_mode and target_username is not None:
            # Use sudo -u with XDG_RUNTIME_DIR for systemd user session commands
            enhanced_command = f"sudo -u {target_username} XDG_RUNTIME_DIR=/run/user/1000 {command_str}"
            return RunnableCommandString(command=enhanced_command, sudo=True)
        else:
            # System-wide commands require sudo, user commands do not.
            return RunnableCommandString(command=command_str, sudo=not user_mode)

    def start(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to start a systemd service."""
        return self._build_command("start", service_name, user_mode, target_username)

    def stop(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to stop a systemd service."""
        return self._build_command("stop", service_name, user_mode, target_username)

    def restart(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to restart a systemd service."""
        return self._build_command("restart", service_name, user_mode, target_username)

    def status(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to check the status of a systemd service."""
        # Status check typically doesn't modify state, so sudo might not be strictly necessary,
        # but keeping it consistent with other actions for system-wide services.
        return self._build_command("status", service_name, user_mode, target_username)

    def enable(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to enable a systemd service (start on boot)."""
        return self._build_command("enable", service_name, user_mode, target_username)

    def disable(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to disable a systemd service (don't start on boot)."""
        return self._build_command("disable", service_name, user_mode, target_username)

    def enable_now(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to enable and immediately start a systemd service."""
        return self._build_command(
            "enable --now", service_name, user_mode, target_username
        )

    def daemon_reload(
        self, user_mode: bool = True, target_username: str | None = None
    ) -> RunnableCommandString:
        """Generates a command to reload the systemd manager configuration."""
        return self._build_command(
            "daemon-reload", "", user_mode, target_username
        )  # service_name is not applicable here

    def is_active(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to check if a service is active (returns exit code 0 if active)."""
        return self._build_command(
            "is-active", service_name, user_mode, target_username
        )

    def is_enabled(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to check if a service is enabled (returns exit code 0 if enabled)."""
        return self._build_command(
            "is-enabled", service_name, user_mode, target_username
        )

    def is_failed(
        self,
        service_name: str,
        user_mode: bool = True,
        target_username: str | None = None,
    ) -> RunnableCommandString:
        """Generates a command to check if a service is in a failed state (returns exit code 0 if failed)."""
        return self._build_command(
            "is-failed", service_name, user_mode, target_username
        )

    def version(self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} --version")
