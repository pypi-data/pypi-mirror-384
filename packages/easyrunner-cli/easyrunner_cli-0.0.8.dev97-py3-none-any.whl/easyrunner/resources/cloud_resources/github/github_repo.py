from typing import List

from ....types.exec_result import ExecResult
from .. import CloudResourceApiBase
from .github_api_client import GitHubApiClient
from .github_api_client_dtos import (
    AddDeployKeyResponse,
    CreateDeployKeyRequest,
    DeleteDeployKeyResponse,
    GitHubDeployKey,
)


class GithubRepo(CloudResourceApiBase):
    """Represents a repository on Github.com.

    Accesses a Github.com repository using the GitHub API client.

    Other resources that needs github access to a github repo cloud resource should use this class.
    """

    def __init__(
        self, name: str, owner: str, github_api_client: GitHubApiClient
    ) -> None:
        super().__init__()
        """Create a GitHubRepo object.
        
        Args:
            name (str): The name of the repository.
            owner (str): The owner of the repository. Organization name or user account name. https://github.com/<owner>/<name>
            github_api_client (GitHubApiClient): GitHub API client for API operations.
        """
        self.name = name
        self.owner = owner
        self._github_api_client: GitHubApiClient = github_api_client

    # def _get_api_client(self) -> GitHubApiClient:
    #     """Get or create API client."""
    #     if not self._github_api_client:
    #         if not self._access_token:
    #             raise ValueError("GitHub access token is required for API operations.")

    #         self._github_api_client = GitHubApiClient(self._access_token)

    #     return self._github_api_client

    def get_repo_info(self) -> str:
        return f"Repository: {self.name}, Owner: {self.owner}"

    def add_deploy_key(
        self,
        public_ssh_key_content: str,
        title: str = "EasyRunner Deploy Key",
        read_only: bool = True,
    ) -> ExecResult:
        """Add a deploy key to the repository.

        Args:
            public_ssh_key_content (str): The public SSH key content.
            title (str): Title for the deploy key.
            read_only (bool): Whether the key should be read-only.

        Returns:
            ExecResult: Result of the API operation.
        """
        api_client = self._github_api_client

        create_deploy_key_request = CreateDeployKeyRequest(
            title=title, key=public_ssh_key_content.strip(), read_only=read_only
        )

        http_response = api_client.add_deploy_key(
            self.owner,
            self.name,
            create_deploy_key_request=create_deploy_key_request,
        )

        # Use DTO internally for validation but don't expose it
        deploy_key = None
        if (
            http_response.success
            and http_response.data
            and isinstance(http_response.data, dict)
        ):
            deploy_key = GitHubDeployKey.from_json(http_response.data)

        add_response = AddDeployKeyResponse(
            success=http_response.success,
            status_code=http_response.status_code,
            deploy_key=deploy_key,
            error_message=http_response.error,
        )

        return ExecResult(
            success=add_response.is_success,
            return_code=add_response.status_code,
            stdout=None,
            stderr=add_response.error_message,
        )

    def list_deploy_keys(self) -> ExecResult[List[GitHubDeployKey]]:
        """List all deploy keys for the repository.

        Returns:
            ExecResult[List[GitHubDeployKey]]: Result with list of deploy keys.
        """
        api_client = self._github_api_client
        list_response = api_client.list_deploy_keys(self.owner, self.name)

        result = ExecResult[List[GitHubDeployKey]](
            success=list_response.is_success,
            return_code=list_response.status_code,
            stdout=None,
            stderr=list_response.error_message,
        )
        result.result = list_response.deploy_keys if list_response.deploy_keys else []

        return result

    def delete_deploy_key(self, key_id: int) -> ExecResult:
        """Delete a deploy key from the repository.

        Args:
            key_id (int): The ID of the deploy key to delete.

        Returns:
            ExecResult: Result of the deletion operation.
        """
        api_client = self._github_api_client
        http_response = api_client.delete_deploy_key(self.owner, self.name, key_id)

        # Use DTO internally for validation but don't expose it
        delete_response = DeleteDeployKeyResponse(
            success=http_response.success,
            status_code=http_response.status_code,
            error_message=http_response.error,
        )

        return ExecResult(
            success=delete_response.is_success,
            return_code=delete_response.status_code,
            stdout=None,
            stderr=delete_response.error_message,
            command=None,
        )
