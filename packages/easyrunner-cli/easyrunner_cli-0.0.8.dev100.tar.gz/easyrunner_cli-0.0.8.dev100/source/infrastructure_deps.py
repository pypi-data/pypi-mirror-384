import platform
import subprocess

from easyrunner.source.tool_paths import EasyRunnerPaths
from easyrunner.source.types.exec_result import ExecResult


class InfrastructureDependencies:
    """Manages infrastructure tool dependencies for EasyRunner."""

    @staticmethod
    def ensure_cloud_tools_available() -> ExecResult:
        """Ensure required cloud infrastructure tools are installed."""
        # Check if Pulumi CLI is available
        if not InfrastructureDependencies._is_pulumi_available():
            print("Setting up cloud infrastructure tools...")
            result = InfrastructureDependencies._install_pulumi()
            if not result.success:
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout=None,
                    stderr=f"Failed to install required cloud infrastructure tools. {result.stderr}",
                )
            print("✓ Cloud infrastructure tools ready")

        return ExecResult(success=True, return_code=0, stdout=None, stderr=None)

    @staticmethod
    def _is_pulumi_available() -> bool:
        """Check if Pulumi CLI is available and get the path."""

        easyrunner_pulumi = EasyRunnerPaths.get_pulumi_command()

        try:
            subprocess.run(
                [str(easyrunner_pulumi), "version"], capture_output=True, check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    @staticmethod
    def _install_pulumi() -> ExecResult:
        """Install Pulumi CLI to EasyRunner-specific directory based on platform."""
        pulumi_install_root = EasyRunnerPaths.get_pulumi_root()
        system = platform.system().lower()

        try:
            # Create the directory if it doesn't exist
            pulumi_install_root.mkdir(parents=True, exist_ok=True)

            if system == "darwin":  # macOS
                # Use installation script with proper command-line arguments for macOS
                # Using shell pipe is necessary here for the installation script pattern
                install_cmd = f"curl -fsSL https://get.pulumi.com | sh -s -- --install-root {pulumi_install_root} --no-edit-path"
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    shell=True,  # nosec B602 - Required for pipe syntax with curl | sh, path is controlled
                )

            elif system == "linux":
                # Use installation script with proper command-line arguments for Linux
                # Using shell pipe is necessary here for the installation script pattern
                install_cmd = f"curl -fsSL https://get.pulumi.com | sh -s -- --install-root {pulumi_install_root} --no-edit-path"
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    shell=True,  # nosec B602 - Required for pipe syntax with curl | sh, path is controlled
                )

            elif system == "windows":
                # Use PowerShell installation script for Windows with command-line arguments
                powershell_script = f"""
                iex ((New-Object System.Net.WebClient).DownloadString('https://get.pulumi.com/install.ps1')) -InstallRoot "{pulumi_install_root}" -NoEditPath
                """
                result = subprocess.run(
                    ["powershell", "-Command", powershell_script],
                    capture_output=True,
                    text=True,
                )

            else:
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout=None,
                    stderr=f"Automatic installation not supported on platform: {system}. "
                    "Please install Pulumi manually: https://www.pulumi.com/docs/get-started/install/",
                )

            return ExecResult(
                success=result.returncode == 0,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )

        except Exception as e:
            return ExecResult(
                success=False,
                return_code=1,
                stdout=None,
                stderr=str(e)
            )
