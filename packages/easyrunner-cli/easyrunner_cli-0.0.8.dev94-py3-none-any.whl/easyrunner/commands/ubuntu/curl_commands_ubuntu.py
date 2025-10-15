from typing import Dict, Optional, Union

from ...commands.base.curl_commands import CurlCommands
from ...commands.runnable_command_string import RunnableCommandString
from ...types.cpu_arch_types import CpuArch
from ...types.json import JsonArray, JsonObject
from ...types.os_type import OS


class CurlCommandsUbuntu(CurlCommands):
    def __init__(self) -> None:
        super().__init__(
            os=OS.UBUNTU, cpu_arch=CpuArch.X86_64, command_name="curl"
        )

    def _build_base_command(self, method: Optional[str] = None) -> str:
        """
        Build the base curl command with silent flag and optional HTTP method.

        Args:
            method: Optional HTTP method (GET, POST, PUT, etc.)

        Returns:
            Base command string with silent flag and response code
        """
        # Use a unique delimiter that won't appear in response bodies
        delimiter = "|||HTTP_STATUS|||"
        # Only return numeric status code - most reliable and sufficient for API logic
        base_cmd = f"{self.command_name} -s -w '{delimiter}%{{http_code}}'"
        if method:
            base_cmd += f" -X {method}"
        return base_cmd

    def _add_headers(self, command: str, headers: Optional[Dict[str, str]] = None) -> str:
        """
        Helper method to add headers to a curl command
        
        Args:
            command: The current command string
            headers: Dictionary of headers to include
            
        Returns:
            Updated command string with headers
        """
        if headers:
            for key, value in headers.items():
                command += f" -H '{key}: {value}'"
        return command

    def _add_data(self, command: str, data: Optional[str] = None, 
                 json_data: Optional[JsonObject | JsonArray] = None, 
                 headers: Optional[Dict[str, str]] = None) -> str:
        """
        Helper method to add data to a curl command

        Args:
            command: The current command string
            data: Optional string data to send in the request body. If this is provided `json_data` must be omitted.
            json_data: Optional JSON data to send in the request body. If this is provided `data` must be omitted.
            headers: Optional headers (used to check for Content-Type)

        Returns:
            Updated command string with data payload
        """

        if json_data and data:
            raise ValueError(
                "Cannot provide both 'data' and 'json_data'. Use one or the other."
            )

        if json_data:
            if not headers or not any(k.lower() == 'content-type' for k in headers):
                command += " -H 'Content-Type: application/json'"
            import json
            command += f" -d '{json.dumps(json_data)}'"
        elif data:
            command += f" -d '{data}'"
        return command

    def _format_url_with_params(self, url: str, params: Optional[Dict[str, str]] = None) -> str:
        """
        Helper method to format URL with query parameters
        
        Args:
            url: The base URL
            params: Optional query parameters to append
            
        Returns:
            Formatted URL with parameters
        """
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            if "?" in url:
                return f"{url}&{param_str}"
            else:
                return f"{url}?{param_str}"
        return url

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl GET request command
        
        Args:
            url: The URL to send the GET request to
            headers: Optional dictionary of headers to include
            params: Optional query parameters
            
        Returns:
            RunnableCommandString for a curl GET request
        """
        formatted_url = self._format_url_with_params(url, params)
        command = self._build_base_command("GET")
        command += f" '{formatted_url}'"
        command = self._add_headers(command, headers)

        return RunnableCommandString(command=command)

    def post(self, url: str, data: Optional[str] = None, json_data: Optional[JsonObject | JsonArray] = None, 
             headers: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl POST request command
        
        Args:
            url: The URL to send the POST request to
            data: Optional string data to send in the request body
            json_data: Optional JSON data to send in the request body
            headers: Optional dictionary of headers to include
            
        Returns:
            RunnableCommandString for a curl POST request
        """
        command = self._build_base_command("POST")
        command += f" '{url}'"
        command = self._add_headers(command, headers)
        command = self._add_data(command, data, json_data, headers)

        return RunnableCommandString(command=command)

    def put(self, url: str, data: Optional[str] = None, json_data: Optional[JsonObject | JsonArray] = None,
            headers: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl PUT request command
        
        Args:
            url: The URL to send the PUT request to
            data: Optional string data to send in the request body
            json_data: Optional JSON data to send in the request body
            headers: Optional dictionary of headers to include
            
        Returns:
            RunnableCommandString for a curl PUT request
        """
        command = self._build_base_command("PUT")
        command += f" '{url}'"
        command = self._add_headers(command, headers)
        command = self._add_data(command, data, json_data, headers)

        return RunnableCommandString(command=command)

    def patch(self, url: str, data: Optional[str] = None, json_data: Optional[Union[JsonObject, JsonArray]] = None,
              headers: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl PATCH request command

        Args:
            url: The URL to send the PATCH request to
            data: Optional string data to send in the request body. If this is provided `json_data` must be omitted.
            json_data: Optional JSON data to send in the request body. If this is provided `data` must be omitted.
            headers: Optional dictionary of headers to include

        Returns:
            RunnableCommandString for a curl PATCH request
        """
        command = self._build_base_command("PATCH")
        command += f" '{url}'"
        command = self._add_headers(command, headers)
        command = self._add_data(command, data, json_data, headers)

        return RunnableCommandString(command=command)

    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl DELETE request command
        
        Args:
            url: The URL to send the DELETE request to
            headers: Optional dictionary of headers to include
            
        Returns:
            RunnableCommandString for a curl DELETE request
        """
        command = self._build_base_command("DELETE")
        command += f" '{url}'"
        command = self._add_headers(command, headers)

        return RunnableCommandString(command=command)

    def head(self, url: str, headers: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl HEAD request command
        
        Args:
            url: The URL to send the HEAD request to
            headers: Optional dictionary of headers to include
            
        Returns:
            RunnableCommandString for a curl HEAD request
        """
        # HEAD uses -I flag instead of -X HEAD
        command: str = self._build_base_command()
        command += " -I"
        command += f" '{url}'"
        command = self._add_headers(command, headers)

        return RunnableCommandString(command=command)

    def options(self, url: str, headers: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl OPTIONS request command
        
        Args:
            url: The URL to send the OPTIONS request to
            headers: Optional dictionary of headers to include
            
        Returns:
            RunnableCommandString for a curl OPTIONS request
        """
        command = self._build_base_command("OPTIONS")
        command += f" '{url}'"
        command = self._add_headers(command, headers)

        return RunnableCommandString(command=command)

    def download_file(self, url: str, output_path: str, headers: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl command to download a file
        
        Args:
            url: The URL to download from
            output_path: The path to save the downloaded file to
            headers: Optional dictionary of headers to include
            
        Returns:
            RunnableCommandString for downloading a file with curl
        """
        command: str = self._build_base_command()
        command += f" -o '{output_path}'"
        command += f" '{url}'"
        command = self._add_headers(command, headers)

        return RunnableCommandString(command=command)

    def follow_redirects(self, url: str, headers: Optional[Dict[str, str]] = None) -> RunnableCommandString:
        """
        Create a curl command that follows redirects
        
        Args:
            url: The URL to send the request to
            headers: Optional dictionary of headers to include
            
        Returns:
            RunnableCommandString for a curl request that follows redirects
        """
        command = self._build_base_command()  # -L follows redirects
        command += " -L"
        command += f" '{url}'"
        command = self._add_headers(command, headers)

        return RunnableCommandString(command=command)

    @staticmethod
    def parse_curl_response_with_status(response_output: str) -> tuple[str, int]:
        """Parse curl response that includes HTTP status code."""

        delimiter = "|||HTTP_STATUS|||"

        if delimiter in response_output:
            parts = response_output.split(delimiter)
            if len(parts) == 2:
                body = parts[0]
                try:
                    status_code = int(parts[1].strip())
                    return body, status_code
                except ValueError:
                    pass

        # Fallback if parsing fails
        return response_output, 0

    # Security scanning specific commands
    def get_with_full_headers(self, url: str, user_agent: str = "EasyRunner-Security-Scanner/1.0") -> RunnableCommandString:
        """
        Create a curl GET request that includes full response headers for security analysis.
        
        Args:
            url: The URL to send the GET request to
            user_agent: User agent string to use
            
        Returns:
            RunnableCommandString that returns headers and body
        """
        # Use -i to include response headers, -s for silent, custom User-Agent
        command = f"{self.command_name} -i -s -H 'User-Agent: {user_agent}' '{url}'"
        return RunnableCommandString(command=command)

    def get_headers_only(self, url: str, user_agent: str = "EasyRunner-Security-Scanner/1.0") -> RunnableCommandString:
        """
        Create a curl HEAD request to get only response headers for security analysis.
        
        Args:
            url: The URL to get headers from
            user_agent: User agent string to use
            
        Returns:
            RunnableCommandString that returns only headers
        """
        command = f"{self.command_name} -I -s -H 'User-Agent: {user_agent}' '{url}'"
        return RunnableCommandString(command=command)

    def test_http_methods(self, url: str, method: str) -> RunnableCommandString:
        """
        Test specific HTTP method on a URL for security analysis.
        
        Args:
            url: The URL to test
            method: HTTP method to test (TRACE, TRACK, etc.)
            
        Returns:
            RunnableCommandString for method testing
        """
        delimiter = "|||HTTP_STATUS|||"
        command = f"{self.command_name} -s -w '{delimiter}%{{http_code}}' -X {method} '{url}'"
        return RunnableCommandString(command=command)

    def get_with_timeout(self, url: str, timeout_seconds: int = 10, 
                        user_agent: str = "EasyRunner-Security-Scanner/1.0") -> RunnableCommandString:
        """
        Create a curl GET request with timeout for security scanning.
        
        Args:
            url: The URL to request
            timeout_seconds: Connection and max time timeout
            user_agent: User agent string to use
            
        Returns:
            RunnableCommandString with timeout settings
        """
        delimiter = "|||HTTP_STATUS|||"
        command = (f"{self.command_name} -s --connect-timeout {timeout_seconds} "
                  f"--max-time {timeout_seconds} -w '{delimiter}%{{http_code}}' "
                  f"-H 'User-Agent: {user_agent}' '{url}'")
        return RunnableCommandString(command=command)

    def get_with_follow_redirects_and_headers(self, url: str, max_redirects: int = 5,
                                            user_agent: str = "EasyRunner-Security-Scanner/1.0") -> RunnableCommandString:
        """
        Create a curl request that follows redirects and includes headers for security analysis.
        
        Args:
            url: The URL to request
            max_redirects: Maximum number of redirects to follow
            user_agent: User agent string to use
            
        Returns:
            RunnableCommandString with redirect following and header inclusion
        """
        command = (f"{self.command_name} -i -s -L --max-redirs {max_redirects} "
                  f"-H 'User-Agent: {user_agent}' '{url}'")
        return RunnableCommandString(command=command)
