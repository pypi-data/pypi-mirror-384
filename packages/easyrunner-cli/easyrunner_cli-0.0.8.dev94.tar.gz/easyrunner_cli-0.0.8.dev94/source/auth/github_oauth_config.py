import os
from dataclasses import dataclass, field


def _env_required(name: str) -> str:
    value: str | None = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"{name} not set")
    return value


@dataclass
class GitHubOAuthConfig:
    """Configuration for GitHub OAuth application."""
    client_id: str = field(
        default_factory=lambda: _env_required("ER_GITHUB_OAUTH_CLIENT_ID")
    )
    client_secret: str = field(
        default_factory=lambda: _env_required("ER_GITHUB_OAUTH_CLIENT_SECRET")
    )
    redirect_uri: str = "http://localhost:8789/callback"
    scopes: str = "repo"
    authorization_url: str = "https://github.com/login/oauth/authorize"
    token_url: str = "https://github.com/login/oauth/access_token"
