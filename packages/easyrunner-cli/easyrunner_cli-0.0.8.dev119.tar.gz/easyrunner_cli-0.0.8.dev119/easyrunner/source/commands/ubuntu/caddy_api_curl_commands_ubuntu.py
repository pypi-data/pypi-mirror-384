from ...commands.ubuntu.curl_commands_ubuntu import CurlCommandsUbuntu
from ...types.cpu_arch_types import CpuArch
from ...types.json import JsonObject
from ...types.os_type import OS
from ..base.caddy_api_curl_commands import CaddyApiCurlCommands
from ..runnable_command_string import RunnableCommandString


class CaddyApiCurlCommandsUbuntu(CaddyApiCurlCommands):
    def __init__(self) -> None:
        super().__init__(
            os=OS.UBUNTU,
            cpu_arch=CpuArch.X86_64,
            command_name="",
        )

        self._curl_cmds = CurlCommandsUbuntu()
        self._api_endpoint_address = "http://localhost:2019"
        self._servers_endpoint = "/config/apps/http/servers"
        self._json_header: dict[str, str] = {"Content-Type": "application/json"}

    def reload_config(self) -> RunnableCommandString:
        """
        Create a curl command to reload the Caddy configuration.
        
        Returns:
            RunnableCommandString for reloading Caddy config
        """
        # Caddy's reload config is done with POST to /load
        url: str = f"{self._api_endpoint_address}/load"
        headers: dict[str, str] = self._json_header

        return self._curl_cmds.post(
            url=url,
            headers=headers,
            json_data={}  # Empty payload triggers a reload of the active config
        )

    def add_server_config(self, server_name: str, config: JsonObject) -> RunnableCommandString:
        """
        Create a curl command to add new or replace a server configuration to Caddy.

        Server config in the API json is the same as site config in the Caddyfile.

        Args:
            server_name: The name of the server to configure
            config: The JSON configuration for the server

        Returns:
            RunnableCommandString for adding server config
        """
        # Caddy's server config is managed at /config/apps/http/servers/[server_name]
        url = f"{self._api_endpoint_address}{self._servers_endpoint}/{server_name}"
        headers: dict[str, str] = self._json_header

        # PUT creates a new resource
        return self._curl_cmds.put(
            url=url,
            headers=headers,
            json_data=config
        )

    def merge_into_server_config(
        self, server_name: str, config: JsonObject
    ) -> RunnableCommandString:
        """
        Create a curl command to update an existing server configuration in Caddy.

        It merges config in the `config` arg with the existing server config. That means it will do a partial update rather than replace the entire configuration where the server_name matches. If the `config` contains one property then that the only property that will be updated.

        Args:
            server_name: The name of the server to update
            config: The updated JSON configuration for the server

        Returns:
            RunnableCommandString for updating server config
        """
        # Use the same endpoint but with PATCH which merges with existing config
        url: str = f"{self._api_endpoint_address}{self._servers_endpoint}/{server_name}"
        headers: dict[str, str] = self._json_header

        return self._curl_cmds.patch(
            url=url,
            headers=headers,
            json_data=config
        )

    def get_server_routes_config(self, server_name: str) -> RunnableCommandString:
        """
        Create a curl command to get the routes configuration for a specific server in Caddy.

        Args:
            server_name: The name of the server to get the routes config for

        Returns:
            RunnableCommandString for getting server routes config
        """
        url: str = (
            f"{self._api_endpoint_address}{self._servers_endpoint}/{server_name}/routes"
        )
        headers: dict[str, str] = self._json_header

        return self._curl_cmds.get(url=url, headers=headers)

    def get_server_route_config(
        self,
        server_name: str,
        route_index: int,
    ) -> RunnableCommandString:
        """
        Create a curl command to get a specific route configuration from Caddy.

        Args:
            route_index: The index of the route to get
            server_name: The name of the server to get the route config for

        Returns:
            RunnableCommandString for getting server route config
        """
        url: str = (
            f"{self._api_endpoint_address}{self._servers_endpoint}/{server_name}/routes/{route_index}"
        )
        headers: dict[str, str] = self._json_header

        return self._curl_cmds.get(url=url, headers=headers)

    def add_server_route_config(self, server_name: str, route_config: JsonObject):
        """
        Create a curl command to add a new route configuration to Caddy.

        Args:
            server_name: The name of the server to add the route to
            route_config: The JSON configuration for the new route

        Returns:
            RunnableCommandString for adding server route config
        """
        url: str = (
            f"{self._api_endpoint_address}{self._servers_endpoint}/{server_name}/routes"
        )
        headers: dict[str, str] = self._json_header

        return self._curl_cmds.post(url=url, headers=headers, json_data=route_config)

    def merge_into_server_route_config(
        self, server_name: str, route_index: int, route_config: JsonObject
    ):
        """
        Create a curl command to update an existing route configuration in Caddy.

        It merges config in the `route_config` arg with the existing route config at the specified index. If the `route_config` contains one property then that the only property that will be updated.

        Args:
            server_name: The name of the server to update
            route_index: The index of the route to update
            route_config: The updated JSON configuration for the route

        Returns:
            RunnableCommandString for updating server route config
        """
        url: str = (
            f"{self._api_endpoint_address}{self._servers_endpoint}/{server_name}/routes/{route_index}"
        )
        headers: dict[str, str] = self._json_header

        return self._curl_cmds.patch(url=url, headers=headers, json_data=route_config)

    def get_config(self) -> RunnableCommandString:
        """
        Create a curl command to get the current full Caddy configuration block.

        Returns:
            RunnableCommandString for getting the current config
        """
        url = f"{self._api_endpoint_address}/config/"

        # return RunnableCommandString(command=f"{self.command_name} wget -O - {url}")
        return self._curl_cmds.get(url=url)

    def get_server_config(self, server_name: str) -> RunnableCommandString:
        """
        Create a curl command to get a specific server configuration from Caddy.
        
        Args:
            server_name: The name of the server to get the configuration for
            
        Returns:
            RunnableCommandString for getting server config
        """
        url = f"{self._api_endpoint_address}{self._servers_endpoint}/{server_name}"

        return self._curl_cmds.get(url=url)

    def delete_server_config(self, server_name: str) -> RunnableCommandString:
        """
        Create a curl command to delete a server configuration from Caddy.
        
        Args:
            server_name: The name of the server to delete the configuration for
            
        Returns:
            RunnableCommandString for deleting server config
        """
        url = f"{self._api_endpoint_address}{self._servers_endpoint}/{server_name}"

        return self._curl_cmds.delete(url=url)

    def parse_curl_response_with_status(self, response_output: str) -> tuple[str, int]:
        return self._curl_cmds.parse_curl_response_with_status(response_output)
