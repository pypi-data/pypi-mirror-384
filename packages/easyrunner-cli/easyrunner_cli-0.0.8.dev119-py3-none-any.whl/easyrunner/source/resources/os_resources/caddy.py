from typing import Self

from .... import logger
from ...command_executor import CommandExecutor
from ...commands.runnable_command_string import RunnableCommandString
from ...commands.ubuntu.caddy_api_curl_commands_ubuntu import CaddyApiCurlCommandsUbuntu
from ...commands.ubuntu.caddy_commands_container_ubuntu import (
    CaddyCommandsContainerUbuntu,
)
from ...types.exec_result import ExecResult
from ...types.json import JsonObject, to_json_array_safe, to_json_object_safe
from .os_resource_base import OsResourceBase


class Caddy(OsResourceBase):
    """Represents the Caddy web server."""

    def __init__(
        self, commands: CaddyCommandsContainerUbuntu, executor: CommandExecutor
    ):
        super().__init__(commands=commands, executor=executor)

        self._commands: CaddyCommandsContainerUbuntu = commands
        self._caddy_api_curl_cmd = CaddyApiCurlCommandsUbuntu()

    def validate_config(self: Self, config_path: str) -> ExecResult:
        """Validate the Caddy configuration."""
        command: RunnableCommandString = self._commands.validate_config(config_path)
        return self.executor.execute(command)

    def reload_config(self) -> ExecResult:
        """Reload the Caddy configuration."""
        command: RunnableCommandString = self._commands.reload_config()
        return self.executor.execute(command)

    def get_server_config(self, server_name: str) -> ExecResult[JsonObject | None]:
        """Get the configuration for a specific server in Caddy.

        Args:
            server_name: The name of the Caddy server config block to get
        """
        command: RunnableCommandString = self._caddy_api_curl_cmd.get_server_config(
            server_name
        )
        return self._handle_response(self.executor.execute(command))

    def get_server_sites(self, server_name: str) -> ExecResult[list[JsonObject] | None]:
        """Get the list of sites for a specific server in Caddy.

        Args:
            server_name: The name of the Caddy server config block to get sites for
        """
        command: RunnableCommandString = (
            self._caddy_api_curl_cmd.get_server_routes_config(server_name)
        )
        return self._handle_array_response(self.executor.execute(command))

    def get_server_site_config(
        self, server_name: str, hostname: str
    ) -> ExecResult[JsonObject | None]:
        """Get the configuration for a specific site in Caddy.

        Args:
            server_name: The name of the Caddy server config block
            hostname: The primary hostname of the site config block to get
        """

        site_result = ExecResult[JsonObject | None]()
        site_result.success = False

        route_index_result = self._get_server_route_index(
            server_name=server_name, hostname=hostname
        )
        if not route_index_result.success or route_index_result.result is None:
            site_result.return_code = 1
            site_result.stderr = (
                f"A route index for hostname '{hostname}' was not found."
            )
            return site_result

        # Ensure we have an integer index
        if not isinstance(route_index_result.result, int):
            return site_result

        command: RunnableCommandString = (
            self._caddy_api_curl_cmd.get_server_route_config(
                server_name, route_index_result.result
            )
        )
        return self._handle_response(self.executor.execute(command))

    def site_exists(self, server_name: str, hostname: str) -> bool:
        """Check if a site configuration exists in Caddy.

        Args:
            hostname: The primary domain name for the site
            server_name: The name of the Caddy server config block to check

        Returns:
            bool: True if the site exists, False otherwise
        """
        server_config_result = self.get_server_site_config(
            server_name=server_name, hostname=hostname
        )

        return server_config_result.success

    def server_exists(self, server_name: str) -> bool:
        """Check if a server configuration exists in Caddy.

        Args:
            server_name: The name of the server to check

        Returns:
            bool: True if the server exists, False otherwise
        """
        server_config_result = self.get_server_config(server_name)

        logger.debug(
            f">>>>Server config for '{server_name}' exists: {repr(server_config_result)}, results: {server_config_result.result}."
        )
        if (
            server_config_result.return_code == 200
            and server_config_result.result is None
        ):
            return False
        elif server_config_result.return_code == 500:
            return False
        else:
            return True

    def add_server_config(
        self, server_name: str, config: JsonObject
    ) -> ExecResult[JsonObject | None]:
        """Add or replace a server configuration in Caddy.

        If a site configuration node with key `site_name` already exists, it will be replaced. Otherwise a new one will be created.
        """
        command: RunnableCommandString = self._caddy_api_curl_cmd.add_server_config(
            server_name, config
        )
        return self._handle_response(self.executor.execute(command))

    def add_site_config(
        self, server_name: str, hostname: str, site_config: JsonObject
    ) -> ExecResult[JsonObject | None]:
        """Add or replace a site configuration in Caddy."""
        if self.site_exists(server_name, hostname):
            return ExecResult[JsonObject | None](
                success=False,
                return_code=1,
                stderr=f"Site with the hostname '{hostname}' already exists therefore cannot add. Each site must have a unique hostname(s).",
            )
        command: RunnableCommandString = (
            self._caddy_api_curl_cmd.add_server_route_config(server_name, site_config)
        )
        return self._handle_response(self.executor.execute(command))

    def delete_site_config(self, site_name: str) -> ExecResult[JsonObject | None]:
        """Delete a site configuration in Caddy."""
        command: RunnableCommandString = self._caddy_api_curl_cmd.delete_server_config(
            site_name
        )
        return self._handle_response(self.executor.execute(command))

    def merge_into_server_config(
        self, server_name: str, site_config: JsonObject
    ) -> ExecResult[JsonObject | None]:
        """Update a site configuration in Caddy by merging just the provided config into the existing one and preserving the rest."""
        command: RunnableCommandString = (
            self._caddy_api_curl_cmd.merge_into_server_config(server_name, site_config)
        )
        return self._handle_response(self.executor.execute(command))

    def merge_into_server_site_config(
        self, server_name: str, hostname: str, config: JsonObject
    ) -> ExecResult[JsonObject | None]:
        """Update a server route configuration in Caddy
        by merging just the provided config into the existing one and preserving the rest.
        """
        site_route_index = self._get_server_route_index(server_name, hostname)
        if not site_route_index.success or site_route_index.result is None:
            return ExecResult[JsonObject | None](
                success=False,
                return_code=1,
                stderr=f"Site route not found for hostname: {hostname}.",
            )

        # Type guard: ensure we have an integer route index
        route_index = site_route_index.result
        if not isinstance(route_index, int):
            raise ValueError(
                f"Invalid route index type for hostname: {hostname}. route_index must be an Int."
            )

        command: RunnableCommandString = (
            self._caddy_api_curl_cmd.merge_into_server_route_config(
                server_name, route_index, config
            )
        )
        return self._handle_response(self.executor.execute(command))

    def get_config(self) -> ExecResult[JsonObject | None]:
        """Get the full Caddy configuration."""
        command: RunnableCommandString = self._caddy_api_curl_cmd.get_config()
        return self._handle_response(self.executor.execute(command))

    def _get_server_route_index(
        self, server_name: str, hostname: str
    ) -> ExecResult[int | None]:
        """Get the index of a server route by its hostname.

        Returns the index of the FIRST route found with the specified hostname.
        If multiple routes exist with the same hostname (duplicates), this will
        return the index of the first one encountered.

        Args:
            server_name: The Caddy server name to search in
            hostname: The exact hostname to search for in route match conditions

        Returns:
            ExecResult containing the route index (int) if found, None if not found
        """
        command: RunnableCommandString = (
            self._caddy_api_curl_cmd.get_server_routes_config(server_name)
        )

        routes_result = self._handle_array_response(self.executor.execute(command))

        if not routes_result.success:
            result = ExecResult[int | None](success=False)
            result.result = None
            result.stderr = f"Failed to get routes for server '{server_name}': {routes_result.stderr}"
            return result

        if not routes_result.result:
            # No routes exist for this server
            result = ExecResult[int | None](success=False)
            result.result = None
            return result

        # Find the index of the route that has the hostname
        for index, route in enumerate(routes_result.result):
            if not isinstance(route, dict):
                continue

            # Extract hostnames from the match array
            match_array = route.get("match", [])
            if not isinstance(match_array, list):
                continue

            for match_item in match_array:
                if not isinstance(match_item, dict):
                    continue

                host_array = match_item.get("host", [])
                if isinstance(host_array, list) and hostname in host_array:
                    result = ExecResult[int | None](success=True)
                    result.result = index
                    return result

        # Hostname not found in any route
        result = ExecResult[int | None](success=False)
        result.result = None
        return result

    def _handle_response(self, response: ExecResult) -> ExecResult[JsonObject | None]:
        """
        Handle null responses from the Caddy API when the resource doesn't exist.

        If the response is None or empty, return an empty ExecResult.
        """
        logger.debug(
            f"_handle_response() > mapping Caddy API response: {repr(response)}"
        )

        result: ExecResult[JsonObject | None] = ExecResult[JsonObject | None](
            success=response.success,
            stdout=response.stdout,
            stderr=response.stderr,
            return_code=response.return_code,
            command=response.command,
        )

        if response.stdout is not None:
            body, status_code = (
                self._caddy_api_curl_cmd.parse_curl_response_with_status(
                    response.stdout
                )
            )

            result.return_code = status_code
            logger.debug(f"_handle_response() > status code: {result.return_code}")
            if body.strip() == "null":
                logger.debug(
                    f"_handle_response() > body contains `null`: '{body.strip()}'"
                )
                result.result = None

            else:
                result.result = to_json_object_safe(body)
        else:
            logger.debug(f"_handle_response() > stdout is None: {response.stdout}")

        logger.debug(
            f"_handle_response() > returning result: {repr(result)}, result: '{result.result}'"
        )
        return result

    def _handle_array_response(
        self, response: ExecResult
    ) -> ExecResult[list[JsonObject] | None]:
        """
        Handle JSON array responses from the Caddy API when the resource doesn't exist.

        If the response is None or empty, return None.
        """
        logger.debug(
            f"_handle_array_response() > mapping Caddy API response: {repr(response)}"
        )
        result: ExecResult[list[JsonObject] | None] = ExecResult[
            list[JsonObject] | None
        ](
            success=response.success,
            stdout=response.stdout,
            stderr=response.stderr,
            return_code=response.return_code,
            command=response.command,
        )
        if result.stdout is not None:
            body, status_code = (
                self._caddy_api_curl_cmd.parse_curl_response_with_status(result.stdout)
            )
            result.return_code = status_code

            if body.strip() == "null":
                result.result = None
            else:
                json_array = to_json_array_safe(body)
                if json_array is not None:
                    # Filter to only JsonObject items
                    json_objects = [
                        item for item in json_array if isinstance(item, dict)
                    ]
                    result.result = json_objects
                else:
                    result.result = None

        return result
