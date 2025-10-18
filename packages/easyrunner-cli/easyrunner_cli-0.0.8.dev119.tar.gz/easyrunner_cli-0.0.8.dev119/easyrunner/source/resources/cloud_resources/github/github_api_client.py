from typing import List

from ..... import logger
from ....http_client import HttpClient, HttpResponse
from .github_api_client_dtos import (
    CreateDeployKeyRequest,
    GitHubDeployKey,
    ListDeployKeysResponse,
)


class GitHubApiClient:
    """Client for GitHub API operations using HTTP client abstraction.

    The intent is that a CloudResource (e.g., GitHubRepo) abstracts away the client and DTOs.
    """

    def __init__(self, access_token: str) -> None:
        """Initialize GitHub API client.
        
        Args:
            access_token (str): GitHub access token for authentication.
        """
        self.access_token = access_token
        self.http_client = HttpClient(
            base_url="https://api.github.com",
            timeout=30,
            auth_token=access_token,
            auth_type="Bearer"
        )
        # Set GitHub-specific headers
        self.http_client.default_headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "EasyRunner-CLI"
        })

    def add_deploy_key(
        self,
        owner: str,
        repo: str,
        create_deploy_key_request: CreateDeployKeyRequest,
    ) -> HttpResponse:
        """Add a deploy key for a Github repository.

        Args:
            owner (str): Repository owner.
            repo (str): Repository name.
            create_deploy_key_request (CreateDeployKeyRequest): Deploy key creation request data.

        Returns:
            HttpResponse: Result of the API operation.
        """

        endpoint = f"/repos/{owner}/{repo}/keys"
        return self.http_client.post(
            endpoint=endpoint, json_data=create_deploy_key_request.to_json()
        )

    def list_deploy_keys(self, owner: str, repo: str) -> ListDeployKeysResponse:
        """List deploy keys for a repository.

        Args:
            owner (str): Repository owner.
            repo (str): Repository name.

        Returns:
            ListDeployKeysResponse: Response containing list of deploy keys and status.
        """
        endpoint = f"/repos/{owner}/{repo}/keys"
        response = self.http_client.get(
            endpoint=endpoint
        )

        if response.status_code != 200:
            return ListDeployKeysResponse(
                success=False,
                status_code=response.status_code,
                deploy_keys=None,
                error_message=response.error,
            )

        if not isinstance(response.data, list):
            return ListDeployKeysResponse(
                success=False,
                status_code=response.status_code,
                deploy_keys=None,
                error_message=f"Unexpected response format: expected list, got {type(response.data)}",
            )

        # Type-safe list comprehension
        deploy_keys: List[GitHubDeployKey] = []
        for key_data in response.data:
            if isinstance(key_data, dict):
                deploy_keys.append(GitHubDeployKey.from_json(key_data))

        return ListDeployKeysResponse(
            success=True,
            status_code=response.status_code,
            deploy_keys=deploy_keys,
            error_message=None,
        )

    def delete_deploy_key(self, owner: str, repo: str, key_id: int) -> HttpResponse:
        """Delete a deploy key from a repository.
        
        Args:
            owner (str): Repository owner.
            repo (str): Repository name.
            key_id (int): The ID of the deploy key to delete.
            
        Returns:
            HttpResponse: Result of the API operation.
        """
        endpoint = f"/repos/{owner}/{repo}/keys/{key_id}"
        return self.http_client.delete(
            endpoint=endpoint
        )

    def is_access_token_valid(self) -> bool:
        """Test if the access token is accepted as authentication.

        Returns:
            bool: True if token is valid, False otherwise.
        """
        try:
            response = self.http_client.get(endpoint="/user")
            return (
                response.success
                and response.data is not None
                and isinstance(response.data, dict)
                and "login" in response.data
            )
        except Exception as e:
            logger.error(f"Error occurred while validating access token: {e}")
            return False
