"""Centralized tool path configuration for EasyRunner."""

import platform
from pathlib import Path


class EasyRunnerPaths:
    """Centralized path management for EasyRunner tools."""

    @staticmethod
    def get_tools_root() -> Path:
        """Get the root directory for EasyRunner tools."""
        return Path.joinpath(Path.home(), ".easyrunner", "tools")

    @staticmethod
    def get_pulumi_root() -> Path:
        """Get the root directory for Pulumi installation."""
        return Path.joinpath(EasyRunnerPaths.get_tools_root(), "pulumi")

    @staticmethod
    def get_pulumi_bin_dir() -> Path:
        """Get the bin directory for Pulumi installation."""
        return Path.joinpath(EasyRunnerPaths.get_pulumi_root(), "bin")

    @staticmethod
    def get_pulumi_command() -> str:
        """Get the full path to the Pulumi executable. OS Platform aware."""
        pulumi_bin_dir = EasyRunnerPaths.get_pulumi_bin_dir()

        # Handle Windows executable extension
        system = platform.system().lower()
        pulumi_executable = "pulumi.exe" if system == "windows" else "pulumi"

        easyrunner_pulumi = Path.joinpath(pulumi_bin_dir, pulumi_executable)
        if easyrunner_pulumi.exists():
            return str(easyrunner_pulumi)

        raise FileNotFoundError(
            f"Pulumi executable not found at {easyrunner_pulumi}. "
            "The Pulumi CLI should have been installed automatically by EasyRunner."
        )

    @staticmethod
    def get_pulumi_local_backend_dir() -> Path:
        """Get the local backend directory for Pulumi workspaces. Creates the directory if it doesn't exist."""

        path = Path.joinpath(EasyRunnerPaths.get_pulumi_root(), "workspaces")
        path.mkdir(parents=True, exist_ok=True)

        return path
