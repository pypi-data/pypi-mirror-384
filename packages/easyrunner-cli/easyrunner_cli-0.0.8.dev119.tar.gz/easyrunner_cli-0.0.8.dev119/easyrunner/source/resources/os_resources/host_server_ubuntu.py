import io
import os
import re
from importlib.abc import Traversable
from typing import Callable, List, LiteralString, Optional, Self, cast

from .... import logger
from ...command_executor import CommandExecutor
from ...commands.base.null_command import NullCommand
from ...commands.base.utility_commands import UtilityCommands
from ...commands.runnable_command_string import RunnableCommandString
from ...commands.ubuntu.archive_commands_ubuntu import ArchiveCommandsUbuntu
from ...commands.ubuntu.caddy_commands_container_ubuntu import (
    CaddyCommandsContainerUbuntu,
)
from ...commands.ubuntu.dir_commands_ubuntu import DirCommandsUbuntu
from ...commands.ubuntu.file_commands_ubuntu import FileCommandsUbuntu
from ...commands.ubuntu.git_commands_ubuntu import GitCommandsUbuntu
from ...commands.ubuntu.ip_tables_commands_ubuntu import IpTablesCommandsUbuntu
from ...commands.ubuntu.os_package_manager_commands_ubuntu import (
    OsPackageManagerCommandsUbuntu,
)
from ...commands.ubuntu.podman_commands_ubuntu import PodmanCommandsUbuntu
from ...commands.ubuntu.ssh_agent_commands_ubuntu import SshAgentCommandsUbuntu
from ...commands.ubuntu.systemctl_commands_ubuntu import SystemctlCommandsUbuntu
from ...commands.ubuntu.user_commands_ubuntu import UserCommandsUbuntu
from ...ssh_key import SshKey
from ...types.compose_project.compose_project import ComposeProject
from ...types.cpu_arch_types import CpuArch
from ...types.dir_info import DirInfo
from ...types.exec_result import ExecResult
from ...types.file_info import FileInfo
from ...types.json import JsonArray, JsonObject
from ...types.os_type import OS
from ..cloud_resources.github.github_api_client import GitHubApiClient
from ..cloud_resources.github.github_repo import GithubRepo
from .caddy import Caddy
from .directory import Directory
from .file import File
from .git_repo import GitRepo
from .ip_tables import IpTables
from .os_package_manager import OsPackageManager
from .os_resource_base import OsResourceBase
from .podman import Podman
from .podman_network import PodmanNetwork
from .ssh_agent import SshAgent
from .systemd_service import SystemdService
from .user import User


