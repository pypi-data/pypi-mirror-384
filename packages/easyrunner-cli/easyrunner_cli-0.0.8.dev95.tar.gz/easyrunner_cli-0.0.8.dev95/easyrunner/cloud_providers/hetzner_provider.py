import os
from typing import TYPE_CHECKING

from .cloud_provider_base import CloudProviderBase
from .cloud_providers import CloudProviders

if TYPE_CHECKING:
    import pulumi_hcloud


class HetznerProvider(CloudProviderBase):
    """Hetzner cloud provider implementation using Pulumi."""

    def __init__(self, api_key: str, region: str = "nbg1"):
        super().__init__(api_key, region)
        # Store the API key for programmatic provider configuration
        self._hetzner_token = api_key

    def _create_provider(self) -> "pulumi_hcloud.Provider":
        """Create Hetzner provider with explicit token configuration."""
        import pulumi_hcloud as hetzner

        return hetzner.Provider("hetzner-provider", token=self._hetzner_token)

    def name(self) -> str:
        """Get the name of the cloud provider."""
        return CloudProviders.HETZNER.value

    @classmethod
    def from_env(cls, region: str = "nbg1") -> "HetznerProvider":
        """Create HetznerProvider instance from HETZNER_API_KEY environment variable."""
        api_key = os.getenv("HETZNER_API_KEY")
        if not api_key:
            raise ValueError("HETZNER_API_KEY environment variable is required")
        return cls(api_key=api_key, region=region)

    # def create_select_state_backend_bucket(self) -> ExecResult:
    #     """Setup Pulumi state backend - local for initial setup, S3 for production.

    #     Retrurns:
    #         ExecResult[dict[str, Any]]

    #         results keys:
    #             - bucket_name: Name of the created S3 bucket for state storage.
    #     """

    #     # Create S3 compatible object storage backend using the base class execute_pulumi_program method
    #     def create_state_backend_object_store() -> None:
    #         """there currently no pulumi object storage support for Hetzner as it's a new service."""
    #         pass

    #     # Execute the program using local backend (for creating the S3 bucket)
    #     result: ExecResult[dict[str, Any]] = self.execute_pulumi_program(
    #         program=create_state_backend_object_store,
    #         stack_name="state-backend",
    #         backend_url=None,  # Use local backend to create the S3 bucket
    #     )

    #     if not result.success:
    #         return result

    #     # Get the bucket name from outputs
    #     outputs = self.get_stack_outputs(
    #         stack_name="state-backend",
    #         backend_url=None,
    #     )

    #     bucket_name = ""
    #     if outputs and "state_bucket_name" in outputs:
    #         bucket_name = outputs["state_bucket_name"]

    #     return ExecResult(
    #         success=True,
    #         return_code=0,
    #         stdout=f"S3 state bucket created: {bucket_name}. Use backend URL: s3://{bucket_name}",
    #         stderr=None,
    #     )
