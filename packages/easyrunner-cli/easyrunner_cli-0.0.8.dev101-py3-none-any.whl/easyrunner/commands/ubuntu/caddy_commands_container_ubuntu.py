import os
from typing import Optional

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.caddy_commands import (
    CaddyCommands,
)
from ..runnable_command_string import RunnableCommandString


class CaddyCommandsContainerUbuntu(CaddyCommands):
    """Handles executing Caddy commands in side the container via `podman exec`."""

    _caddy_container_name: str = "systemd-easyrunner__caddy"

    def __init__(self, cpu_arch: CpuArch) -> None:
        super().__init__(
            os=OS.UBUNTU,
            cpu_arch=cpu_arch,
            command_name=f"podman exec -w /etc/caddy {self._caddy_container_name} caddy",
        )
        # podman exec -w /etc/caddy <container_name> caddy <command>

    def reload_config(self) -> RunnableCommandString:
        """After updating the Caddyfile, call this to trigger hot reload the configuration.
        Best to call validate_config before this to ensure the new configuration is valid.
        """
        return RunnableCommandString(command=f"{self.command_name} reload")

    def validate_config(
        self, config_path: Optional[str] = None
    ) -> RunnableCommandString:
        """Validate the Caddyfile configuration before applying it.

        Args:
            config_path (Optional[str]): Path to the Caddyfile. If None, uses the default path. Note this must be a valid path inside the container
        """
        if config_path is not None and not self._is_valid_path(config_path):
            raise ValueError("Invalid path specified")

        cfg_cmd: str = ""
        if config_path is not None:
            cfg_cmd = f" --config {config_path.strip()}"

        return RunnableCommandString(
            command=f"{self.command_name} validate{cfg_cmd}",
        )

    def _is_valid_path(self, path: str) -> bool:
        valid = False
        # TODO: move to a shared helper library
        # Check if path is a string and not empty
        if isinstance(path, str) and path.strip():
            # Remove any null bytes that could be used for injection
            clean_path = path.replace("\0", "")
            # Check if path contains valid characters and follows path format
            if os.path.normpath(clean_path) == clean_path and not any(
                char in clean_path for char in ["|", "&", ";", "$", ">", "<"]
            ):
                valid = True

        return valid
