from typing import Optional, Self

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class GitCommands(CommandBase):
    _version_response_prefix: str = "git version"

    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str = "git") -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name="git"
        )

    def init(self) -> RunnableCommandString:
        return RunnableCommandString(command=f"{self.command_name} init")

    def remote_add_origin(self, repo_url: str) -> RunnableCommandString:
        return RunnableCommandString(
            command=f"{self.command_name} remote add -f origin {repo_url}"
        )

    def remote_get_url(
        self, remote_name: str = "origin", working_dir: Optional[str] = None
    ) -> RunnableCommandString:
        """Get the URL of a remote repository.

        Args:
            remote_name (str, optional): The name of the remote. Defaults to "origin".
            working_dir (Optional[str], optional): The git repository directory. Defaults to None.

        Returns:
            RunnableCommandString: Command to get the remote URL
        """
        wdc: str = ""
        if working_dir:
            wdc = f"-C {working_dir} "
        return RunnableCommandString(
            command=f"{self.command_name} {wdc}remote get-url {remote_name}"
        )

    def config_sparse_checkout(self) -> RunnableCommandString:
        """Tells Git that you want to selectively check out only specific files or directories from the repository"""
        return RunnableCommandString(
            command=f"{self.command_name} config core.sparseCheckout true"
        )

    def sparse_checkout_add_dirs(self, sub_dir: str) -> RunnableCommandString:
        """Adds a directory/file/pattern to the sparse checkout list. These will be the only files checked out from the repository."""
        return RunnableCommandString(
            command=f"echo {sub_dir} >> .git/info/sparse-checkout"
        )

    def pull(
        self, branch: str, working_dir: Optional[str] = None
    ) -> RunnableCommandString:
        wdc: str = ""
        if working_dir:
            wdc = f"-C {working_dir}"
        return RunnableCommandString(
            command=f"{self.command_name} {wdc} pull origin {branch}"
        )

    def clone(
        self, repo_url: str, branch: str, working_dir: Optional[str] = None
    ) -> RunnableCommandString:
        """Clone a git repository.

        Args:
            repo_url (str): The URL of the git repository to clone (SSH or HTTPS format).
            branch (str): The branch to clone.
            working_dir (Optional[str], optional): The directory to clone into. Defaults to None.

        Raises:
            ValueError: If repo_url doesn't end with .git or isn't a valid GitHub URL
        """
        wdc: str = ""

        if not repo_url.endswith(".git"):
            raise ValueError("repo_url", "The repository URL must end with '.git'")

        if not repo_url.startswith("git@github.com:") and not repo_url.startswith(
            "https://github.com/"
        ):
            raise ValueError(
                "repo_url",
                "The repository URL must start with 'git@github.com:' or 'https://github.com/'",
            )

        if working_dir:
            wdc = f" -C {working_dir}"
        return RunnableCommandString(
            command=f"{self.command_name} {wdc} clone -b {branch} {repo_url}"
        )

    def status(self: Self, working_dir: Optional[str] = None) -> RunnableCommandString:
        wdc: str = ""
        if working_dir:
            wdc = f"-C {working_dir}"
        return RunnableCommandString(command=f"{self.command_name} {wdc} status")

    def latest_commit_hash(
        self, working_dir: Optional[str] = None
    ) -> RunnableCommandString:
        """Get the latest commit hash of the currently checked out branch."""
        wdc: str = ""
        if working_dir:
            wdc = f"-C {working_dir}"
        return RunnableCommandString(
            command=f"{self.command_name} {wdc} rev-parse HEAD"
        )

    def version(self) -> RunnableCommandString:
        """Get the version of the git command."""
        return RunnableCommandString(command=f"{self.command_name} --version")
