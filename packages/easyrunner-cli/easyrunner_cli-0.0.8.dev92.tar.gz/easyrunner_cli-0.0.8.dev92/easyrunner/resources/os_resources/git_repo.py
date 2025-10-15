import os
import re
from typing import Optional, Tuple

from .... import logger
from ...command_executor import CommandExecutor
from ...commands.base.git_commands import GitCommands
from ...commands.base.utility_commands import UtilityCommands
from ...commands.ubuntu.dir_commands_ubuntu import DirCommandsUbuntu
from ...types.cpu_arch_types import CpuArch
from ...types.exec_result import ExecResult
from .directory import Directory
from .os_resource_base import OsResourceBase


class GitRepo(OsResourceBase):
    def __init__(
        self,
        commands: GitCommands,
        executor: CommandExecutor,
        util_commands: UtilityCommands,
        repo_remote_url: str,
        branch_name: str,
        repo_local_base_dir: str,
        ssh_agent_env_vars: Optional[dict[str, str]] = None,
    ):
        super().__init__(commands=commands, executor=executor)
        self.commands = commands
        self.executor = executor
        self._uc = util_commands
        self._dir_cmds = DirCommandsUbuntu(
            cpu_arch=CpuArch.X86_64,
        )

        self.repo_remote_url = repo_remote_url
        self.branch_name = branch_name
        self.repo_local_base_dir = repo_local_base_dir
        self.ssh_agent_env_vars = ssh_agent_env_vars

        # Parse repo owner and name from URL (supports both SSH and HTTPS formats)
        self.repo_owner, self.repo_name = self._parse_git_url(repo_remote_url)
        self.full_repo_path = os.path.join(self.repo_local_base_dir, self.repo_name)

    """Represents a git repository on disk on the server.

    Args:
        commands (GitCommands): The git commands to use.
        executor (CommandExecutor): The command executor to use.
        repo_remote_url (str): The URL of the git remote repository.
        branch_name (str): The name of the branch to clone.
        repo_local_base_dir (str): The local directory where the repository will/has been cloned to. Remember this doesn't include the repo name.
    """

    def _parse_git_url(self, repo_url: str) -> Tuple[str, str]:
        """Parse Git repository URL to extract owner and repo name.

        Supports both SSH and HTTPS Git URL formats:
        - SSH: git@github.com:owner/repo.git
        - HTTPS: https://github.com/owner/repo.git

        Args:
            repo_url (str): The Git repository URL to parse.

        Returns:
            Tuple[str, str]: A tuple containing (repo_owner, repo_name).

        Raises:
            ValueError: If the URL format is not recognized.
        """
        # Remove .git suffix if present
        clean_url = repo_url.rstrip("/").replace(".git", "")

        # SSH format: git@github.com:owner/repo
        ssh_pattern = r"^git@([^:]+):([^/]+)/(.+)$"
        ssh_match = re.match(ssh_pattern, clean_url)
        if ssh_match:
            owner = ssh_match.group(2)
            repo_name = ssh_match.group(3)
            return owner, repo_name

        # HTTPS format: https://github.com/owner/repo
        https_pattern = r"^https://([^/]+)/([^/]+)/(.+)$"
        https_match = re.match(https_pattern, clean_url)
        if https_match:
            owner = https_match.group(2)
            repo_name = https_match.group(3)
            return owner, repo_name

        # Fallback: try to parse from path segments
        if "/" in clean_url:
            path_parts = clean_url.split("/")
            if len(path_parts) >= 2:
                owner = path_parts[-2]
                repo_name = path_parts[-1]
                return owner, repo_name

        raise ValueError(f"Unable to parse Git repository URL: {repo_url}")

    def clone(self, branch_name: str = "main") -> ExecResult:
        """Clone the repo."""
        cmd = self.commands.clone(
            repo_url=self.repo_remote_url,
            branch=branch_name,
            working_dir=self.repo_local_base_dir,
        )
        cmd.env = self.ssh_agent_env_vars
        return self.executor.execute(command=cmd)

    def pull(self) -> ExecResult:
        """Pull the repo."""
        cmd = self.commands.pull(
            branch=self.branch_name, working_dir=self.full_repo_path
        )
        cmd.env = self.ssh_agent_env_vars
        return self.executor.execute(command=cmd)

    def status(self) -> ExecResult:
        """Get the status of the repo."""
        result: ExecResult = self.executor.execute(
            command=self.commands.status(working_dir=self.full_repo_path)
        )
        logger.debug("repo git status, %s", result.stdout)
        return result

    def is_cloned(self) -> bool:
        """Check if the repo is cloned."""
        is_cloned: bool = False

        repo_dir: Directory = Directory(
            executor=self.executor,
            commands=self._dir_cmds,
            path=self.full_repo_path,
        )

        # dir_exists_cmd: RunnableCommandString = self._uc.dir_exists(
        #     directory=f"{self.local_repo_base_dir}/{self.repo_name}"
        # )

        # result: ExecResult = self.executor.execute(command=dir_exists_cmd)

        # dir_exists: bool = result.success
        logger.debug(f"Checking if the repo '{self.repo_name}' is cloned...")
        logger.debug(f"Checking if repo directory exists: {repo_dir.exists()}")
        if not repo_dir.exists():
            logger.debug(
                f"Repo directory '{self.repo_name}' does not exist. Repo hasn't been cloned yet."
            )
            is_cloned = False
            return is_cloned

        # there's dir with the repo name, check if it's a git repo
        logger.debug(f"Repo directory '{self.repo_name}' exists.")
        logger.debug(f"Checking if the repo '{self.repo_name}' is a git repository...")
        if self.status().success:
            # it's a git repo
            is_cloned = True
        else:
            is_cloned = False
        logger.debug(f"Repo '{self.repo_name}' is cloned: {is_cloned}")
        return is_cloned

    def latest_commit_hash(self) -> str:
        """Get the latest commit hash."""
        result: ExecResult = self.executor.execute(
            command=self.commands.latest_commit_hash(working_dir=self.full_repo_path)
        )
        if result.success and result.stdout is not None:
            return result.stdout.strip()
        else:
            raise Exception(f"Failed to get latest commit hash: {result.stderr}")

    def get_remote_url(self, remote_name: str = "origin") -> ExecResult[str]:
        """Get the URL of a remote repository.

        Args:
            remote_name (str, optional): The name of the remote. Defaults to "origin".

        Returns:
            ExecResult[str]: Result containing the remote URL in the result field if successful
        """
        cmd = self.commands.remote_get_url(
            remote_name=remote_name, working_dir=self.full_repo_path
        )
        cmd.env = self.ssh_agent_env_vars
        exec_result = self.executor.execute(command=cmd)

        # Parse stdout and populate result field
        if exec_result.success and exec_result.stdout is not None:
            exec_result.result = exec_result.stdout.strip()

        return exec_result

    def is_ssh_repo_url(self) -> bool:
        """Check if this repository's configured URL is in SSH format.

        Returns:
            bool: True if URL is SSH format (git@github.com:), False otherwise
        """
        return GitRepo.is_url_ssh_format(self.repo_remote_url)

    def is_https_repo_url(self) -> bool:
        """Check if this repository's configured URL is in HTTPS format.

        Returns:
            bool: True if URL is HTTPS format (https://), False otherwise
        """
        return GitRepo.is_url_https_format(self.repo_remote_url)

    @staticmethod
    def is_url_https_format(url: str) -> bool:
        """Check if a given URL string is in HTTPS format.

        Args:
            url (str): The URL to check

        Returns:
            bool: True if URL is HTTPS format (https://), False otherwise
        """
        return url.startswith("https://")

    @staticmethod
    def is_url_ssh_format(url: str) -> bool:
        """Check if a given URL string is in SSH format.

        Args:
            url (str): The URL to check

        Returns:
            bool: True if URL is SSH format (git@), False otherwise
        """
        return url.startswith("git@")
