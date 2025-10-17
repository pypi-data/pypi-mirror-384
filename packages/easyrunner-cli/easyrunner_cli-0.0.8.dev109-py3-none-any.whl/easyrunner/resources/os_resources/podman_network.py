"""
A resource class for managing Podman networks.
"""

import logging

from ...command_executor import CommandExecutor
from ...commands.base.podman_commands import PodmanCommands
from ...types import ExecResult, PodmanNetworkDriver
from .os_resource_base import OsResourceBase


class PodmanNetwork(OsResourceBase):
    """Resource that represents a Podman networks"""

    def __init__(self, commands: PodmanCommands, executor: CommandExecutor, network_name: str) -> None:
        self._commands = commands
        self._executor = executor
        self._logger = logging.getLogger("easyrunner.podman_network")
        self.network_name: str = network_name

    def network_exists(self) -> bool:
        """
        Ensures that the specified network exists.
        Returns True if the network exists or was created, False otherwise.
        """

        # First check if network exists
        network_ls_result: ExecResult = self._executor.execute(
            self._commands.network_ls(filter_name=self.network_name)
        )

        if network_ls_result.return_code != 0:
            self._logger.error(f"Failed to check if network {self.network_name} exists: {network_ls_result.stderr}")
            return False

        # If network doesn't exist, create it
        # Add null check before using 'in' operator
        if network_ls_result.stdout is not None and self.network_name in network_ls_result.stdout:
            return True
        else:
            return False

    def create_network(self, driver: PodmanNetworkDriver = PodmanNetworkDriver.BRIDGE) -> None:
        """
        Creates a new network with the specified name and driver.
        """
        if not self.network_exists():
            create_result: ExecResult = self._executor.execute(
                self._commands.network_create(name=self.network_name, driver=driver)
            )
            if create_result.return_code != 0:
                self._logger.error(f"Failed to create network {self.network_name}: {create_result.stderr}")
            else:
                self._logger.info(f"Network {self.network_name} created successfully.")
        else:
            self._logger.info(f"Network {self.network_name} already exists. No action taken.")

    def get_network_info(self) -> ExecResult:
        """
        Gets detailed information about a network.
        Returns the raw ExecResult with network information.
        """
        return self._executor.execute(self._commands.network_inspect(self.network_name))
