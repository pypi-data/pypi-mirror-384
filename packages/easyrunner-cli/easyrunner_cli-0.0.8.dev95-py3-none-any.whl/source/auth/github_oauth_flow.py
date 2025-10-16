import json
import logging
import urllib.parse
import webbrowser
from typing import Callable, Optional

from easyrunner.source.command_executor_local import CommandExecutorLocal
from easyrunner.source.commands.ubuntu.curl_commands_ubuntu import CurlCommandsUbuntu

from .github_oauth_config import GitHubOAuthConfig
from .oauth_callback_server import OAuthCallbackHandler, OAuthCallbackServer

logger = logging.getLogger(__name__)


class GitHubOAuthFlow:
    """Manages GitHub OAuth authentication flow."""

    def __init__(
        self,
        config: GitHubOAuthConfig,
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self.config = config
        self.executor = CommandExecutorLocal()
        self.curl_commands = CurlCommandsUbuntu()
        self.progress_callback = progress_callback or (lambda msg, end="\n": None)

    def find_available_port(self, start_port: int = 8789) -> int:
        """Find an available port for the callback server."""
        import socket

        for port in range(start_port, start_port + 20):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue

        raise RuntimeError("No available ports found for OAuth callback")

    def start_oauth_flow(self) -> Optional[str]:
        """Start OAuth flow and return access token if successful."""
        try:
            # Find available port
            port = self.find_available_port()
            callback_url = f"http://localhost:{port}/callback"

            # Generate state for CSRF protection
            import secrets
            state = secrets.token_urlsafe(32)

            # Build authorization URL
            auth_params = {
                'client_id': self.config.client_id,
                'redirect_uri': callback_url,
                'scope': self.config.scopes,
                'state': state
            }
            auth_url = f"{self.config.authorization_url}?{urllib.parse.urlencode(auth_params)}"

            # Start local server
            authorization_code = self._wait_for_callback(port, auth_url)

            if authorization_code:
                # Exchange code for token
                return self._exchange_code_for_token(authorization_code)

            return None

        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            return None

    def _wait_for_callback(self, port: int, auth_url: str) -> Optional[str]:
        """Start callback server and wait for authorization."""
        self.progress_callback("🌐 Opening GitHub authorization page...", "\n")
        self.progress_callback(
            "⏳ Waiting for authorization (check your browser)...", "\n"
        )

        # Open browser
        webbrowser.open(auth_url)

        # Start HTTP server using our custom server class
        with OAuthCallbackServer(("localhost", port), OAuthCallbackHandler) as httpd:
            # Set timeout
            httpd.timeout = 300  # 5 minutes

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                self.progress_callback("\n❌ Authorization cancelled by user", "\n")
                return None

            if httpd.oauth_error:
                self.progress_callback(
                    f"❌ Authorization failed: {httpd.oauth_error}", "\n"
                )
                return None

            return httpd.authorization_code

    def _exchange_code_for_token(self, authorization_code: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        try:
            # Prepare token request data
            token_data = {
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret,
                'code': authorization_code
            }

            # Convert to form data
            form_data = urllib.parse.urlencode(token_data)

            # Make token request using POST with form data
            cmd = self.curl_commands.post(
                url=self.config.token_url,
                data=form_data,
                headers={"Accept": "application/json"}
            )

            result = self.executor.execute(cmd)

            if result.success and result.stdout:
                # Parse response
                response_body, _ = self.curl_commands.parse_curl_response_with_status(result.stdout)

                try:
                    token_response = json.loads(response_body)
                    access_token = token_response.get('access_token')

                    if access_token:
                        return access_token
                    else:
                        error_desc = token_response.get('error_description', 'Unknown error')
                        logger.error(f"Token exchange failed: {error_desc}")
                        return None

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse token response: {response_body}")
                    return None
            else:
                logger.error(f"Token exchange request failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return None

    def test_token(self, token: str) -> bool:
        """Test if token is valid by making a test API call."""
        try:
            cmd = self.curl_commands.get(
                url="https://api.github.com/user",
                headers={"Authorization": f"Bearer {token}"}
            )

            result = self.executor.execute(cmd)
            return result.success and result.stdout is not None and "login" in result.stdout

        except Exception:
            return False
