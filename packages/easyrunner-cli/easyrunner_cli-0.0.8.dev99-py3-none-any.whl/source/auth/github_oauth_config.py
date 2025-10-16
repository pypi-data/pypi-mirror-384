import os
from dataclasses import dataclass


@dataclass
class GitHubOAuthConfig:
    """Configuration for GitHub OAuth (Device Flow).

    Device Flow is designed for CLIs and doesn't require a client secret.
    The client_id is public and safe to distribute in the codebase.
    """
    # Public client ID - safe to distribute
    client_id: str = "Ov23liIBTV75Sjfu4Pay"
    scopes: str = "repo"

    # URLs for device flow
    device_code_url: str = "https://github.com/login/device/code"
    token_url: str = "https://github.com/login/oauth/access_token"

    def __post_init__(self):
        """Override client_id from env if present (for testing/development)."""
        env_client_id = os.getenv("ER_GITHUB_OAUTH_CLIENT_ID")
        if env_client_id:
            self.client_id = env_client_id
