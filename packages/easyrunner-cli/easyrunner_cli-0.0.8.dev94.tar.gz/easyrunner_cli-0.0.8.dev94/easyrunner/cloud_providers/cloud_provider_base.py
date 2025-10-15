import os
from abc import ABC, abstractmethod
from typing import Any, Optional

import pulumi.automation as auto

from ..tool_paths import EasyRunnerPaths
from ..types.exec_result import ExecResult


class CloudProviderBase(ABC):
    """Base class for cloud provider implementations."""

    def __init__(
        self, api_key: str, region: str, project_name: Optional[str] = None
    ) -> None:
        self.api_key = api_key
        self.region = region
        self.project_name = project_name or f"easyrunner-{self.name()}"

    @abstractmethod
    def _create_provider(self) -> Any:
        """Create the cloud provider instance."""
        pass

    def _get_pulumi_command(self) -> str:
        """Get the Pulumi root directory for PulumiCommand, which will append /bin/pulumi."""
        return str(EasyRunnerPaths.get_pulumi_root())

    def _create_workspace_options(
        self, backend_url: Optional[str] = None
    ) -> auto.LocalWorkspaceOptions:
        """Create workspace options with custom Pulumi command and optional backend."""
        pulumi_command_path = self._get_pulumi_command()

        # Set default backend to EasyRunner's local backend if not provided
        if backend_url is None or backend_url == "":
            backend_url = f"file://{EasyRunnerPaths.get_pulumi_local_backend_dir()}"

        # Set Pulumi config passphrase if not already set
        if "PULUMI_CONFIG_PASSPHRASE" not in os.environ:
            os.environ["PULUMI_CONFIG_PASSPHRASE"] = (
                "klshdf324£$@::D£$mcmoWERXakhk234%basdmnbqqvffadqWEQAO[]£N!#sdff"
            )

        return auto.LocalWorkspaceOptions(
            pulumi_command=auto.PulumiCommand(pulumi_command_path),
            pulumi_home=str(
                EasyRunnerPaths.get_pulumi_root()
            ),  # Control where all Pulumi data is stored
            secrets_provider="passphrase",
            work_dir=str(
                EasyRunnerPaths.get_pulumi_local_backend_dir()
            ),  # Set workspace directory
            project_settings=auto.ProjectSettings(
                name=self.project_name,
                runtime="python",
                backend=auto.ProjectBackend(url=backend_url),
            ),
        )

    def _ensure_cloud_tools_available(self) -> ExecResult:
        """Ensure cloud tools are available before executing Pulumi operations."""
        from easyrunner_cli.source.infrastructure_deps import InfrastructureDependencies

        return InfrastructureDependencies.ensure_cloud_tools_available()

    def get_provider_instance(self) -> Any:
        """Get the provider instance for programmatic use."""

        return self._create_provider()

    def _convert_pulumi_outputs_to_dict(
        self, outputs: auto.OutputMap
    ) -> dict[str, Any]:
        """Convert Pulumi OutputMap to standard dictionary with extracted values.

        Args:
            outputs: Pulumi OutputMap from stack.outputs()

        Returns:
            Dictionary with extracted values from Pulumi OutputValue objects
        """
        result: dict[str, Any] = {}
        for key, output_value in outputs.items():
            # Pulumi automation API returns OutputValue objects with a 'value' field
            result[key] = (
                output_value.value if hasattr(output_value, "value") else output_value
            )
        return result

    @abstractmethod
    def name(self) -> str:
        """Get the name of the cloud provider."""
        pass

    # def execute_pulumi_program(
    #     self,
    #     program: Callable[[], None],
    #     stack_name: str,
    #     backend_url: Optional[str] = None,
    # ) -> ExecResult:
    #     """Execute a Pulumi program using EasyRunner's Pulumi installation.

    #     Args:
    #         program: The Pulumi program function to execute
    #         stack_name: Name of the stack
    #         backend_url: Optional backend URL (e.g., s3://bucket-name for S3 backend)
    #     Returns:
    #         ExecResult[dict[str, Any]]: The result of the Pulumi program execution stack.outputs as a dictionary.
    #     """
    #     # Ensure cloud tools are available before executing
    #     deps_result = self._ensure_cloud_tools_available()
    #     if not deps_result.success:
    #         return deps_result

    #     try:
    #         # Create or select stack with custom workspace options
    #         stack = auto.create_or_select_stack(
    #             stack_name=stack_name,
    #             project_name=self.project_name,
    #             program=program,
    #             opts=self._create_workspace_options(backend_url=backend_url),
    #         )

    #         # Deploy
    #         stack.up()

    #         result = ExecResult[dict[str, Any]](
    #             success=True,
    #             return_code=0,
    #             stdout="Stack deployed successfully",
    #             stderr=None,
    #         )

    #         # Convert Pulumi OutputMap to standard dict
    #         result.result = self._convert_pulumi_outputs_to_dict(stack.outputs())

    #         return result

    #     except Exception as e:
    #         return ExecResult(success=False, return_code=1, stdout=None, stderr=str(e))

    # def destroy_pulumi_stack(
    #     self, stack_name: str, backend_url: Optional[str] = None
    # ) -> ExecResult:
    #     """Destroy a Pulumi stack using EasyRunner's Pulumi installation."""
    #     try:

    #         def dummy_program() -> None:
    #             """Empty program required for stack selection."""
    #             pass

    #         stack = auto.select_stack(
    #             stack_name=stack_name,
    #             project_name=self.project_name,
    #             program=dummy_program,
    #             opts=self._create_workspace_options(backend_url=backend_url),
    #         )

    #         stack.destroy()

    #         return ExecResult(
    #             success=True,
    #             return_code=0,
    #             stdout=f"Stack {stack_name} destroyed",
    #             stderr=None,
    #         )

    #     except Exception as e:
    #         return ExecResult(success=False, return_code=1, stdout=None, stderr=str(e))

    def get_stack_outputs(
        self, stack_name: str, backend_url: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Get outputs from a Pulumi stack using EasyRunner's Pulumi installation."""
        try:
            stack = auto.select_stack(
                stack_name=stack_name,
                project_name=self.project_name,
                opts=self._create_workspace_options(backend_url=backend_url),
            )

            outputs = stack.outputs()
            result = self._convert_pulumi_outputs_to_dict(outputs)
            return result if result else None

        except Exception:
            return None

    # @abstractmethod
    # def create_select_state_backend_bucket(self) -> ExecResult:
    #     """Setup the Pulumi state backend."""
    #     pass