class HostServerUbuntu(OsResourceBase):
    """
    Represents an Ubuntu remote host server OS level resource.
    This class is unaware of the physical server location, provider etc.

    Args:
        easyrunner_username (str): The username for the EasyRunner service account
        executor (CommandExecutor): The command executor to use for running commands
        debug (bool): Whether to enable debug mode
        silent (bool): Whether to suppress output
        progress_callback (Optional[Callable[[str, str], None]]): Optional callback function to report progress updates with message and end parameter
    """

    def __init__(
        self,
        easyrunner_username: str,
        executor: CommandExecutor,
        debug: bool,
        silent: bool,
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ):
        super().__init__(commands=NullCommand(), executor=executor)

        self._uc = UtilityCommands(
            os=OS.UBUNTU, cpu_arch=CpuArch.X86_64, command_name=""
        )

        self._archive_commands = ArchiveCommandsUbuntu(cpu_arch=CpuArch.X86_64)
        self._dir_cmds = DirCommandsUbuntu(cpu_arch=CpuArch.X86_64)
        self._file_cmds = FileCommandsUbuntu(cpu_arch=CpuArch.X86_64)
        self._sysetmctl_cmds = SystemctlCommandsUbuntu()
        self._user_cmds = UserCommandsUbuntu(cpu_arch=CpuArch.X86_64)

        self._os_package_manager: OsPackageManager = OsPackageManager(
            commands=OsPackageManagerCommandsUbuntu(CpuArch.X86_64),
            executor=self.executor,
        )

        self._command_executor = executor

        self._easyrunner_username = easyrunner_username
        """The username for the EasyRunner service account."""

        self._easyrunner_user = User(
            executor=self.executor,
            commands=self._user_cmds,
            username=self._easyrunner_username,
        )
        """The EasyRunner service account user object."""

        # TODO: this should be grabbed from User.get_home_directory() for the 'easyrunner' user
        self._easyrunner_home_dir = "/home/easyrunner"
        self._apps_source_dir: LiteralString = (
            f"{self._easyrunner_home_dir}/easyrunner-stack/apps-source"
        )
        self._infra_config_dir: LiteralString = (
            f"{self._easyrunner_home_dir}/easyrunner-stack/infra"
        )
        self._apps_compose_dir: LiteralString = (
            f"{self._infra_config_dir}/docker-compose"
        )
        self._easyrunner_stack_compose_file: LiteralString = (
            f"{self._infra_config_dir}/docker-compose/docker-compose-host.yaml"
        )

        self._server_config_archive_filename: LiteralString = "server-config.tar.gz"

        # self._systemd_user_config_dir: LiteralString = (
        #     f"{self._easyrunner_home_dir}/.config/systemd/user"
        # )

        self._quadlets_config_dir: LiteralString = (
            f"{self._easyrunner_home_dir}/.config/containers/systemd"
        )

        self._github_repo_deploy_key_name_prefix: LiteralString = "easyrunner"

        self.debug: bool = debug
        self.silent: bool = silent
        self.progress_callback: Optional[Callable[[str, str], None]] = progress_callback

    def _report_progress(self, message: str, end: str = "\n") -> None:
        """Report progress using the configured callback if available.

        Args:
            message: The progress message to report
            end: The end character for the message (e.g., "\n" or "")
        """
        if self.progress_callback:
            self.progress_callback(message, end)

    def setup_ssh(self, username: str) -> ExecResult:
        """Setup SSH directory structure with correct permissions

        Args:
            username (str): The username for which to setup the SSH directory
        """
        try:
            user = User(
                executor=self.executor, commands=self._user_cmds, username=username
            )

            user_home_dir: str | None = user.get_home_directory().result

            if user_home_dir is None:
                error_msg = f"Failed to get home directory for user: {username}. Cannot proceed with SSH setup."
                logger.error(error_msg)
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=error_msg,
                )

            # Check if .ssh directory exists
            ssh_dir: Directory = Directory(
                executor=self.executor,
                commands=self._dir_cmds,
                path=f"{user_home_dir}/.ssh",
            )
            if not ssh_dir.exists():
                # Create .ssh directory if it doesn't exist
                # self.executor.execute(command=self._uc.mkdir("~/.ssh"))
                ssh_dir.create(owner=username, group=username, mode="700")
                logger.debug(
                    f"Created SSH directory: {ssh_dir.path} with permission 700 owner: rwx, group: none, others: none"
                )

                if not ssh_dir.set_owner(
                    owner_user=username, owner_group=username
                ).success:
                    error_msg = (
                        f"Failed to set ownership of SSH directory: {ssh_dir.path}"
                    )
                    logger.error(error_msg)
                    return ExecResult(
                        success=False,
                        return_code=1,
                        stdout="",
                        stderr=error_msg,
                    )

            return ExecResult(
                success=True,
                return_code=0,
                stdout=f"SSH directory setup successfully for user: {username}",
                stderr="",
            )
        except Exception as e:
            error_msg = f"Failed to setup SSH directory: {str(e)}"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

    # def dir_exists(self, directory: str) -> bool:
    #     """Check if directory exists"""
    #     return (
    #         self.executor.execute(command=self._uc.dir_exists(directory)).return_code
    #         == 0
    #     )

    def add_public_key_to_authorised_keys(
        self, username: str, ssh_public_key: str
    ) -> ExecResult:
        """Add public key to remote 'authorized_keys' file and make sure it has the correct permissions."""
        try:
            # Ensure SSH directory exists
            self.setup_ssh(username=username)

            user = User(
                executor=self.executor, commands=self._user_cmds, username=username
            )

            # Format key - ensure single line and newline at end
            ssh_public_key = ssh_public_key.strip()
            if not ssh_public_key.endswith("\n"):
                ssh_public_key += "\n"

            # Append key to authorized_keys
            user_home_dir: str | None = user.get_home_directory().result

            if user_home_dir is None:
                logger.error(
                    f"Failed to get home directory for user: {username}. Cannot proceed with SSH setup."
                )
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=f"Failed to get home directory for user: {username}. Cannot proceed with SSH setup.",
                )

            authorized_keys_path = f"{user_home_dir.strip()}/.ssh/authorized_keys"
            authorized_keys_file = File(
                executor=self.executor,
                commands=self._file_cmds,
                path=authorized_keys_path,
            )

            if not authorized_keys_file.exists():
                authorized_keys_file.create(owner=username, group=username, mode="600")

            content = authorized_keys_file.open_read()

            if (
                content is not None
                and content.result is not None
                and ssh_public_key in content.result
            ):
                logger.debug(
                    f"Public key already exists in '{authorized_keys_path}', skipping addition."
                )
                return ExecResult(
                    success=True,
                    return_code=0,
                    stdout=f"Public key already exists in '{authorized_keys_path}'",
                    stderr="",
                )

            # result1 = self.executor.execute(
            #     command=RunnableCommandString(
            #         command=f"echo '{ssh_public_key}'",
            #         output_to_file=authorized_keys_file.path,
            #         append_or_overwrite="APPEND",
            #     )
            # )

            result1 = authorized_keys_file.open_write(
                content=ssh_public_key, mode="APPEND"
            )

            # Ensure Set correct file permissions
            result2 = authorized_keys_file.set_permissions(mode="600")

            error = result1.stderr or result2.stderr

            return ExecResult(
                success=result1.success and result2.success,
                return_code=int(not (result1.success and result2.success)),
                stdout=(
                    f"Public key added to '{authorized_keys_file.path}'"
                    if not error
                    else ""
                ),
                stderr=error,
            )

        except Exception as e:
            # raise RuntimeError(f"Failed to add public key: {str(e)}")
            error_msg = f"Failed to add public key: {str(e)}"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

    def add_private_key(
        self,
        private_key: str,
        hostname: str,
        username: str,
        private_key_filename: str,
        use_ssh_agent: bool = False,
        metadata: str | None = None,
    ) -> str | None:
        """Add private key to remote host and configure SSH authentication.

        We do this when the host is the client accessing a remote service such as GitHub.com.
        The public key of the pair needs to be added to the remote service manually.

        Args:
            private_key (str): The content of the private key.
            hostname (str): The hostname of the remote host service e.g. github.com.
            username (str): The username to use for the SSH connection to the remote host. This is usually defined by the remote service like github.com.
            private_key_filename (str): The name of the file to save the private key to (only used when use_ssh_agent=False). This should be unique for each host and key type. The recommended file naming convention is hostname_keytype. For example, github_com_ed25519.
            use_ssh_agent (bool, optional): Whether to add key to SSH agent (memory only) instead of saving to file. Defaults to False.
            metadata (str | None, optional): Optional metadata to include with SSH agent key (only used when use_ssh_agent=True). Defaults to None.

        Returns:
            str | None: The file path to the private key file if use_ssh_agent=False, None if use_ssh_agent=True (key stored in memory only).
        """
        if use_ssh_agent:
            # Add key directly to SSH agent (memory only, no file)
            self._configure_ssh_agent_key(private_key, hostname, username, metadata)
            return None
        else:
            # Save key to file and configure file-based SSH
            private_key_file_path = self._save_private_key_file(
                private_key, private_key_filename
            )
            self._configure_ssh_file_key(private_key_file_path, hostname, username)
            return private_key_file_path

    def _save_private_key_file(
        self, private_key: str, private_key_filename: str
    ) -> str:
        """Save private key content to file with proper permissions."""
        private_key_file_path = (
            f"{self._easyrunner_home_dir}/.ssh/{private_key_filename}"
        )

        private_key_file = File(
            executor=self.executor,
            commands=self._file_cmds,
            path=private_key_file_path,
        )

        if not private_key_file.exists():
            private_key_file.create(
                owner=self._easyrunner_username,
                group=self._easyrunner_username,
                mode="600",
            )
            logger.debug(f"Empty private key file '{private_key_file.path}' created.")

        private_key_write_result = private_key_file.open_write(
            content=private_key, mode="OVERWRITE"
        )
        if not private_key_write_result.success:
            raise RuntimeError(
                f"SSH key config error: Failed to write private key to {private_key_file.path}. Error: {private_key_write_result.stderr}"
            )
        logger.debug(
            f"Successfully wrote private key content to {private_key_file.path}"
        )

        private_key_perms_result = private_key_file.set_permissions(mode="600")
        if not private_key_perms_result.success:
            raise RuntimeError(
                f"SSH key config error: Failed to set permissions on {private_key_file_path}. Error: {private_key_perms_result.stderr}"
            )

        return private_key_file_path

    def _configure_ssh_agent_key(
        self,
        private_key_content: str,
        hostname: str,
        username: str,
        metadata: str | None = None,
    ) -> None:
        """Configure SSH for agent-based authentication (key stored in memory only)."""
        # Add key directly to SSH agent from content (no file involved)
        ssh_agent = self.get_ssh_agent()
        add_result = ssh_agent.add_key_from_content(
            private_key_content, comment_content=metadata
        )
        if not add_result.success:
            raise RuntimeError(f"Failed to add key to SSH agent: {add_result.stderr}")
        logger.debug(
            f"Successfully added private key for {hostname} to SSH agent (memory only)"
        )

        # Create SSH config entry WITHOUT IdentitiesOnly (allows all agent keys to be tried)
        # With IdentitiesOnly=yes and no IdentityFile, SSH won't offer ANY keys
        # With IdentitiesOnly=no (default), SSH will try all agent keys
        self._update_ssh_config(
            hostname, username, private_key_file_path=None, identities_only=False
        )

    def _configure_ssh_file_key(
        self, private_key_file_path: str, hostname: str, username: str
    ) -> None:
        """Configure SSH for file-based authentication with IdentitiesOnly=yes."""
        self._update_ssh_config(
            hostname, username, private_key_file_path, identities_only=True
        )

    def _update_ssh_config(
        self,
        hostname: str,
        username: str,
        private_key_file_path: str | None,
        identities_only: bool,
    ) -> None:
        """Update SSH config file with host entry.

        Args:
            hostname: The hostname for the SSH config entry
            username: The username for the SSH connection
            private_key_file_path: Path to private key file, or None for agent-only mode
            identities_only: Whether to set IdentitiesOnly=yes or no
        """
        ssh_config_file_path = f"{self._easyrunner_home_dir}/.ssh/config"
        ssh_config_file = File(
            executor=self.executor,
            commands=self._file_cmds,
            path=ssh_config_file_path,
        )

        if not ssh_config_file.exists():
            ssh_config_create_result = ssh_config_file.create(
                owner=self._easyrunner_username,
                group=self._easyrunner_username,
                mode="600",
            )
            if not ssh_config_create_result.success:
                raise RuntimeError(
                    f"Failed to create SSH config file at {ssh_config_file_path}. Error: {ssh_config_create_result.stderr}"
                )
            logger.debug(
                f"Successfully created SSH config file at '{ssh_config_file_path}'"
            )

        ssh_config_content_result = ssh_config_file.open_read()
        if not ssh_config_content_result.success:
            raise RuntimeError(
                f"Failed to read SSH config file at {ssh_config_file_path}. Error: {ssh_config_content_result.stderr}"
            )

        ssh_config_content = ssh_config_content_result.result or ""

        # Remove existing entry for this hostname if it exists
        if f"Host {hostname}" in ssh_config_content:
            logger.debug(f"Removing existing SSH config entry for {hostname}")
            pattern = rf"^Host\s+{re.escape(hostname)}\s*\n(?:\s+.*\n)*"
            ssh_config_content = re.sub(
                pattern, "", ssh_config_content, flags=re.MULTILINE
            )

        # Create new SSH config entry
        identities_setting = "yes" if identities_only else "no"
        ssh_config_entry = (
            f"Host {hostname}\n\tHostname {hostname}\n\tUser {username}\n"
        )

        # Only add IdentityFile if we have a file path (not for agent-only mode)
        if private_key_file_path is not None:
            ssh_config_entry += f"\tIdentityFile {private_key_file_path}\n"

        ssh_config_entry += f"\tIdentitiesOnly {identities_setting}\n"
        ssh_config_entry += "\tStrictHostKeyChecking accept-new\n"

        # Write updated config
        ssh_config_write_result = ssh_config_file.open_write(
            content=ssh_config_content + ssh_config_entry, mode="OVERWRITE"
        )

        if not ssh_config_write_result.success:
            raise RuntimeError(
                f"Failed to write SSH config entry for {hostname}. Error: {ssh_config_write_result.stderr}"
            )

        config_type = "agent-based" if private_key_file_path is None else "file-based"
        logger.debug(
            f"Successfully added {config_type} SSH config entry for {hostname} (IdentitiesOnly={identities_setting})"
        )

    def get_ssh_agent(self) -> SshAgent:
        """Get a reference to SSH Agent on the server.

        If not running, setup and start SSH agent for the easyrunner user on the server.

        Args:
            socket_path: Optional custom socket path for the SSH agent

        Returns:
            SshAgent: Configured SSH agent resource instance

        Raises:
            RuntimeError: If SSH agent setup fails
        """
        # TODO: extend set_ssh_agent to support multiple ssh agent instances.
        try:
            # Create SSH agent resource with absolute socket path
            ssh_agent_commands = SshAgentCommandsUbuntu(cpu_arch=CpuArch.X86_64)
            socket_path = f"{self._easyrunner_home_dir}/.ssh/ssh_agent_er.sock"
            self._ssh_agent = SshAgent(
                executor=self.executor,
                commands=ssh_agent_commands,
                socket_path=socket_path,
            )

            # Start SSH agent if not already running
            if not self._ssh_agent.is_running():
                logger.debug("Starting SSH agent...")
                start_result = self._ssh_agent.start()
                if not start_result.success:
                    raise RuntimeError(
                        f"Failed to start SSH agent: {start_result.stderr}"
                    )
                logger.debug(
                    f"SSH agent started with PID: {self._ssh_agent.agent_pid}, Socket: {self._ssh_agent.auth_sock}"
                )
            else:
                logger.debug("SSH agent is already running")

            return self._ssh_agent

        except Exception as e:
            error_msg = f"Failed to setup SSH agent: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def create_user(
        self,
        username: str,
        password: Optional[str] = None,
        create_home: bool = True,
        shell: str = "/bin/bash",
    ) -> ExecResult[User]:
        """Create a new user on the remote host.

        Args:
            username (str): The username for the new user.
            password (Optional[str]): The password for the user. If None, no password is set.
            create_home (bool): Whether to create a home directory for the user. Defaults to True.
            shell (str): The default shell for the user. Defaults to "/bin/bash".

        Returns:
            ExecResult: The result of the user creation command.
        """
        try:
            user = User(
                executor=self.executor, commands=self._user_cmds, username=username
            )
            # Check if user already exists
            if user.exists():
                logger.debug(f"User {username} already exists")
                return ExecResult(
                    success=True,
                    return_code=0,
                    stdout=f"User {username} already exists",
                    stderr="",
                )

            # Create user using command class
            result = user.create()

            if result.success:
                if password is not None:
                    # Set password using command class
                    passwd_result = user.set_password(password)
                    if not passwd_result.success:
                        logger.warning(
                            f"User {username} created but password setting failed: {passwd_result.stderr}"
                        )

            if result.success:
                logger.debug(f"Successfully created user: {username}")
            else:
                logger.error(f"Failed to create user {username}: {result.stderr}")

            result.result = user  # Set the result to the User object
            return result

        except Exception as e:
            error_msg = f"Failed to create user {username}: {str(e)}"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

    def add_user_to_groups(self, username: str, groups: List[str]) -> ExecResult:
        """Add a user to one or more groups on the remote host.

        Args:
            username (str): The username to add to groups.
            groups (List[str]): List of group names to add the user to.

        Returns:
            ExecResult: The result of the group assignment commands.
        """
        try:
            # Check if user exists
            check_user_cmd = self._user_cmds.check_user_exists(username)
            check_result = self.executor.execute(command=check_user_cmd)

            if check_result.return_code != 0:
                error_msg = f"User {username} does not exist"
                logger.error(error_msg)
                return ExecResult(
                    success=False, return_code=1, stdout="", stderr=error_msg
                )

            # Add user to each group
            failed_groups = []
            for group in groups:
                usermod_cmd = self._user_cmds.add_user_to_group(username, group)
                result = self.executor.execute(command=usermod_cmd)

                if not result.success:
                    failed_groups.append(group)
                    logger.warning(
                        f"Failed to add user {username} to group {group}: {result.stderr}"
                    )
                else:
                    logger.debug(f"Successfully added user {username} to group {group}")

            if failed_groups:
                error_msg = f"Failed to add user {username} to groups: {', '.join(failed_groups)}"
                return ExecResult(
                    success=False, return_code=1, stdout="", stderr=error_msg
                )
            else:
                success_msg = (
                    f"Successfully added user {username} to groups: {', '.join(groups)}"
                )
                return ExecResult(
                    success=True, return_code=0, stdout=success_msg, stderr=""
                )

        except Exception as e:
            error_msg = f"Failed to add user {username} to groups: {str(e)}"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

    def add_ssh_key_to_user(
        self, username: str, ssh_public_key_content: str
    ) -> ExecResult:
        """Add an SSH public key to a specific user's authorized_keys file.

        Args:
            username (str): The username to associate the SSH key with.
            ssh_public_key (str): The SSH public key content to add.

        Returns:
            ExecResult: The result of adding the SSH key to the user.
        """
        try:
            user = User(
                executor=self.executor, commands=self._user_cmds, username=username
            )
            # Check if user exists

            # check_user_cmd = self._user_cmds.check_user_exists(username)
            # check_result = self.executor.execute(command=check_user_cmd)

            if not user.exists():
                error_msg = f"User {username} does not exist"
                logger.error(error_msg)
                return ExecResult(
                    success=False, return_code=1, stdout="", stderr=error_msg
                )

            if ssh_public_key_content.strip() == "":
                error_msg = "Provided SSH public key content is empty"
                logger.error(error_msg)
                return ExecResult(
                    success=False, return_code=1, stdout="", stderr=error_msg
                )

            # Get user's home directory
            home_result = user.get_home_directory()
            # home_dir_cmd = self._user_cmds.get_user_home_directory(username)
            # home_result = self.executor.execute(command=home_dir_cmd)

            if (
                not home_result.success
                or not home_result.stdout
                or home_result.result is None
            ):
                error_msg = f"Failed to get home directory for user {username}"
                logger.error(error_msg)
                return ExecResult(
                    success=False, return_code=1, stdout="", stderr=error_msg
                )

            user_home = home_result.result.strip()
            ssh_path = f"{user_home}/.ssh"
            authorized_keys_path = f"{ssh_path}/authorized_keys"

            # ssh_dir = Directory(
            #     executor=self.executor, commands=self._dir_cmds, path=ssh_path
            # )
            # # Create .ssh directory if it doesn't exist using dir commands
            # if not ssh_dir.exists():
            #     ssh_dir.create()

            # # Set proper ownership and permissions for .ssh directory using dir commands
            # ssh_dir.set_owner(owner_user=username, owner_group=username)
            # ssh_dir.set_permissions(mode="700")

            ssh_setup_result = self.setup_ssh(username=username)
            if not ssh_setup_result.success:
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=ssh_setup_result.stderr,
                )

            authorized_keys_file = File(
                executor=self.executor,
                commands=self._file_cmds,
                path=authorized_keys_path,
            )
            if not authorized_keys_file.exists():
                if not authorized_keys_file.create(
                    owner=username, group=username, mode="600"
                ).success:
                    error_msg = f"Failed to create authorized_keys file at {authorized_keys_path}"
                    logger.error(error_msg)
                    return ExecResult(
                        success=False, return_code=1, stdout="", stderr=error_msg
                    )

            # Add the public key to authorized_keys and set permissions
            if not self.add_public_key_to_authorised_keys(
                username=username, ssh_public_key=ssh_public_key_content
            ).success:
                error_msg = (
                    f"Failed to add public key to authorized_keys for user {username}"
                )
                logger.error(error_msg)
                return ExecResult(
                    success=False, return_code=1, stdout="", stderr=error_msg
                )

            # Set proper ownership and permissions for authorized_keys using file commands
            authorized_keys_file.set_owner(owner_user=username, owner_group=username)

            success_msg = f"Successfully added SSH key to user '{username}'"
            logger.debug(success_msg)

            authorized_keys_file_content = authorized_keys_file.open_read()
            if authorized_keys_file_content.success:
                logger.debug(f"content: {authorized_keys_file_content.result}")
                logger.debug(f"stdout: {authorized_keys_file_content.stdout}")
                return ExecResult(
                    success=True, return_code=0, stdout=success_msg, stderr=""
                )
            else:
                logger.error(
                    f"Failed to read authorized_keys file: {authorized_keys_file_content.stderr}"
                )
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=authorized_keys_file_content.stderr,
                )

        except Exception as e:
            error_msg = f"Failed to add SSH key to user {username}: {str(e)}"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

    def add_key_to_known_hosts(self: Self, ssh_key: str) -> None:
        """Add the specified host's public SSH key to the known_hosts file for the current user i.e. the one that ssh connection is made from.

        Args:
            ssh_key (str): The full public SSH key to add in known_hosts format: "hostname key_type key_value".
        """

        try:
            # TODO: refactor known_hosts into a resource class

            # Ensure SSH directory exists
            self.setup_ssh(self.executor.ssh_client.username)

            # user = User(
            #     executor=self.executor,
            #     commands=self._user_cmds,
            #     username=self.executor.ssh_client.username,
            # )

            known_hosts_file_path = (
                f"/home/{self.executor.ssh_client.username}/.ssh/known_hosts"
            )

            # Check if known_hosts file exists, create if not
            known_hosts_file: File = File(
                executor=self.executor,
                commands=self._file_cmds,
                path=known_hosts_file_path,
            )

            if not known_hosts_file.exists():
                # Create known_hosts file if it doesn't exist
                # touch_cmd = RunnableCommandString(
                #     command=f"touch {known_hosts_file.path}"
                # )
                # self.executor.execute(command=touch_cmd)
                known_hosts_file.create(
                    owner=self.executor.ssh_client.username,
                    group=self.executor.ssh_client.username,
                    mode="600",
                )

            # Extract hostname and key type from ssh_key for more specific matching
            try:
                ssh_key_parts = ssh_key.split()
                if len(ssh_key_parts) >= 3:
                    # First part is the hostname
                    hostname = ssh_key_parts[0]
                    # Second part is the key type (e.g., ssh-ed25519, ssh-rsa)
                    key_type = ssh_key_parts[1]
                else:
                    # Invalid key format
                    raise ValueError(
                        "Invalid SSH key format. Expected format: 'hostname key_type key_value'"
                    )
            except (IndexError, AttributeError, ValueError) as e:
                raise RuntimeError(f"Failed to parse SSH key: {str(e)}")

            # check_cmd = RunnableCommandString(
            #     command=f"grep -q '{hostname} {key_type}' {known_hosts_file.path}"
            # )
            # check_result = self.executor.execute(command=check_cmd)

            # if check_result.return_code != 0:
            #     # # Get the SSH key for the specified host using ssh-keyscan and append it to the known_hosts file
            #     # scan_cmd = RunnableCommandString(
            #     #     command=f"ssh-keyscan -t {key_type.value} {hostname}",
            #     #     output_to_file=known_hosts_file.path,
            #     #     append_or_overwrite="APPEND",
            #     # )

            #     # TODO: refactor how we do content append/replace. switch to pipe | rather than >>. and tee -a. Also remove the special case from the RunnableCommandString interface.
            #     cmd = RunnableCommandString(
            #         command=f"echo {ssh_key}",
            #         output_to_file=known_hosts_file.path,
            #         append_or_overwrite="APPEND",
            #     )

            # result = self.executor.execute(command=cmd)

            # Check if the specific hostname and key type combination is already in known_hosts
            known_hosts_file_result = known_hosts_file.open_read()
            if known_hosts_file_result.success:
                known_hosts_file_content = known_hosts_file_result.result
                if (
                    known_hosts_file_content
                    and f"{hostname} {key_type}" not in known_hosts_file_content
                ):
                    result1 = known_hosts_file.open_write(
                        content=ssh_key, mode="APPEND"
                    )

                    if result1.success:
                        logger.debug(
                            f"Successfully added {hostname} to known_hosts file"
                        )
                    else:
                        raise RuntimeError(
                            f"Failed to add {hostname} ssh key to known_hosts: {result1.stderr}"
                        )
                else:
                    logger.debug(
                        f"{hostname} {key_type} already exists in known_hosts file"
                    )

        except Exception as e:
            raise RuntimeError(f"Failed to set up host key: {str(e)}")

    def ensure_easyrunner_ops_user_is_setup(
        self, easyrunner_ops_user_ssh_public_key_content: str
    ) -> ExecResult[User]:
        """Ensure the `easyrunner` user exists on the host server with correct permissions and SSH key.
        This is the user and SSH key that the EasyRunner CLI or other client will use to connect to host server.
        EasyRunner ops user SSH key pairs are generated one per host server being managed by EasyRunner.

        Args:
            easyrunner_ops_user_ssh_public_key_content (str): The content of the SSH public key to add to the easyrunner user's authorized_keys file.
            The key pair must be generated on the client machine that connects to the host server e.g. where the EasyRunner CLI is run from.
        """
        # add user named `easyrunner` if it doesn't exist.
        # Create the user `easyrunner` on the server. strictly no passwords.
        self._report_progress("\n👤 USER SETUP", end="\n")
        self._report_progress(" [yellow]Creating EasyRunner user...[/yellow]", end="")
        self.create_user(username=self._easyrunner_username)
        self._report_progress(" [green]✔[/green]", end="\n")

        user = User(
            executor=self.executor,
            commands=self._user_cmds,
            username=self._easyrunner_username,
        )

        # Fix home directory ownership to ensure SSH authentication works
        # This is critical because SSH will refuse to authenticate if the home directory
        # has incorrect ownership (e.g., owned by a different UID/GID)
        # Use the Directory resource to handle ownership - follows existing pattern
        self._report_progress(
            " [yellow]Fixing home directory ownership...[/yellow]", end=""
        )
        home_dir_result = user.get_home_directory()
        if home_dir_result.success and home_dir_result.result:
            home_dir = Directory(
                executor=self.executor,
                commands=self._dir_cmds,
                path=home_dir_result.result,
            )
            fix_ownership_result = home_dir.set_owner(
                owner_user=self._easyrunner_username,
                owner_group=self._easyrunner_username,
                recursive=True,
            )
            if not fix_ownership_result.success:
                logger.warning(
                    f"Failed to fix home directory ownership for user {self._easyrunner_username}: {fix_ownership_result.stderr}"
                )
                # Continue anyway as this might not be critical in all cases
        else:
            logger.warning(
                f"Failed to get home directory for user {self._easyrunner_username}, skipping ownership fix"
            )
        self._report_progress(" [green]✔[/green]", end="\n")

        # Only add to sudoers if the user doesn't already have sudo access
        if not user.has_sudo_access():
            logger.debug(
                f"User {self._easyrunner_username} does not have sudo access, adding to sudoers"
            )
            self._report_progress(
                " [yellow]Configuring user permissions...[/yellow]", end=""
            )
            sudoers_result = user.add_to_sudoers_nopasswd()
            self.add_user_to_groups(
                username=self._easyrunner_username,
                groups=["sudo", "systemd-journal"],
            )
            if not sudoers_result.success:
                logger.warning(
                    f"Failed to add user {self._easyrunner_username} to sudoers: {sudoers_result.stderr}"
                )
                # Don't fail the entire installation if sudoers setup fails on subsequent runs
                logger.warning(
                    "Continuing with installation despite sudoers setup failure"
                )
            self._report_progress(" [green]✔[/green]", end="\n")
        else:
            logger.debug(
                f"User {self._easyrunner_username} already has sudo access, skipping sudoers setup"
            )
            self._report_progress(
                " [green]✔[/green] User permissions already configured", end="\n"
            )

        if not self.add_ssh_key_to_user(
            username=self._easyrunner_username,
            ssh_public_key_content=easyrunner_ops_user_ssh_public_key_content,
        ).success:
            error_msg = f"Failed to add SSH key to user {self._easyrunner_username}"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

        result = ExecResult[User](
            success=True,
            return_code=0,
            stdout=f"User {self._easyrunner_username} is set up",
            stderr="",
        )
        result.result = user
        return result

    def update_os_packages(self) -> None:
        # update the list of apt packages. Podman etc. isn't always downloaded.
        self._report_progress("🔄 INITIALIZING INSTALLATION", end="\n")
        self._report_progress(" [yellow]Updating package list...[/yellow]", end="")
        if self._os_package_manager.update_packages().success:
            self._report_progress(" [green]✔[/green]", end="\n")
        else:
            self._report_progress(" [red]✗[/red]", end="\n")

    def install_easyrunner(self) -> None:
        """Setup the host server with the EasyRunner stack."""
        try:
            # Update OS packages
            self.update_os_packages()

            self._report_progress("\n📁 DIRECTORY SETUP", end="\n")
            self._report_progress(
                " [yellow]Creating directory structure...[/yellow]", end=""
            )
            self._ensure_easyrunner_directory_structure()
            self._report_progress(" [green]✔[/green]", end="\n")

            # enable linger for the easyrunner user before any systemd user commands
            # this is required for systemd user services to work correctly
            logger.debug("Enabling linger for the easyrunner user.")
            self._report_progress(
                " [yellow]Enabling user linger for systemd...[/yellow]", end=""
            )
            if not self._enable_linger():
                self._report_progress(" [red]✗[/red]", end="\n")
                raise RuntimeError("Failed to enable linger for the easyrunner user.")
            self._report_progress(" [green]✔[/green]", end="\n")

            self._report_progress("\n📦 PACKAGE INSTALLATION", end="\n")
            self._report_progress(" [yellow]Installing Git...[/yellow]", end="")
            if not self._install_git():
                self._report_progress(" [red]✗[/red]", end="\n")
                raise RuntimeError("Git installation failed.")
            self._report_progress(" [green]✔[/green]", end="\n")

            self._report_progress(" [yellow]Installing Podman...[/yellow]", end="")
            result: ExecResult = self._install_podman()
            if not result.success:
                self._report_progress(" [red]✗[/red]", end="\n")
                # TODO: we shouldn't raise this as an exception. we should return a response object model and let the UI handle the rendering.
                # let the exception handler deal with actual exceptions that bubble up.
                raise RuntimeError(str(result))
            self._report_progress(" [green]✔[/green]", end="\n")

            # enable podman socket
            self._report_progress("\n🐳 PODMAN (CONTAINER RUNTIME) SETUP", end="\n")
            self._report_progress(
                " [yellow]Enabling Podman sockets...[/yellow]", end=""
            )
            # enableSocketCmd: RunnableCommandString = (
            #     PodmanCommandsUbuntu().enable_socket()
            # )
            # self._command_executor.execute(command=enableSocketCmd)

            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)
            podman.enable_sockets()
            self._report_progress(" [green]✔[/green]", end="\n")

            self._report_progress("\n🧱 LOCAL FIREWALL CONFIGURATION", end="\n")
            self._report_progress(
                " [yellow]Configuring explicit inbound rules and drop everything else...[/yellow]",
                end="",
            )
            try:
                self._configure_local_firewall()
                self._report_progress(" [green]✔[/green]", end="\n")
            except Exception as e:
                self._report_progress(" [red]✗[/red]", end="\n")
                logger.error(f"Failed to configure local firewall: {e}")
                raise RuntimeError(f"Failed to configure local firewall: {e}")

            logger.debug("copy config files from templates")
            # copy config files from templates
            self._report_progress("\n📄 CONFIGURATION FILES", end="\n")
            self._report_progress(
                " [yellow]Installing configuration templates...[/yellow]", end=""
            )
            self._put_config_files_on_host()
            self._report_progress(" [green]✔[/green]", end="\n")

            # create shared easyrunner proxy network via quadlet
            self._report_progress("\n🌐 NETWORK SETUP", end="\n")
            self._report_progress(
                " [yellow]Creating proxy network quadlet...[/yellow]", end=""
            )
            self._create_proxy_network_quadlet()
            self._report_progress(" [green]✔[/green]", end="\n")

            # config systemd to manage podman containers
            # we need systemd because in podman rootless mode containers run in the current user's session
            # Therefore terminate when the user (ssh) session terminates. Also doesn't restart on VM reboot.
            self._report_progress("\n🏗️ SYSTEMD SETUP", end="\n")
            self._report_progress(
                " [yellow]Converting compose to systemd units...[/yellow]", end=""
            )
            compose_project = podman.load_compose_file(
                compose_file_path=self._easyrunner_stack_compose_file
            )

            self._convert_compose_file_to_quadlets(compose_project=compose_project)
            self._report_progress(" [green]✔[/green]", end="\n")

            # # start the easy runner docker compose file
            # podman = Podman(PodmanCommandsUbuntu(), self._command_executor)
            # podman.compose_up(compose_file=self._easyrunner_stack_compose_file)
            # DO NOT podman compose up because we wand to run the containers via systemd.

            # reload systemd to pick up the new unit files
            logger.debug("Reloading systemd to pick up new unit files.")
            self._report_progress(
                " [yellow]Reloading systemd daemon...[/yellow]", end=""
            )
            systemd_service = SystemdService(
                commands=self._sysetmctl_cmds,
                executor=self._command_executor,
                ServiceName="",  # not applicable for daemon-reload
                user_mode=True,
                target_username=self._easyrunner_username,
            )
            reload_result: ExecResult = systemd_service.daemon_reload()

            if not reload_result.success:
                self._report_progress(" [red]✗[/red]", end="\n")
                logger.error(f"Failed to reload systemd daemon: {reload_result.stderr}")
                raise RuntimeError(
                    f"Failed to reload systemd daemon: {reload_result.stderr}"
                )
            self._report_progress(" [green]✔[/green]", end="\n")

            # start the easyrunner stack
            logger.debug("Starting the EasyRunner stack.")
            self._report_progress("\n🚀 STARTING SERVICES", end="\n")
            self._report_progress(
                " [yellow]Starting EasyRunner stack...[/yellow]", end=""
            )
            if self.start_easyrunner_stack():
                self._report_progress(" [green]✔[/green]", end="\n")
            else:
                self._report_progress(" [red]✗[/red]", end="\n")

            self._report_progress("\n🌐 WEB SERVER SETUP", end="\n")
            caddy: Caddy = Caddy(
                commands=CaddyCommandsContainerUbuntu(cpu_arch=CpuArch.X86_64),
                executor=self._command_executor,
            )

            logger.debug("Reloading Caddy config.")
            self._report_progress(" [yellow]Configuring web server...[/yellow]", end="")
            caddy.reload_config()

            logger.debug("Fetching Caddy config.")
            caddy.get_config()
            self._report_progress(" [green]✔[/green]", end="\n")

            self._report_progress(
                "\n🎉 EasyRunner installation completed successfully!", end="\n\n"
            )

        except Exception as e:
            raise RuntimeError("Failed to initialise host server.", e)

    def is_easyrunner_installed(self) -> bool:
        """Verify the EasyRunner stack on the host server."""
        result: bool = False
        is_podman_installed: bool = self._os_package_manager.is_package_installed(
            package_commands=PodmanCommandsUbuntu()
        )

        is_git_installed: bool = self._os_package_manager.is_package_installed(
            package_commands=GitCommandsUbuntu(CpuArch.X86_64)
        )

        result = is_podman_installed and is_git_installed
        return result

    def _verify_firewall_nat_rules(self) -> None:
        """Verify NAT table REDIRECT rules for HTTP/HTTPS traffic routing."""
        ipt = IpTables(
            IpTablesCommandsUbuntu(cpu_arch=CpuArch.X86_64), self._command_executor
        )

        # Check HTTP redirect (80 → 8080)
        http_redirect = ipt.check_port_redirect_exists(source_port=80, dest_port=8080)
        http_icon = " [green]✔[/green]" if http_redirect.success else " [red]✗[/red]"
        self._report_progress(
            f"{http_icon} HTTP REDIRECT (80→8080) - Routes web traffic to container port",
            end="\n",
        )

        # Check HTTPS redirect (443 → 8443)
        https_redirect = ipt.check_port_redirect_exists(source_port=443, dest_port=8443)
        https_icon = " [green]✔[/green]" if https_redirect.success else " [red]✗[/red]"
        self._report_progress(
            f"{https_icon} HTTPS REDIRECT (443→8443) - Routes secure traffic to container port",
            end="\n",
        )

    def _verify_firewall_input_basic_rules(self) -> None:
        """Verify basic INPUT chain rules for connection state and loopback."""
        ipt = IpTables(
            IpTablesCommandsUbuntu(cpu_arch=CpuArch.X86_64), self._command_executor
        )

        # Check ESTABLISHED,RELATED connections
        established_rule = ipt.check_inbound_rule_exists(
            protocol="all",
            dport=None,
            action="ACCEPT",
            source_ip="0.0.0.0/0",
            state=["ESTABLISHED", "RELATED"],
        )
        established_icon = (
            " [green]✔[/green]" if established_rule.success else " [red]✗[/red]"
        )
        self._report_progress(
            f"{established_icon} ESTABLISHED/RELATED connections - Allows return traffic",
            end="\n",
        )

        # For loopback, we'll use a custom command since it uses -i lo interface option
        loopback_cmd = RunnableCommandString(
            command="iptables -C INPUT -i lo -j ACCEPT", sudo=True
        )
        loopback_result = self._command_executor.execute(loopback_cmd)
        loopback_icon = (
            " [green]✔[/green]" if loopback_result.success else " [red]✗[/red]"
        )
        self._report_progress(
            f"{loopback_icon} Loopback interface - Allows local system communication",
            end="\n",
        )

    def _verify_firewall_service_ports(self) -> None:
        """Verify INPUT rules for essential service ports (SSH, HTTP, HTTPS)."""
        ipt = IpTables(
            IpTablesCommandsUbuntu(cpu_arch=CpuArch.X86_64), self._command_executor
        )

        # Check SSH access (port 22)
        ssh_rule = ipt.check_inbound_rule_exists(
            protocol="tcp",
            dport=22,
            action="ACCEPT",
            source_ip="0.0.0.0/0",  # Any source
        )
        ssh_icon = " [green]✔[/green]" if ssh_rule.success else " [red]✗[/red]"
        self._report_progress(
            f"{ssh_icon} SSH access (port 22) - Remote administration access",
            end="\n",
        )

        # Check HTTP access (port 80)
        http_rule = ipt.check_inbound_rule_exists(
            protocol="tcp",
            dport=80,
            action="ACCEPT",
            source_ip="0.0.0.0/0",  # Any source
        )
        http_icon = " [green]✔[/green]" if http_rule.success else " [red]✗[/red]"
        self._report_progress(
            f"{http_icon} HTTP access (port 80) - Web traffic entry point",
            end="\n",
        )

        # Check HTTPS access (port 443)
        https_rule = ipt.check_inbound_rule_exists(
            protocol="tcp",
            dport=443,
            action="ACCEPT",
            source_ip="0.0.0.0/0",  # Any source
        )
        https_icon = " [green]✔[/green]" if https_rule.success else " [red]✗[/red]"
        self._report_progress(
            f"{https_icon} HTTPS access (port 443) - Secure web traffic entry point",
            end="\n",
        )

    def _verify_firewall_caddy_api_security(self) -> None:
        """Verify Caddy API access rules (localhost allow, external block)."""
        ipt = IpTables(
            IpTablesCommandsUbuntu(cpu_arch=CpuArch.X86_64), self._command_executor
        )

        # Check Caddy API localhost access
        caddy_localhost = ipt.check_inbound_rule_exists(
            protocol="tcp", dport=2019, action="ACCEPT", source_ip="127.0.0.1"
        )
        localhost_icon = (
            " [green]✔[/green]" if caddy_localhost.success else " [red]✗[/red]"
        )
        self._report_progress(
            f"{localhost_icon} Caddy API localhost access - Local management interface",
            end="\n",
        )

        # Check Caddy API external block
        caddy_block = ipt.check_inbound_rule_exists(
            protocol="tcp", dport=2019, action="DROP", source_ip="0.0.0.0/0"
        )
        block_icon = " [green]✔[/green]" if caddy_block.success else " [red]✗[/red]"
        self._report_progress(
            f"{block_icon} Caddy API external block - Prevents external access to API",
            end="\n",
        )

    def _verify_firewall_conntrack_rules(self) -> None:
        """Verify conntrack-based acceptance for redirected traffic."""
        ipt = IpTables(
            IpTablesCommandsUbuntu(cpu_arch=CpuArch.X86_64), self._command_executor
        )

        # Check conntrack rule for port 8080 (HTTP redirected traffic)
        http_conntrack = ipt.check_accept_redirected_port_tcp_exists(port=8080)
        http_ct_icon = (
            " [green]✔[/green]" if http_conntrack.success else " [red]✗[/red]"
        )
        self._report_progress(
            f"{http_ct_icon} HTTP conntrack acceptance (8080) - Allows redirected HTTP traffic",
            end="\n",
        )

        # Check conntrack rule for port 8443 (HTTPS redirected traffic)
        https_conntrack = ipt.check_accept_redirected_port_tcp_exists(port=8443)
        https_ct_icon = (
            " [green]✔[/green]" if https_conntrack.success else " [red]✗[/red]"
        )
        self._report_progress(
            f"{https_ct_icon} HTTPS conntrack acceptance (8443) - Allows redirected HTTPS traffic",
            end="\n",
        )

    def _verify_firewall_default_policy(self) -> None:
        """Verify INPUT chain default policy is DROP for security."""
        # Check INPUT chain policy by listing the chain status
        policy_cmd = RunnableCommandString(
            command="iptables -L INPUT -n | head -1", sudo=True
        )
        policy_result = self._command_executor.execute(policy_cmd)

        # Check if the output contains "policy DROP"
        policy_is_drop = (
            policy_result.success
            and policy_result.stdout is not None
            and "policy DROP" in policy_result.stdout
        )

        policy_icon = " [green]✔[/green]" if policy_is_drop else " [red]✗[/red]"
        self._report_progress(
            f"{policy_icon} INPUT default policy DROP - Blocks unmatched traffic (security)",
            end="\n",
        )

    def _verify_firewall_configuration(self) -> None:
        """Comprehensive firewall configuration verification."""
        # NAT table REDIRECT rules
        self._report_progress("  📡 NAT Redirects:", end="\n")
        self._verify_firewall_nat_rules()

        # Basic INPUT chain rules
        self._report_progress("  🔗 Connection State:", end="\n")
        self._verify_firewall_input_basic_rules()

        # Service port access
        self._report_progress("  🚪 Service Ports:", end="\n")
        self._verify_firewall_service_ports()

        # Caddy API security
        self._report_progress("  🔒 Caddy API Security:", end="\n")
        self._verify_firewall_caddy_api_security()

        # Conntrack rules for redirected traffic
        self._report_progress("  🎯 Conntrack Rules:", end="\n")
        self._verify_firewall_conntrack_rules()

        # Default policy
        self._report_progress("  🛡️ Default Policy:", end="\n")
        self._verify_firewall_default_policy()

    def verify_server_setup(self) -> None:
        """Verify the EasyRunner server setup.

        This is like an integration test for the server. Therefore we should be very careful when changes to tests here.
        """
        # 🟦 SYSTEM PACKAGES & TOOLS
        self._report_progress("🟦 SYSTEM PACKAGES & TOOLS", end="\n")

        is_podman_installed: bool = self._os_package_manager.is_package_installed(
            package_commands=PodmanCommandsUbuntu()
        )
        podman_icon = " [green]✔[/green]" if is_podman_installed else " [red]✗[/red]"
        self._report_progress(
            f"{podman_icon} Podman - Container runtime engine", end="\n"
        )

        is_git_installed: bool = self._os_package_manager.is_package_installed(
            package_commands=GitCommandsUbuntu(CpuArch.X86_64)
        )
        git_icon = " [green]✔[/green]" if is_git_installed else " [red]✗[/red]"
        self._report_progress(
            f"{git_icon} Git - Version control system for app deployments", end="\n"
        )

        # 👤 USER CONFIGURATION
        self._report_progress("\n👤 USER CONFIGURATION", end="\n")

        user = User(
            executor=self.executor,
            commands=self._user_cmds,
            username=self._easyrunner_username,
        )
        user_exists: bool = user.exists()
        user_icon = " [green]✔[/green]" if user_exists else " [red]✗[/red]"
        self._report_progress(
            f"{user_icon} EasyRunner user exists - System user for EasyRunner operations",
            end="\n",
        )

        user_has_sudo: bool = user.has_sudo_access() if user_exists else False
        sudo_icon = " [green]✔[/green]" if user_has_sudo else " [red]✗[/red]"
        self._report_progress(
            f"{sudo_icon} EasyRunner user sudo access - Required for system management",
            end="\n",
        )

        # Check if linger is enabled
        check_linger_cmd = RunnableCommandString(
            command=f"loginctl show-user {self._easyrunner_username}",
            sudo=True,
        )
        linger_result: ExecResult = self._command_executor.execute(
            command=check_linger_cmd
        )
        linger_enabled: bool = (
            linger_result.success
            and linger_result.stdout is not None
            and "Linger=yes" in linger_result.stdout
        )
        linger_icon = " [green]✔[/green]" if linger_enabled else " [red]✗[/red]"
        self._report_progress(
            f"{linger_icon} User linger enabled - Enables systemd user services to persist",
            end="\n",
        )

        # 📁 DIRECTORY STRUCTURE
        self._report_progress("\n📁 DIRECTORY STRUCTURE", end="\n")

        directories_to_check: List[tuple[str, str]] = [
            (
                f"{self._easyrunner_home_dir}/easyrunner-stack",
                "Main EasyRunner directory",
            ),
            (self._apps_source_dir, "Application source code storage"),
            (self._apps_compose_dir, "Docker compose files for apps"),
            (self._quadlets_config_dir, "Systemd quadlet unit files"),
        ]

        for dir_path, description in directories_to_check:
            directory: Directory = Directory(
                executor=self.executor,
                commands=self._dir_cmds,
                path=dir_path,
            )
            dir_exists: bool = directory.exists()
            dir_icon = " [green]✔[/green]" if dir_exists else " [red]✗[/red]"
            self._report_progress(f"{dir_icon} {dir_path} - {description}", end="\n")

        # 🐳 PODMAN CONFIGURATION
        self._report_progress("\n🐳 PODMAN CONFIGURATION", end="\n")

        # Check if podman sockets are enabled
        systemd_service = SystemdService(
            commands=self._sysetmctl_cmds,
            executor=self._command_executor,
            ServiceName="podman.socket",
            user_mode=True,
            target_username=self._easyrunner_username,
        )
        socket_enabled_result: ExecResult = systemd_service.is_enabled()
        socket_icon = (
            " [green]✔[/green]" if socket_enabled_result.success else " [red]✗[/red]"
        )
        self._report_progress(
            f"{socket_icon} Podman socket enabled - API access for container management",
            end="\n",
        )

        # Check if easyrunner proxy network exists
        easyrunner_proxy_network = PodmanNetwork(
            PodmanCommandsUbuntu(),
            self._command_executor,
            network_name="easyrunner_proxy_network",
        )
        network_exists: bool = easyrunner_proxy_network.network_exists()
        network_icon = " [green]✔[/green]" if network_exists else " [red]✗[/red]"
        self._report_progress(
            f"{network_icon} EasyRunner proxy network - Container networking for reverse proxy",
            end="\n",
        )

        # 🧱 FIREWALL CONFIGURATION
        self._report_progress("\n🧱 FIREWALL CONFIGURATION", end="\n")
        self._verify_firewall_configuration()

        # 🏗️ SYSTEMD SERVICES
        self._report_progress("\n🏗️ SYSTEMD SERVICES", end="\n")

        # Check core EasyRunner systemd services
        services_to_check: List[tuple[str, str]] = [
            ("easyrunner__caddy.service", "Caddy reverse proxy server"),
        ]

        for service_name, description in services_to_check:
            service = SystemdService(
                commands=self._sysetmctl_cmds,
                executor=self._command_executor,
                ServiceName=service_name,
                user_mode=True,
                target_username=self._easyrunner_username,
            )
            service_active: ExecResult = service.is_active()
            service_enabled: ExecResult = service.is_enabled()

            # Use single status based on both active and enabled
            overall_status = service_active.success and service_enabled.success

            enabled_status = "enabled" if service_enabled.success else "disabled"
            active_status = "active" if service_active.success else "inactive"

            service_icon = " [green]✔[/green]" if overall_status else " [red]✗[/red]"
            self._report_progress(
                f"{service_icon} {service_name} ({active_status}, {enabled_status}) - {description}",
                end="\n",
            )

        # Check if proxy network quadlet exists (networks don't have systemd status like containers)
        network_quadlet_file = File(
            executor=self.executor,
            commands=self._file_cmds,
            path=f"{self._quadlets_config_dir}/easyrunner__easyrunner_proxy_network.network",
        )
        network_quadlet_exists: bool = network_quadlet_file.exists()

        # Check if the actual network is running and available to containers
        easyrunner_proxy_network_runtime = PodmanNetwork(
            PodmanCommandsUbuntu(),
            self._command_executor,
            network_name="easyrunner_proxy_network",
        )
        network_runtime_exists: bool = easyrunner_proxy_network_runtime.network_exists()

        # Both quadlet file and runtime network should exist
        network_overall_status = network_quadlet_exists and network_runtime_exists

        config_status = "configured" if network_quadlet_exists else "not configured"
        runtime_status = "running" if network_runtime_exists else "not running"

        network_proxy_icon = (
            " [green]✔[/green]" if network_overall_status else " [red]✗[/red]"
        )
        self._report_progress(
            f"{network_proxy_icon} EasyRunner proxy network ({config_status}, {runtime_status}) - Container network configuration and runtime availability",
            end="\n",
        )

        # 🌐 CADDY WEB SERVER
        self._report_progress("\n🌐 CADDY WEB SERVER", end="\n")

        # Check if Caddy API is responding
        caddy: Caddy = Caddy(
            commands=CaddyCommandsContainerUbuntu(cpu_arch=CpuArch.X86_64),
            executor=self._command_executor,
        )

        try:
            caddy_config_result: ExecResult = caddy.get_config()
            caddy_api_responsive: bool = (
                caddy_config_result.success
                and caddy_config_result.stdout is not None
                and caddy_config_result.stdout.strip() != ""
            )
            caddy_icon = (
                " [green]✔[/green]" if caddy_api_responsive else " [red]✗[/red]"
            )
            self._report_progress(
                f"{caddy_icon} Caddy API responsive - Management interface accessible",
                end="\n",
            )
        except Exception:
            self._report_progress(
                " [red]✗[/red] Caddy API responsive - Management interface not accessible",
                end="\n",
            )

    def remove_easyrunner(self) -> None:
        """Delete EasyRunner stack from the host server."""
        try:
            # we don't remove everything we try to install because something might be a dependency of something else.
            # only add remove logic for things we are absolutely sure about.

            if not self._remove_podman():
                raise RuntimeError("Podman removal failed.")

            logger.debug("Podman removed successfully.")

            # don't remove Git, it could have been pre installed by something else.

        except Exception as e:
            raise RuntimeError(f"Failed to delete EasyRunner stack: {str(e)}")

    def start_application_compose(self, repo_name: str) -> bool:
        """Start the application using Podman compose. This basically runs the docker-compose up command so applying everything in apps the compose file."""
        try:
            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)

            # Start the application using Podman compose
            result = podman.compose_up(
                compose_file=f"{self._apps_compose_dir}/docker-compose-{repo_name}.yaml"
            )

            return result.success

        except Exception as e:
            logger.error("Failed to start the application: %s", str(e))
            raise RuntimeError(f"Failed to start the application: {str(e)}")

    def stop_application_compose(self, repo_name: str) -> bool:
        """Stop the application using Podman compose. This basically runs the docker-compose down command to stop the application and related services as defined in the app compose file."""
        try:
            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)

            # Stop the application using Podman compose
            result = podman.compose_down(
                compose_file=f"{self._apps_compose_dir}/docker-compose-{repo_name}.yaml"
            )

            return result.success

        except Exception as e:
            logger.error("Failed to stop the application: %s", str(e))
            raise RuntimeError(f"Failed to stop the application: {str(e)}")

    def start_application_stack(
        self, compose_project_name: str, app_repo_name: str
    ) -> bool:
        """Start the application container via Systemd using the systemctl command.

        Args:
            compose_project_name: The name of the compose project (usually "easyrunner")
            app_repo_name: The name of the app repository to start

        Returns True if the application stack was started successfully, False otherwise.
        """
        try:
            # Start the EasyRunner stack using systemd
            quadlet_config_dir: Directory = Directory(
                executor=self.executor,
                commands=self._dir_cmds,
                path=self._quadlets_config_dir,
            )

            # Look for files specific to this app: easyrunner__<app_repo_name>.*
            app_pattern = f"{compose_project_name}__{app_repo_name}*.*"
            logger.debug(f"Looking for quadlet files with pattern: {app_pattern}")
            dir_items: List[DirInfo | FileInfo] = cast(
                List[DirInfo | FileInfo],
                quadlet_config_dir.list(filter=app_pattern).result,
            )

            logger.debug(
                f"Found {len(dir_items)} quadlet files: {[item.name for item in dir_items]}"
            )

            for item in dir_items:
                if isinstance(item, FileInfo) and item.extension == "container":
                    logger.debug(f"Starting systemd service for container: {item.name}")
                    app_service = SystemdService(
                        commands=self._sysetmctl_cmds,
                        executor=self._command_executor,
                        ServiceName=f"{item.name}.service",
                        user_mode=True,
                        target_username=self._easyrunner_username,
                    )
                    service_op_result: ExecResult = app_service.start()

                    is_active_result: ExecResult = app_service.is_active()

                    if is_active_result.success:
                        # Service is active, restart it to pick up new image
                        logger.debug(
                            f"Service '{app_service._service_name}' is active, restarting to pick up new version of container"
                        )
                        service_op_result: ExecResult = app_service.restart()
                    else:
                        # Service is not active (stopped or doesn't exist), start it
                        # this has to be 'start' not 'enable' or 'enable_now' which will fail because the unit files are dynamically generated / transient.
                        # They are implicitly enabled by starting them.
                        logger.debug(
                            f"Service '{app_service._service_name}' is not active, starting it"
                        )
                        service_op_result: ExecResult = app_service.start()

                    if service_op_result.success:
                        logger.debug(
                            f"Successfully started container service: {item.name}"
                        )
                    else:
                        logger.error(
                            f"Failed to start container service {item.name}: {service_op_result.stderr}"
                        )
                        return False

            # Check if we found any container files to start
            container_files = [
                item
                for item in dir_items
                if isinstance(item, FileInfo) and item.extension == "container"
            ]
            if not container_files:
                logger.error(
                    f"No container files found with pattern: {compose_project_name}__*.container"
                )
                return False

            logger.debug(
                f"Successfully started {len(container_files)} container services"
            )
            return True

        except Exception as e:
            logger.error("Failed to start the EasyRunner stack: %s", str(e))
            raise RuntimeError(f"Failed to start the EasyRunner stack: {str(e)}")

    def stop_application_stack(self, compose_project_name: str) -> bool:
        """Stop the application container via Systemd using the systemctl command."""

        results = SystemdService(
            commands=self._sysetmctl_cmds,
            executor=self._command_executor,
            ServiceName=f"{compose_project_name}/*.service",
            user_mode=True,
            target_username=self._easyrunner_username,
        ).disable()
        return results.success

    def start_easyrunner_stack(self) -> bool:
        """Start the EasyRunner stack using Podman compose.

        Enables easyrunner services, networks, and volumes.
        """
        try:
            # Start the EasyRunner stack using systemd
            quadlet_config_dir: Directory = Directory(
                executor=self.executor,
                commands=self._dir_cmds,
                path=self._quadlets_config_dir,
            )

            dir_items: List[DirInfo | FileInfo] = cast(
                List[DirInfo | FileInfo],
                quadlet_config_dir.list(filter="easyrunner__*.*").result,
            )

            for item in dir_items:
                if isinstance(item, FileInfo) and item.extension == "container":
                    service_name = f"{item.name}.service"

                    # Use SystemdService with target_username for proper environment setup
                    systemd_service = SystemdService(
                        commands=self._sysetmctl_cmds,
                        executor=self._command_executor,
                        ServiceName=service_name,
                        user_mode=True,
                        target_username=self._easyrunner_username,
                    )
                    self._report_progress(
                        f" [yellow](Re)starting service: '{service_name}'...[/yellow]",
                        end="",
                    )
                    container_result: ExecResult = systemd_service.restart()

                    if container_result.success:
                        logger.debug(f"Successfully restarted service {service_name}")
                        self._report_progress(" [green]✔[/green]", end="\n")
                    else:
                        self._report_progress(" [red]✗[/red]", end="\n")
                        self._report_progress(
                            f" [red]Error msg[/red]: {container_result.stderr}. {container_result.stdout}",
                            end="\n",
                        )
                        self._report_progress(
                            f" [red]Error code[/red]: {container_result.return_code}",
                            end="\n",
                        )

                        logger.error(
                            f"Failed to restart service {service_name}: {container_result.stderr}"
                        )
                        # Get status for debugging
                        status_result: ExecResult = systemd_service.status()
                        logger.error(f"Service status: {status_result.stderr}")
                    # Check status regardless of restart result
                    systemd_service.status()

            return True

        except Exception as e:
            logger.error("Failed to start the EasyRunner stack: %s", str(e))
            raise RuntimeError(f"Failed to start the EasyRunner stack: {str(e)}")

    def stop_easyrunner_stack(self) -> bool:
        """Stop the EasyRunner stack using Podman compose.

        Disables just easyrunner services, not networks and volumes.
        """
        try:
            # podman = Podman(PodmanCommandsUbuntu(), self._command_executor)

            # Stop the EasyRunner stack using Podman compose
            # result = podman.compose_down(
            #     compose_file=self._easyrunner_stack_compose_file
            # )
            # Stop the EasyRunner stack using systemd
            result: ExecResult = SystemdService(
                commands=self._sysetmctl_cmds,
                executor=self._command_executor,
                ServiceName="easyrunner/*.service",
                user_mode=True,
                target_username=self._easyrunner_username,
            ).disable()

            return result.success

        except Exception as e:
            logger.error("Failed to stop the EasyRunner stack: %s", str(e))
            raise RuntimeError(f"Failed to stop the EasyRunner stack: {str(e)}")

    def deploy_app_flow_a(
        self: Self,
        repo_url: str,
        custom_app_domain_name: str,
        github_access_token: str,
    ) -> None:
        """Deploy application using flow A. See docs for details on flow A.

        <repo name>.a.easyrunner.xyz will always added and resolve where ever the ER CLI is running.

        Args:
            repo_url (str): The URL of the application repository to deploy. Must be SSH format (git@github.com:owner/repo.git).
            custom_app_domain_name (Optional[str]): a custom domain name for the application. Example "mygrandproduct.com" or "api.mygrandproduct.com".
            github_access_token (Optional[str]): GitHub access token for automatic deploy key management. If None, manual deploy key setup may be required.
        """
        try:
            logger.debug(f"Deploying application from repository: {repo_url}")

            # Validate that we're using SSH URL format (required for deploy key authentication)
            if not repo_url.startswith("git@github.com:"):
                error_msg = (
                    "\n"
                    "❌ Only SSH repository URLs are supported for deployment.\n\n"
                    f"URL provided: {repo_url}\n\n"
                    "Why SSH only?\n"
                    "  • EasyRunner uses deploy keys for secure, repository-specific access\n"
                    "  • Deploy keys only work with SSH URLs, not HTTPS\n"
                    "  • This ensures each app has its own isolated authentication\n\n"
                    "To get the SSH URL:\n"
                    "  1. Go to your repository on GitHub\n"
                    "  2. Click the green 'Code' button\n"
                    "  3. Select the 'SSH' tab\n"
                    "  4. Copy the URL (it starts with git@github.com:)\n\n"
                    "To update your app's repository URL, run:\n"
                    "  er app update <app-name> --repo-url <SSH-URL-you-copied>\n"
                )
                self._report_progress(error_msg)
                return

            # 1. clone repo to /home/easyrunner/easyrunner-stack/apps-source
            app_repo: GitRepo = GitRepo(
                commands=GitCommandsUbuntu(CpuArch.X86_64),
                executor=self._command_executor,
                util_commands=self._uc,
                repo_remote_url=repo_url,
                branch_name="main",
                repo_local_base_dir=self._apps_source_dir,
            )

            # ensure github deploy key is set up
            if not self._ensure_github_repo_deploy_key_configured(
                repo_owner=app_repo.repo_owner,
                repo_name=app_repo.repo_name,
                github_access_token=github_access_token,
            ):
                self._report_progress(" [red]✗[/red]", end="\n")
                return

            ssh_agent = self.get_ssh_agent()

            # set need to pass the ssh agent env vars to the git repo.
            # because these commands run in a different session therefore not have access to the ssh-agent env vars
            app_repo.ssh_agent_env_vars = ssh_agent.get_setup_env_vars()

            if app_repo.is_cloned():
                logger.debug(
                    "Application repository already cloned. Checking if re-clone is needed..."
                )

                # Check if the existing repo was cloned with HTTPS URL (incompatible with deploy keys)
                # We do this by checking the remote URL
                remote_url_result = app_repo.get_remote_url(remote_name="origin")

                if remote_url_result.success and remote_url_result.result is not None:
                    existing_remote_url = remote_url_result.result
                    logger.debug(f"Existing remote URL: {existing_remote_url}")

                    # If existing repo uses HTTPS, delete it and re-clone with SSH
                    if GitRepo.is_url_https_format(existing_remote_url):
                        logger.debug(
                            "Existing repo was cloned with HTTPS URL. Deleting and re-cloning with SSH..."
                        )
                        self._report_progress(
                            " [yellow]Existing repo uses HTTPS, re-cloning with SSH...[/yellow]",
                            end="",
                        )

                        repo_dir = Directory(
                            executor=self._command_executor,
                            commands=self._dir_cmds,
                            path=app_repo.full_repo_path,
                        )
                        remove_result = repo_dir.remove()
                        if not remove_result.success:
                            raise RuntimeError(
                                f"Failed to remove existing HTTPS repo at {repo_dir.path}. Error: {remove_result.stderr}"
                            )

                        # Clone with SSH URL
                        clone_result = app_repo.clone(branch_name="main")
                        if not clone_result.success:
                            self._report_progress(" [red]x[/red]", end="\n")
                            raise RuntimeError(
                                f"Failed to clone application repository: {app_repo.repo_name}. Error: {clone_result.stderr}"
                            )
                        self._report_progress(" [green]✔[/green]", end="\n")
                    else:
                        # Remote URL is SSH, just pull latest changes
                        logger.debug("Remote URL is SSH, pulling latest changes...")
                        self._report_progress(
                            " [yellow]Pulling latest changes...[/yellow]", end=""
                        )
                        pull_result = app_repo.pull()
                        if not pull_result.success:
                            self._report_progress(" [red]x[/red]", end="\n")
                            raise RuntimeError(
                                f"Failed to pull latest changes for application: {app_repo.repo_name}. Error: {pull_result.stderr}"
                            )
                        self._report_progress(" [green]✔[/green]", end="\n")
                else:
                    # Could not check remote URL, assume it needs re-clone
                    logger.debug("Could not check remote URL, proceeding with pull...")
                    self._report_progress(
                        " [yellow]Pulling latest changes...[/yellow]", end=""
                    )
                    pull_result = app_repo.pull()
                    if not pull_result.success:
                        self._report_progress(" [red]x[/red]", end="\n")
                        raise RuntimeError(
                            f"Failed to pull latest changes for application: {app_repo.repo_name}. Error: {pull_result.stderr}"
                        )
                    self._report_progress(" [green]✔[/green]", end="\n")
            else:
                # check of the folder exists, even if not cloned. it's possible
                repo_dir = Directory(
                    executor=self._command_executor,
                    commands=self._dir_cmds,
                    path=app_repo.full_repo_path,
                )
                if repo_dir.exists():
                    remove_result = repo_dir.remove()
                    logger.debug(
                        f"Removing existing repo directory: {repo_dir.path}, because it's not a git repository."
                    )
                    if not remove_result.success:
                        raise RuntimeError(
                            "Removing the repo directory, that wasn't a valid git repository, failed."
                        )

                logger.debug(f"Cloning application repository {app_repo.repo_name}...")
                self._report_progress(" [yellow]Cloning repository...[/yellow]", end="")
                # TODO: make the branch configurable by the user.
                # TODO: support monorepos. make repo sub folder configurable by the user
                clone_result = app_repo.clone(branch_name="main")
                if not clone_result.success:
                    self._report_progress(" [red]x[/red]", end="\n")
                    raise RuntimeError(
                        f"Failed to clone application repository: {app_repo.repo_name}. Error: {clone_result.stderr}"
                    )
                self._report_progress(" [green]✔[/green]", end="\n")

            # 2. build container
            self._report_progress(" [yellow]Building container...[/yellow]", end="")
            if not self._build_container(app_repo):
                self._report_progress(" [red]x[/red]", end="\n")
                logger.debug(
                    f"Failed to build container for application: {app_repo.repo_name}"
                )
                raise RuntimeError(
                    f"Application '{app_repo.repo_name}' container build failed"
                )
            self._report_progress(" [green]✔[/green]", end="\n")
            # 3. copy app compose file from repo to ~/easyrunner-stack/infra/docker-compose
            # TODO: only copy if it has changed

            self._report_progress(
                " [yellow]Setting up app configuration as system services...[/yellow]",
                end="",
            )
            self._copy_app_compose_file(app_repo.repo_name)

            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)

            app_compose_file_path = os.path.join(
                self._apps_compose_dir,
                self._build_app_compose_file_name(repo_name=app_repo.repo_name),
            )

            compose_project = podman.load_compose_file(
                compose_file_path=app_compose_file_path
            )

            self._convert_compose_file_to_quadlets(
                compose_project=compose_project, ignore_ports=True
            )
            self._report_progress(" [green]✔[/green]", end="\n")
            # 5. reload systemd config
            # TODO: check if this is reloading the entire Caddy config or just the app specific.
            # ideally we want to guarantee no downtime/change to other apps
            self._report_progress(
                " [yellow]Systemd daemon reloading...[/yellow]", end=""
            )
            # Required for both first deploy and updates to regenerate systemd units from new quadlet files; user-scoped reload doesn't affect other services or cause downtime.
            SystemdService(
                executor=self._command_executor,
                commands=self._sysetmctl_cmds,
                ServiceName="",
                user_mode=True,
                target_username=self._easyrunner_username,
            ).daemon_reload()
            self._report_progress(" [green]✔[/green]", end="\n")

            # 5. start the application stack
            logger.debug(f"Starting application stack for: {app_repo.repo_name}...")
            self._report_progress(" [yellow]Starting app stack...[/yellow]", end="")
            # restarts all the services defined in compose project for this application.
            # TODO: when we add monorepo support the app _restart_ logic on redeploys should me smarter and only restart the service(s) that changed.
            if not self.start_application_stack(
                compose_project_name=compose_project.name,
                app_repo_name=app_repo.repo_name,
            ):
                logger.debug(
                    f"Failed to start application stack for: {app_repo.repo_name}"
                )
                raise RuntimeError(
                    f"Application '{app_repo.repo_name}' stack start failed"
                )
            self._report_progress(" [green]✔[/green]", end="\n")
            # 6. add or modify the site config in Caddy
            self._report_progress(
                " [yellow]Configuring reverse proxy...[/yellow]", end=""
            )

            services_on_public_network = [
                svc
                for svc in compose_project.services.values()
                if "easyrunner_proxy_network" in svc.networks
            ]

            services_on_public_network_and_public_label = [
                svc
                for svc in services_on_public_network
                if svc.labels.get("xyz.easyrunner.appIsPublic", False) is True
            ]

            # TODO: for now we only support one public service in a compose file
            if len(services_on_public_network_and_public_label) > 0:
                public_service = services_on_public_network_and_public_label[0]

            elif len(services_on_public_network) > 0:
                public_service = services_on_public_network[0]

            else:
                raise RuntimeError(
                    "No services found on the public network 'easyrunner_proxy_network'."
                )

            app_framework = public_service.labels.get("xyz.easyrunner.appFramework")

            backend_service_hostname = compose_project.systemd_container_name(
                public_service
            )

            caddy: Caddy = Caddy(
                CaddyCommandsContainerUbuntu(cpu_arch=CpuArch.X86_64),
                self._command_executor,
            )

            hostnames: JsonArray = []

            if custom_app_domain_name is not None:
                # add custom domain name to the hostnames list
                hostnames.append(custom_app_domain_name)
            else:
                raise

            # Extract container port from label, fallback to port mapping, then default to 3000
            container_port_value = public_service.labels.get("xyz.easyrunner.appContainerInternalPort")
            if container_port_value is not None:
                container_port = str(container_port_value)
            else:
                container_port = "3000"  # Default port

            if app_framework == "nextjs":
                site_config: JsonObject = self._build_nextjs_site_config(
                    hostnames=hostnames,
                    backend_service_hostname=backend_service_hostname,
                    container_port=container_port,
                )
            else:
                site_config: JsonObject = self._build_standard_web_site_config(
                    hostnames=hostnames,
                    backend_service_hostname=backend_service_hostname,
                    container_port=container_port,
                )

            # create Caddy server config block if it doesn't exist
            server_config_result = caddy.server_exists(server_name="svr0")
            logger.debug(f"Caddy server config exists: {server_config_result}")
            if not server_config_result:
                logger.debug(
                    "Server config for 'svr0' does not exist therefore adding."
                )
                caddy.add_server_config(
                    server_name="svr0", config=self._build_server_config()
                )

            # Check if site config exists
            if not caddy.site_exists(
                server_name="svr0", hostname=custom_app_domain_name
            ):
                logger.debug(
                    f"Site config route with hostname '{custom_app_domain_name}' does not exist therefore adding "
                )
                # Site config does not exist, we create a new one
                config_merge_result = caddy.add_site_config(
                    server_name="svr0",
                    hostname=custom_app_domain_name,
                    site_config=site_config,
                )
            else:
                # Site config exists, we can merge the new config
                logger.debug(
                    f"Site config route with hostname '{custom_app_domain_name}' exists therefore merging any changes into the existing config."
                )
                config_merge_result = caddy.merge_into_server_site_config(
                    server_name="svr0",
                    hostname=custom_app_domain_name,
                    config=site_config,
                )

                if not config_merge_result.success:
                    self._report_progress(" [red]x[/red]", end="\n")
                    raise RuntimeError(
                        f"Failed to merge site config for application: {app_repo.repo_name}. Error: {config_merge_result.stderr}"
                    )
                self._report_progress(" [green]✔[/green]", end="\n")

            caddy.get_config()  # for debugging purposes

            # Log deployment success with accessible URLs
            server_ip = self.executor.ssh_client.hostname

            # Construct URLs based on the Caddy configuration
            urls = []

            # Add HTTPS URLs for configured hostnames
            if hostnames:
                for hostname in hostnames:
                    urls.append(f"https://{hostname}")

            # Add fallback IP-based URL (since we're listening on :443)
            urls.append(f"https://{server_ip}")

            if urls:
                urls_str = ", ".join(urls)
                self._report_progress(
                    f"\n🎉 Application '{app_repo.repo_name}' deployed successfully!\n Access it at: {urls_str}",
                    end="\n\n",
                )
            else:
                self._report_progress(
                    f"\n🎉 Application '{app_repo.repo_name}' deployed successfully!\n Access it at https://{server_ip}",
                    end="\n\n",
                )

        except Exception as e:
            raise RuntimeError(f"Failed to deploy application using flow A: {str(e)}")

    @staticmethod
    def _build_server_config():
        server_config: JsonObject = {
            "listen": [":443"],
            "routes": [],
        }
        return server_config

    @staticmethod
    def _build_standard_web_site_config(
        hostnames: JsonArray,
        backend_service_hostname: str,
        container_port: str,
    ) -> JsonObject:
        return {
            "match": [{"host": hostnames}],
            "handle": [
                {
                    "handler": "reverse_proxy",
                    "upstreams": [
                        {"dial": f"{backend_service_hostname}:{container_port}"}
                    ],
                    "headers": {
                        "request": {
                            "set": {
                                "X-Forwarded-Proto": ["{http.request.scheme}"],
                                "X-Forwarded-Host": ["{http.request.host}"],
                                "X-Real-IP": ["{http.request.remote_host}"],
                            }
                        }
                    },
                }
            ],
        }

    @staticmethod
    def _build_nextjs_site_config(
        hostnames: JsonArray,
        backend_service_hostname: str,
        container_port: str,
    ) -> JsonObject:
        site_config: JsonObject = {
            "match": [{"host": hostnames}],
            "handle": [
                {
                    "handler": "subroute",
                    "routes": [
                        {
                            "match": [{"path": ["/_next/static/*"]}],
                            "handle": [
                                {
                                    "handler": "headers",
                                    "response": {
                                        "set": {
                                            "Cache-Control": [
                                                "public, max-age=31536000, immutable"
                                            ]
                                        }
                                    },
                                },
                                {
                                    "handler": "reverse_proxy",
                                    "upstreams": [
                                        {
                                            "dial": f"{backend_service_hostname}:{container_port}"
                                        }
                                    ],
                                },
                            ],
                        },
                        {
                            "match": [
                                {
                                    "path": [
                                        "/*.svg",
                                        "/*.ico",
                                        "/*.png",
                                        "/*.jpg",
                                        "/*.jpeg",
                                        "/*.gif",
                                        "/*.webp",
                                        "/*.woff",
                                        "/*.woff2",
                                        "/*.ttf",
                                        "/*.eot",
                                    ]
                                }
                            ],
                            "handle": [
                                {
                                    "handler": "headers",
                                    "response": {
                                        "set": {
                                            "Cache-Control": ["public, max-age=86400"]
                                        }
                                    },
                                },
                                {
                                    "handler": "reverse_proxy",
                                    "upstreams": [
                                        {
                                            "dial": f"{backend_service_hostname}:{container_port}"
                                        }
                                    ],
                                },
                            ],
                        },
                        {
                            "match": [{"path": ["/api/*"]}],
                            "handle": [
                                {
                                    "handler": "headers",
                                    "response": {
                                        "set": {
                                            "Cache-Control": [
                                                "no-cache, no-store, must-revalidate"
                                            ]
                                        }
                                    },
                                },
                                {
                                    "handler": "reverse_proxy",
                                    "upstreams": [
                                        {
                                            "dial": f"{backend_service_hostname}:{container_port}"
                                        }
                                    ],
                                },
                            ],
                        },
                        {
                            "handle": [
                                {
                                    "handler": "reverse_proxy",
                                    "upstreams": [
                                        {
                                            "dial": f"{backend_service_hostname}:{container_port}"
                                        }
                                    ],
                                    "headers": {
                                        "request": {
                                            "set": {
                                                "X-Forwarded-Proto": [
                                                    "{http.request.scheme}"
                                                ],
                                                "X-Forwarded-Host": [
                                                    "{http.request.host}"
                                                ],
                                                "X-Real-IP": [
                                                    "{http.request.remote_host}"
                                                ],
                                            }
                                        }
                                    },
                                }
                            ]
                        },
                    ],
                }
            ],
        }

        return site_config

    def _install_podman(self: Self) -> ExecResult:
        """Install Podman if not already installed."""
        # TODO: capture already installed vs newly installed and version in `result`
        exec_result: ExecResult = ExecResult()

        def _internal_install_podman(self: Self) -> ExecResult:
            _exec_result = self._os_package_manager.install_package(
                PodmanCommandsUbuntu().pkg_name
            )
            _exec_result.success = (
                _exec_result.return_code == 0
                and self._os_package_manager.is_package_installed(
                    package_commands=PodmanCommandsUbuntu()
                )
            )
            return _exec_result

        if self._os_package_manager.is_package_installed(
            package_commands=PodmanCommandsUbuntu()
        ):
            exec_result.success = True
        else:
            try:
                exec_result = _internal_install_podman(self)

                if "dpkg was interrupted, you must manually run" in str(
                    exec_result.stderr
                ) or (not exec_result.success and exec_result.stderr is not None):
                    logger.debug(
                        "Error: %s. Trying self heal: attempting to fix package state.",
                        str(exec_result.stderr),
                    )
                    self._os_package_manager.fix_dpkg()

                    logger.debug(
                        "dpkg fix seems successful. Retrying podman installation."
                    )
                    exec_result = _internal_install_podman(self)

                    if not exec_result.success:
                        logger.debug(
                            "Fixing package state didn't resolve the Podman installation issue. Trying self heal: try --reinstall option. Error: %s",
                            exec_result.stderr,
                        )
                        exec_result = self._os_package_manager.reinstall_package(
                            package_name=PodmanCommandsUbuntu().pkg_name
                        )
                        if not exec_result.success:
                            logger.error(
                                "Reinstalling Podman didn't work either. %s",
                                str(exec_result),
                            )
                            raise RuntimeError(
                                "Podman install failed despite running self-healing."
                            )
                if self._os_package_manager.is_package_installed(
                    package_commands=PodmanCommandsUbuntu()
                ):
                    exec_result.success = True
            except Exception as e:
                raise e

        return exec_result

    def _remove_podman(self: Self) -> bool:
        """Remove Podman."""
        success: bool = False

        def _internal_remove_podman(self: Self) -> ExecResult:
            _exec_result: ExecResult = self._os_package_manager.remove_package(
                PodmanCommandsUbuntu().pkg_name
            )

            _exec_result.success = (
                _exec_result.return_code == 0
                and not self._os_package_manager.is_package_installed(
                    package_commands=PodmanCommandsUbuntu()
                )
            )

            return _exec_result

        if self._os_package_manager.is_package_installed(
            package_commands=PodmanCommandsUbuntu()
        ):
            try:
                logger.debug("Podman is installed. Removing.")
                exec_result: ExecResult = _internal_remove_podman(self)

                success = exec_result.success
                logger.debug("Podman remove result: %s", str(exec_result))

                if "dpkg was interrupted, you must manually run" in str(
                    exec_result.stderr
                ):
                    try:
                        logger.debug(
                            "Error: %s. Auto running dpkg fix.", str(exec_result.stderr)
                        )

                        self._os_package_manager.fix_dpkg()

                        logger.debug(
                            "dpkg fix seems successful. Retrying podman removal."
                        )
                        exec_result = _internal_remove_podman(self)
                        success = exec_result.success
                    except Exception as fix_e:
                        logger.error("Failed to fix dpkg: {0}", str(fix_e))
                        raise RuntimeError(
                            "Podman remove failed due to a dpkg issue. dpkg fix attempt also failed. Original error: %s",
                            str(fix_e),
                        )
            except Exception as e:
                raise e

        else:
            logger.debug("Podman is not installed. Skipping removal.")
            if not self.silent:
                print("Podman is not installed. Skipping removal.")

            success = True

        return success

    def _install_git(self) -> bool:
        """Install Git if not already installed."""
        # TODO: change the return type to ExecResult and capture already installed vs newly installed and version in `result`
        success: bool = False

        if self._os_package_manager.is_package_installed(
            package_commands=GitCommandsUbuntu(CpuArch.X86_64)
        ):
            success = True

        else:
            exec_result: ExecResult = self._os_package_manager.install_package(
                GitCommandsUbuntu(CpuArch.X86_64).pkg_name
            )
            success = (
                exec_result.return_code == 0
                and self._os_package_manager.is_package_installed(
                    package_commands=GitCommandsUbuntu(CpuArch.X86_64)
                )
            )

        return success

    def _remove_git(self) -> bool:
        """Remove Git."""
        success: bool = False
        if self._os_package_manager.is_package_installed(
            package_commands=GitCommandsUbuntu(CpuArch.X86_64)
        ):
            removeResult: ExecResult = self._os_package_manager.remove_package(
                GitCommandsUbuntu(CpuArch.X86_64).pkg_name
            )
            success = (
                removeResult.return_code == 0
                and not self._os_package_manager.is_package_installed(
                    package_commands=GitCommandsUbuntu(CpuArch.X86_64)
                )
            )

        return success

    def _put_config_files_on_host(self) -> None:
        """Copy configuration template files to the remote host.
        Uses the pre-built archive from the package to transfer template files to /etc/easyrunner on the remote host.
        """
        try:
            # Get the package's template archive path
            import importlib.resources

            archive_path: Traversable = (
                importlib.resources.files("easyrunner.source.artefacts")
                / self._server_config_archive_filename
            )
            # print(f"archive path: {str(archive_path)}")
            if not archive_path.is_file():
                raise RuntimeError(
                    f"Server config archive '{archive_path}' not found in package. This is generated during package build."
                )

            # Create the target directory for infra config on remote host
            # mkdir_cmd: RunnableCommandString = self._uc.mkdir(
            #     directory=self._infra_config_dir
            # )
            # self._command_executor.execute(command=mkdir_cmd)
            # infra_config_dir: Directory = Directory(
            #     executor=self.executor,
            #     commands=self._dir_cmds,
            #     path=f"{self._easyrunner_home_dir}/easyrunner-stack",
            # )
            infra_config_dir: Directory = Directory(
                executor=self.executor,
                commands=self._dir_cmds,
                path=self._infra_config_dir,
            )
            if not infra_config_dir.exists():
                infra_config_dir.create(
                    owner=self._easyrunner_username,
                    group=self._easyrunner_username,
                    mode="750",
                )
                # infra_config_dir.set_owner(
                #     owner_group=self._easyrunner_username,
                #     owner_user=self._easyrunner_username,
                # )

            # # Change ownership of the directory to the SSH user
            # whoami_cmd = RunnableCommandString(command="whoami")
            # username_result = self._command_executor.execute(command=whoami_cmd)
            # ssh_username = username_result.stdout.strip() if username_result.stdout else ""

            # chown_cmd = RunnableCommandString(
            #     command=f"chown {ssh_username}:{ssh_username} /etc/easyrunner",
            #     sudo=True
            # )
            # self._command_executor.execute(command=chown_cmd)

            # if not self._uc.dir_exists(self._infra_config_dir):
            #     raise RuntimeError(
            #         f"Failed to create {self._infra_config_dir} directory on host."
            #     )

            # Copy the archive to remote host
            self._command_executor.put_file(
                source=str(archive_path),
                remote_path=f"{self._easyrunner_home_dir}/easyrunner-stack/{self._server_config_archive_filename}",
            )

            # Extract on remote host
            extract_cmd = self._archive_commands.extract(
                archive_name=f"{self._easyrunner_home_dir}/easyrunner-stack/{self._server_config_archive_filename}",
                target_dir=f"{self._easyrunner_home_dir}/easyrunner-stack",
            )
            self._command_executor.execute(extract_cmd)

            # set the ownership to easyrunner recursively AFTER extraction to make sure folders created from the archive are owned by easyrunner
            infra_config_dir.set_owner(
                owner_user=self._easyrunner_username,
                owner_group=self._easyrunner_username,
                recursive=True,
            )

            # Clean up the archive files
            # TODO: replace with command generator func
            cleanup_cmd = RunnableCommandString(
                command=f"rm -f {self._easyrunner_home_dir}/easyrunner-stack/{self._server_config_archive_filename}"
            )
            self._command_executor.execute(cleanup_cmd)

        except Exception as e:
            logger.error("Failed to transfer config files to host: %s", str(e))
            raise RuntimeError(f"Failed to transfer config files to host: {str(e)}")

    def _build_app_compose_file_name(self, repo_name: str) -> str:
        """Build the application compose file name based on the repo name."""
        return f"docker-compose-{repo_name}.yaml"

    def _copy_app_compose_file(self, repo_name: str) -> None:
        """Copy the application compose file from the repo to the remote host."""
        try:
            # Check if the application compose directory exists
            if not self._dir_cmds.dir_exists(self._apps_compose_dir):
                raise RuntimeError(
                    f"Application compose directory '{self._apps_compose_dir}' does not exist on the remote host."
                )

            # Copy the application compose file from the app repo to the server infra docker-compose directory
            source_compose_file_path = os.path.join(
                self._apps_source_dir,
                repo_name,
                ".easyrunner",
                "docker-compose-app.yaml",
            )

            dest_compose_file_path = os.path.join(
                self._apps_compose_dir, self._build_app_compose_file_name(repo_name)
            )

            app_compose_file: File = File(
                executor=self.executor,
                commands=self._file_cmds,
                path=source_compose_file_path,
            )

            # app_compose_file.set_owner(
            #     owner_group=self._easyrunner_username,
            #     owner_user=self._easyrunner_username,
            # )

            if app_compose_file.copy(
                destination=dest_compose_file_path,
                owner=self._easyrunner_username,
                group=self._easyrunner_username,
                mode="644",
            ):
                logger.debug(
                    "Successfully copied application compose file to host: %s",
                    dest_compose_file_path,
                )
            else:
                raise RuntimeError(
                    f"Failed to copy application compose file from {source_compose_file_path} to {dest_compose_file_path}"
                )

        except Exception as e:
            raise RuntimeError(f"Failed to copy app compose file to host: {str(e)}")

    def _build_container(self, repo: GitRepo, no_cache: bool = False) -> bool:
        """Build the container for the application."""
        try:
            # Check if the application compose directory exists
            if not self._dir_cmds.dir_exists(self._apps_compose_dir):
                raise RuntimeError(
                    f"Application compose directory '{self._apps_compose_dir}' does not exist on the remote host."
                )

            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)

            # prepare tags for the container
            tags: list[str] = [
                f"{repo.repo_name}:latest",
                f"{repo.repo_name}:{repo.latest_commit_hash()}",
            ]

            # Build the container using Podman
            build_result = podman.build(
                context=repo.full_repo_path,
                tags=tags,
                no_cache=no_cache,
            )

            return build_result.success

        except Exception as e:
            logger.error("Failed to build the container: %s", str(e))
            raise RuntimeError(f"Failed to build the container: {str(e)}")

    def _enable_linger(self) -> bool:
        """Enable linger for the EasyRunner service account on the server.

        Also ensures proper systemd user session environment setup.
        """
        try:
            # Enable lingering for the user - this always requires root privileges
            enable_linger_cmd = RunnableCommandString(
                command=f"loginctl enable-linger {self._easyrunner_username}",
                sudo=True,  # loginctl always requires root privileges
            )
            result: ExecResult = self._command_executor.execute(
                command=enable_linger_cmd
            )

            if not result.success:
                logger.error(
                    f"Failed to enable lingering for user {self._easyrunner_username}: {result.stderr}"
                )
                return False

            logger.debug(
                f"Successfully enabled lingering for user {self._easyrunner_username}."
            )

            # Verify the user exists and get their home directory
            easyrunner_user = User(
                executor=self.executor,
                commands=self._user_cmds,
                username=self._easyrunner_username,
            )

            if not easyrunner_user.exists():
                logger.error(
                    f"User {self._easyrunner_username} does not exist or is not accessible"
                )
                return False

            logger.debug(f"User '{self._easyrunner_username}' exists")

            # Get user's home directory for proper session setup
            home_dir_result = easyrunner_user.get_home_directory()

            if not home_dir_result.success or not home_dir_result.result:
                logger.error(
                    f"Failed to get home directory for user {self._easyrunner_username}"
                )
                return False

            user_home: str = home_dir_result.result
            logger.debug(
                f"Home directory for user {self._easyrunner_username}: {user_home}"
            )

            # Initialize systemd user session environment
            # First try to create the runtime directory and start the session
            create_runtime_cmd = RunnableCommandString(
                command=f"sudo -u {self._easyrunner_username} XDG_RUNTIME_DIR=/run/user/1000 systemd-run --user --scope true",
                sudo=True,
            )
            session_result: ExecResult = self._command_executor.execute(
                command=create_runtime_cmd
            )

            if session_result.success:
                logger.debug(
                    f"Successfully started systemd user session for {self._easyrunner_username}"
                )
            else:
                logger.warning(
                    f"Failed to start user session with systemd-run: {session_result.stderr}"
                )
                # Try alternative approach - directly create the runtime dir and start session
                runtime_dir = Directory(
                    executor=self.executor,
                    commands=self._dir_cmds,
                    path="/run/user/1000",
                )

                if not runtime_dir.exists():
                    dir_creation_result = runtime_dir.create(
                        owner=self._easyrunner_username,
                        group=self._easyrunner_username,
                        mode="700",  # User only access for runtime directory
                    )
                    if not dir_creation_result.success:
                        logger.error(
                            f"Failed to create runtime directory: {dir_creation_result.stderr}"
                        )
                        return False
                    logger.debug("Created runtime directory using Directory resource")
                else:
                    # Directory exists, ensure correct ownership
                    ownership_result = runtime_dir.set_owner(
                        owner_user=self._easyrunner_username,
                        owner_group=self._easyrunner_username,
                    )
                    if not ownership_result.success:
                        logger.warning(
                            f"Failed to set runtime directory ownership: {ownership_result.stderr}"
                        )

                # Try to start user manager with proper environment using SystemdService
                systemd_service = SystemdService(
                    commands=self._sysetmctl_cmds,
                    executor=self._command_executor,
                    ServiceName="",  # not applicable for daemon-reload
                    user_mode=True,
                    target_username=self._easyrunner_username,
                )
                manager_result: ExecResult = systemd_service.daemon_reload()

                if not manager_result.success:
                    logger.error(
                        f"Failed to start systemd user manager: {manager_result.stderr}"
                    )
                    return False

            # Verify systemd user session is working by checking if we can list units
            # Note: list-units is not available in SystemdService, so we keep the manual command for now
            verify_cmd = RunnableCommandString(
                command=f"sudo -u {self._easyrunner_username} XDG_RUNTIME_DIR=/run/user/1000 systemctl --user list-units --type=service",
                sudo=True,
            )
            verify_result: ExecResult = self._command_executor.execute(
                command=verify_cmd
            )

            if verify_result.success:
                logger.debug(
                    f"systemd user session is working properly for {self._easyrunner_username}"
                )
                return True
            else:
                logger.error(
                    f"systemd user session verification failed: {verify_result.stderr}"
                )
                return False

        except Exception as e:
            logger.error(f"An error occurred while enabling lingering: {str(e)}")
            return False

    def _create_proxy_network_quadlet(self) -> None:
        """Create the easyrunner proxy network quadlet file."""
        import io

        # Create network quadlet content
        network_quadlet_content = """[Unit]
Description=EasyRunner proxy network

[Network]
Driver=bridge

[Install]
WantedBy=default.target
"""

        # Write the network quadlet file
        quadlets_config_dir = Directory(
            executor=self.executor,
            commands=self._dir_cmds,
            path=self._quadlets_config_dir,
        )

        remote_network_quadlet_path = (
            f"{quadlets_config_dir.path}/easyrunner__easyrunner_proxy_network.network"
        )

        network_file_obj = io.BytesIO(
            initial_bytes=network_quadlet_content.encode(encoding="utf-8")
        )
        network_file_obj.seek(0)

        # Upload the network quadlet file to the remote host
        put_result: ExecResult = self._command_executor.put_file(
            source=network_file_obj,
            remote_path=remote_network_quadlet_path,
        )

        if not put_result.success:
            raise RuntimeError(f"Failed to create network quadlet: {put_result.stderr}")

    def _convert_compose_file_to_quadlets(
        self, compose_project: ComposeProject, ignore_ports: bool = False
    ) -> None:
        """Convert the docker compose file to Podman quadlet files and upload them to the remote host.

        Once the quadlet files are generated and uploaded by running this method, call systemd.daemon_reload() to trigger systemd unit file creation.

        Args:
            compose_project: The ComposeProject instance to convert to quadlet files.
            ignore_ports: If True, skip processing 'ports:' sections (for reverse-proxy-first apps)
        """
        # systemd_unit_files_path: str = (
        #     f"{self._systemd_config_dir}/{compose_project_name}"
        # )

        # compose_file = File(
        #     commands=self._file_cmds,
        #     executor=self.executor,
        #     path=compose_file_path,
        # )
        # compose_file_read_result: ExecResult = compose_file.open_read()

        # if compose_file_read_result.stdout is not None:

        #     compose_project = ComposeProject.from_compose_yaml(
        #         compose_yaml=compose_file_read_result.stdout
        #     )

        quadlets_results: dict[str, str] = Podman.compose_to_quadlet(
            compose_project=compose_project, ignore_ports=ignore_ports
        )

        quadlets_config_dir = Directory(
            commands=DirCommandsUbuntu(cpu_arch=CpuArch.X86_64),
            executor=self.executor,
            path=self._quadlets_config_dir,
        )

        # Directory should already exist with correct permissions from _ensure_easyrunner_directory_structure()
        # If it doesn't exist, that indicates a setup issue
        if not quadlets_config_dir.exists():
            raise RuntimeError(
                f"Quadlets config directory '{self._quadlets_config_dir}' does not exist. "
                f"This should have been created during EasyRunner installation via _ensure_easyrunner_directory_structure(). "
                f"Please run 'er server init' to properly initialize the server."
            )

        for filename, content in quadlets_results.items():
            remote_quadlet_file_path: str = (
                # this unit filename partially determines the container name.
                # the container name format is 'systemd'-<compose_project.name>__<filename=<service name>.container>
                f"{quadlets_config_dir.path}/{compose_project.name}__{filename}"
            )
            unit_file_obj = io.BytesIO(initial_bytes=content.encode(encoding="utf-8"))

            unit_file_obj.seek(0)
            # write the unit file to the remote host directly
            put_result: ExecResult = self._command_executor.put_file(
                source=unit_file_obj,
                remote_path=remote_quadlet_file_path,
            )
            logger.debug(
                f"Wrote unit file to remote host: {remote_quadlet_file_path}. Success='{put_result.success}'. Result.stdout: {put_result.stdout}. Result.stderr: {put_result.stderr}"
            )

            # Set proper ownership and permissions for the unit file after creation
            if put_result.success:
                unit_file = File(
                    commands=self._file_cmds,
                    executor=self.executor,
                    path=remote_quadlet_file_path,
                )
                unit_file.set_owner(
                    owner_user=self._easyrunner_username,
                    owner_group=self._easyrunner_username,
                )
                unit_file.set_permissions(mode="644")

    def _ensure_easyrunner_directory_structure(self) -> None:
        """Ensure all EasyRunner directories exist with correct ownership and permissions.

        This method creates the directory structure if it doesn't exist and fixes ownership
        and permissions even if directories already exist. This handles cases where
        directories were created with incorrect ownership (e.g., by sudo or tar extraction).

        Handles running in the context of a user with root privileges (regardless of username so supports username other than 'root') or 'easyrunner' user.
        """
        try:
            logger.debug(
                "Ensuring EasyRunner directory structure exists with correct permissions"
            )

            # Detect current user context to handle both root and regular user scenarios
            whoami_result: ExecResult = self.executor.execute(
                command=RunnableCommandString(command="whoami")
            )
            current_user: str = (
                whoami_result.stdout.strip() if whoami_result.stdout else ""
            )

            # Check if running with root privileges - more reliable than just checking username
            id_result: ExecResult = self.executor.execute(
                command=RunnableCommandString(command="id -u")
            )
            user_id: str = id_result.stdout.strip() if id_result.stdout else ""
            is_root_user: bool = (
                user_id == "0"
            )  # UID 0 is always root regardless of username

            logger.debug(
                f"Current user context: {current_user} (UID: {user_id}), has_root_privileges: {is_root_user}"
            )

            # Define directories with their required permissions
            directories_config: List[tuple[str, str]] = [
                (f"{self._easyrunner_home_dir}/easyrunner-stack", "755"),
                (self._apps_source_dir, "750"),
                (self._infra_config_dir, "750"),
                (self._apps_compose_dir, "750"),
                (f"{self._easyrunner_home_dir}/.config", "750"),
                (f"{self._easyrunner_home_dir}/.config/containers", "750"),
                (self._quadlets_config_dir, "750"),
            ]

            for dir_path, permissions in directories_config:
                directory: Directory = Directory(
                    executor=self.executor,
                    commands=self._dir_cmds,
                    path=dir_path,
                )

                # Create directory if it doesn't exist
                if not directory.exists():
                    logger.debug(f"Creating directory: {dir_path}")
                    directory.create(
                        owner=self._easyrunner_username,
                        group=self._easyrunner_username,
                        mode=permissions,
                    )

                # Always fix ownership and permissions, even if directory already exists
                logger.debug(f"Setting ownership and permissions for: {dir_path}")

                if is_root_user:
                    # When running with root privileges, use direct chown/chmod commands without sudo
                    self.executor.execute(
                        command=RunnableCommandString(
                            command=f"chown {self._easyrunner_username}:{self._easyrunner_username} {dir_path}",
                            sudo=False,  # Already root, don't need sudo
                        )
                    )
                    self.executor.execute(
                        command=RunnableCommandString(
                            command=f"chmod {permissions} {dir_path}",
                            sudo=False,  # Already root, don't need sudo
                        )
                    )
                else:
                    # When running as regular user, use the Directory method which handles sudo internally
                    directory.set_owner(
                        owner_user=self._easyrunner_username,
                        owner_group=self._easyrunner_username,
                    )
                    directory.set_permissions(mode=permissions)

            logger.debug("EasyRunner directory structure setup completed")

        except Exception as e:
            error_msg: str = (
                f"Failed to ensure EasyRunner directory structure: {str(e)}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _ensure_github_repo_deploy_key_configured(
        self, repo_owner: str, repo_name: str, github_access_token: str
    ) -> bool:
        """Ensure a GitHub deploy key is configured for the repository.

        This method follows this flow:
        1. Check GitHub first to see if EasyRunner deploy key already exists
        2. Generate fresh SSH key pair in memory (never persists to disk)
        3. Add private key to SSH agent by content value
        4. Add/update public key to GitHub deploy keys by content value if needed
        5. Keys exist only in memory and SSH agent - never written to filesystem

        Args:
            repo_owner: The GitHub repository owner/organization
            repo_name: The GitHub repository name
            github_access_token: GitHub access token for API operations. If None,
                                 manual deploy key setup will be required.

        Raises:
            RuntimeError: If SSH agent setup fails or critical operations fail
        """
        logger.debug(f"Ensuring deploy key is configured for {repo_owner}/{repo_name}")

        key_name = f"{self._github_repo_deploy_key_name_prefix}_deploy_key"

        # Step 1: Check if GitHub access token is available and valid for API operations
        if github_access_token == "":
            logger.debug("No GitHub access token provided ")
            self._report_progress(
                "Run 'er auth login github' to enable automatic deploy key management",
            )

            return False

        # Step 2: Check GitHub first to see if EasyRunner deploy key already exists
        logger.debug("Checking GitHub for existing EasyRunner deploy keys")
        gh_client = GitHubApiClient(access_token=github_access_token)
        if not gh_client.is_access_token_valid():
            self._report_progress(
                "[red]GitHub access token is invalid or expired.[/red] Please re-authenticate using `er auth github`."
            )
            return False

        try:
            # existing_keys = gh_client.list_deploy_keys(repo_owner, repo_name)
            gh_repo = GithubRepo(
                owner=repo_owner,
                name=repo_name,
                github_api_client=gh_client,
            )

            list_key_result = gh_repo.list_deploy_keys()
            if not list_key_result.success or list_key_result.result is None:
                self._report_progress(
                    f"Failed to list existing deploy keys from GitHub: {list_key_result.return_code} - {list_key_result.stderr}"
                )
                return False

            # Look for existing EasyRunner deploy keys by title pattern in Github
            easyrunner_key_exists = False
            for existing_key in list_key_result.result:
                if (
                    self._github_repo_deploy_key_name_prefix in existing_key.title
                    or key_name in existing_key.title
                ):
                    logger.debug(
                        f"Found existing EasyRunner deploy key: {existing_key.title} (ID: {existing_key.id})"
                    )
                    easyrunner_key_exists = True

                    # Add the existing key's public key content to SSH agent by generating matching private key
                    # Note: We can't retrieve the private key, so we need to generate a new pair
                    # This is a limitation - we'll generate a new key and update the GitHub deploy key
                    logger.debug(
                        "Existing key found, but need to generate new key pair since private key cannot be retrieved"
                    )
                    break

            # Step 3: remove all existing EasyRunner deploy keys to avoid accumulation of old keys
            if easyrunner_key_exists:
                # remove the deploy key
                for existing_key in list_key_result.result:
                    if (
                        self._github_repo_deploy_key_name_prefix in existing_key.title
                        or key_name in existing_key.title
                    ):
                        logger.debug(
                            f"Removing existing EasyRunner deploy key: {existing_key.title} (ID: {existing_key.id})"
                        )

                        delete_result = gh_repo.delete_deploy_key(existing_key.id)
                        if delete_result.success:
                            logger.debug(
                                f"Successfully removed existing deploy key from GitHub: {delete_result.return_code}"
                            )
                        else:
                            self._report_progress(
                                f"Failed to remove existing deploy key from GitHub: {delete_result.return_code} - {delete_result.stderr}"
                            )

            # Step 4: Generate fresh SSH key pair in memory (always needed for private key)
            logger.debug(
                f"Generating fresh SSH key pair in memory for {repo_owner}/{repo_name}"
            )

            ssh_key = SshKey(
                email="deploy@easyrunner.dev",
                name=key_name,
                ssh_key_dir=None,  # Directory not provided as we don't want to accidentally write to disk
                regenerate_if_exists=True,  # always generate fresh key in memory
            )

            # Generate the key pair (always fresh, in memory only) as we don't call save.
            ssh_key.generate_ed25519_keypair()

            # Get key contents for SSH agent and GitHub
            private_key_content = ssh_key.private_key_as_string()
            public_key_content = ssh_key.public_key_as_string().strip()

            # Step 4: Clear SSH agent and add only the deploy key for this repo
            # Deploy keys are repo-specific, so we need to ensure only the right key is offered
            logger.debug(
                "Clearing SSH agent and adding only the deploy key for this repo..."
            )
            ssh_agent_instance = self.get_ssh_agent()
            clear_result = ssh_agent_instance.remove_all_keys()
            if not clear_result.success:
                logger.warning(f"Failed to clear SSH agent: {clear_result.stderr}")

            # Step 5: Add private key to SSH agent on server by content (always needed)
            logger.debug("Adding private key to SSH agent on server by content...")

            # Create metadata for the SSH key
            import json
            from datetime import datetime, timezone

            meta: JsonObject = {
                "repo": f"{repo_name}",
                "owner": f"{repo_owner}",
                "deploy_key_title": key_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Use the unified add_private_key method with SSH agent and metadata
            self.add_private_key(
                private_key=private_key_content,
                hostname="github.com",
                username="git",
                private_key_filename="",  # Not used when use_ssh_agent=True
                use_ssh_agent=True,
                metadata=json.dumps(meta),
            )

            # Step 5: Add deploy key to the repo on GitHub
            logger.debug(
                f"Adding deploy key to GitHub with public key: {public_key_content[:50]}..."
            )
            create_result = gh_repo.add_deploy_key(
                title=key_name,
                public_ssh_key_content=public_key_content,
                read_only=True,
            )
            if create_result.success:
                logger.debug(
                    f"Successfully added new deploy key to GitHub: {create_result.return_code}"
                )
                logger.debug(f"Deploy key response: {create_result.result}")
            else:
                self._report_progress(
                    f"Failed to add new deploy key to GitHub: {create_result.return_code} - {create_result.stderr}"
                )
                return False

        except Exception as e:
            # Log error but don't fail the deployment - manual SSH key setup is still possible
            self._report_progress(
                f"Failed to manage GitHub deploy key automatically: {str(e)}. Run with `--debug` for details."
            )

        logger.debug(f"Deploy key configuration completed for {repo_owner}/{repo_name}")
        return True

    def _configure_local_firewall(self) -> None:
        """Configure the local firewall using iptables.
        explicitly allow required ports.
        default policy for the INPUT chain is set to DROP.
        """
        try:
            ipt = IpTables(
                IpTablesCommandsUbuntu(cpu_arch=CpuArch.X86_64), self._command_executor
            )

            # STEP 1: Add ACCEPT rules FIRST (before any DROP policy)
            # 1. CRITICAL: Allow established connections (preserves current SSH session)
            ipt.add_inbound_rule(
                protocol="all",
                dport=None,
                source_ip="0.0.0.0/0",
                action="ACCEPT",
                state=["ESTABLISHED", "RELATED"],
            )

            # 2. Allow loopback traffic (essential for system processes)
            ipt.add_inbound_rule(
                protocol="all", dport=None, action="ACCEPT", source_ip="127.0.0.1"
            )

            # 3. CRITICAL: Allow SSH access (prevents lockout)
            ipt.add_inbound_rule(
                protocol="tcp", dport=22, action="ACCEPT", source_ip="0.0.0.0/0"
            )

            # 4. Allow HTTP and HTTPS traffic
            ipt.add_inbound_rule(
                protocol="tcp", dport=80, action="ACCEPT", source_ip="0.0.0.0/0"
            )
            ipt.add_inbound_rule(
                protocol="tcp", dport=443, action="ACCEPT", source_ip="0.0.0.0/0"
            )

            # 5. Caddy API protection - allow localhost only
            # even though #2 covers this we define explicitly for clarity.
            ipt.add_inbound_rule(
                protocol="tcp", dport=2019, action="ACCEPT", source_ip="127.0.0.1"
            )

            # 6. Caddy API protection - block external access
            ipt.add_inbound_rule(
                protocol="tcp", dport=2019, action="DROP", source_ip="0.0.0.0/0"
            )

            # STEP 2: Add NAT REDIRECT rules (instead of DNAT to localhost)
            # This redirects external traffic on ports 80/443 to internal ports 8080/8443
            ipt.add_port_redirect(source_port=80, dest_port=8080)
            ipt.add_port_redirect(source_port=443, dest_port=8443)

            # STEP 3: Add conntrack-based INPUT rules to allow redirected traffic
            # These rules only accept traffic that has been redirected by NAT (not direct access)
            ipt.add_accept_redirected_port_tcp(port=8080)
            ipt.add_accept_redirected_port_tcp(port=8443)

            # STEP 4: Set default DROP policy LAST
            ipt.set_default_policy(chain="INPUT", policy="DROP")

            # STEP 5: Save the configuration
            self._report_progress(
                "[yellow]Saving iptables configuration...[/yellow]", end=""
            )
            iptables_save_result = ipt.save()
            if not iptables_save_result.success:
                self._report_progress("[red]✗[/red]", end="\n")
                logger.error(
                    f"Failed to save firewall configuration. Error: {iptables_save_result.stderr}"
                )
            else:
                self._report_progress("[green]✔[/green]", end="\n")
                logger.debug("Successfully saved firewall configuration.")

        except Exception as e:
            raise RuntimeError("Failed to initialise host server.", e)

    def get_app_service_names(self, repo_name: str) -> List[str]:
        """Get the systemd service names for an application.

        Args:
            repo_name: The name of the application repository.

        Returns:
            List of systemd service names for the application.
        """
        try:
            # Load the compose project to get the actual service structure
            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)
            app_compose_file_path = f"{self._apps_compose_dir}/{self._build_app_compose_file_name(repo_name=repo_name)}"

            compose_project = podman.load_compose_file(
                compose_file_path=app_compose_file_path
            )

            # Build service names using the same pattern as deployment
            service_names = []
            for service_name in compose_project.services.keys():
                # The quadlet filename is {compose_project.name}__{service_name}.container
                # The systemd service name is {compose_project.name}__{service_name}.service
                systemd_service_name = f"{compose_project.name}__{service_name}.service"
                service_names.append(systemd_service_name)

            return service_names

        except Exception as e:
            logger.error(f"Failed to get service names for app {repo_name}: {str(e)}")
            return []

    def get_app_container_names(self, repo_name: str) -> List[str]:
        """Get the container names for an application.

        Args:
            repo_name: The name of the application repository.

        Returns:
            List of container names for the application.
        """
        try:
            # Load the compose project to get the actual service structure
            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)
            app_compose_file_path = f"{self._apps_compose_dir}/{self._build_app_compose_file_name(repo_name=repo_name)}"

            compose_project = podman.load_compose_file(
                compose_file_path=app_compose_file_path
            )

            # Build container names using the same pattern as deployment
            container_names = []
            for service in compose_project.services.values():
                container_name = compose_project.systemd_container_name(service)
                container_names.append(container_name)

            return container_names

        except Exception as e:
            logger.error(f"Failed to get container names for app {repo_name}: {str(e)}")
            return []

    def is_app_running(self, repo_name: str) -> bool:
        """Check if an application is currently running.

        Args:
            repo_name: The repository name of the application.

        Returns:
            True if the application containers are running, False otherwise.
        """
        try:
            container_names = self.get_app_container_names(repo_name)
            if not container_names:
                return False

            # Use the podman resource to check container status
            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)
            ps_result = podman.ps(all_containers=True)

            if ps_result.success and ps_result.stdout:
                for container_name in container_names:
                    if container_name in ps_result.stdout:
                        return True

            return False

        except Exception as e:
            logger.error(f"Failed to check if app {repo_name} is running: {str(e)}")
            return False

    def get_app_running_containers(self, repo_name: str) -> List[str]:
        """Get the list of running containers for an application.

        Args:
            repo_name: The repository name of the application.

        Returns:
            List of running container details for the application.
        """
        try:
            container_names = self.get_app_container_names(repo_name)
            if not container_names:
                return []

            # Use the podman resource to check container status
            podman = Podman(PodmanCommandsUbuntu(), self._command_executor)
            ps_result = podman.ps(all_containers=True)

            running_containers = []
            if ps_result.success and ps_result.stdout:
                lines = ps_result.stdout.strip().split("\n")
                for line in lines:
                    for container_name in container_names:
                        if container_name in line:
                            running_containers.append(line)

            return running_containers

        except Exception as e:
            logger.error(
                f"Failed to get running containers for app {repo_name}: {str(e)}"
            )
            return []
