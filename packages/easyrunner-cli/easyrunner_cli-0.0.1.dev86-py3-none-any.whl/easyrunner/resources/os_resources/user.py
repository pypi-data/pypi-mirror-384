from typing import List, Optional

from .... import logger
from ...command_executor import CommandExecutor
from ...commands.base.user_commands import UserCommands
from ...types.exec_result import ExecResult
from .os_resource_base import OsResourceBase


class User(OsResourceBase):
    """Represents a system user account.
    
    This resource provides functionality to manage user accounts including
    creation, deletion, group management, and other user-related operations.
    """

    def __init__(
        self,
        executor: CommandExecutor,
        commands: UserCommands,
        username: str,
    ) -> None:
        """Initialize a user resource.

        Args:
            executor: CommandExecutor instance for executing commands
            commands: UserCommands instance for user operations
            username: The username this resource represents
        """
        super().__init__(commands=commands, executor=executor)
        self._commands: UserCommands = commands
        self.username = username

    def exists(self) -> bool:
        """Check if the user exists.
        
        Returns:
            bool: True if user exists, False otherwise
        """
        result: ExecResult = self.executor.execute(
            command=self._commands.check_user_exists(username=self.username)
        )

        logger.debug(
            f"User check result: {result}, return_code: {result.return_code}, "
            f"stdout: {result.stdout}, stderr: {result.stderr}, success: {result.success}"
        )

        # User exists if id command returns 0 (success)
        exists = result.return_code == 0
        logger.debug(f"User '{self.username}' exists: {exists}")
        return exists

    def create(
        self, 
        password: Optional[str] = None, 
        create_home: bool = True, 
        shell: str = "/bin/bash"
    ) -> ExecResult:
        """Create the user if it doesn't exist.

        Args:
            password: Optional password for the user. If None, no password is set.
            create_home: Whether to create a home directory for the user. Defaults to True.
            shell: The default shell for the user. Defaults to "/bin/bash".

        Returns:
            ExecResult: Result of the user creation operation
        """
        if self.exists():
            logger.debug(f"User {self.username} already exists")
            return ExecResult(
                success=True, 
                return_code=0, 
                stdout=f"User {self.username} already exists", 
                stderr=""
            )

        # Create user using command class
        create_user_cmd = self._commands.create_user(
            username=self.username,
            create_home=create_home,
            shell=shell  # nosec B604 - shell parameter is the user's login shell (e.g., /bin/bash), not subprocess shell=True
        )

        result = self.executor.execute(command=create_user_cmd)

        if result.success and password is not None:
            # Set password using command class
            passwd_cmd = self._commands.set_password(self.username, password)
            passwd_result = self.executor.execute(command=passwd_cmd)
            if not passwd_result.success:
                logger.warning(f"User {self.username} created but password setting failed: {passwd_result.stderr}")

        if result.success:
            logger.debug(f"Successfully created user: {self.username}")
        else:
            logger.error(f"Failed to create user {self.username}: {result.stderr}")

        return result

    def delete(self, remove_home: bool = False) -> ExecResult:
        """Delete the user.

        Args:
            remove_home: Whether to remove the user's home directory. Defaults to False.

        Returns:
            ExecResult: Result of the user deletion operation
        """
        if not self.exists():
            logger.debug(f"User {self.username} does not exist")
            return ExecResult(
                success=True, 
                return_code=0, 
                stdout=f"User {self.username} does not exist", 
                stderr=""
            )

        delete_cmd = self._commands.delete_user(
            username=self.username,
            remove_home=remove_home
        )

        result = self.executor.execute(command=delete_cmd)

        if result.success:
            logger.debug(f"Successfully deleted user: {self.username}")
        else:
            logger.error(f"Failed to delete user {self.username}: {result.stderr}")

        return result

    def add_to_groups(self, groups: List[str]) -> ExecResult:
        """Add the user to one or more groups.

        Args:
            groups: List of group names to add the user to.

        Returns:
            ExecResult: Result of the group assignment operations
        """
        if not self.exists():
            error_msg = f"User {self.username} does not exist"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

        # Add user to each group
        failed_groups = []
        for group in groups:
            usermod_cmd = self._commands.add_user_to_group(self.username, group)
            result = self.executor.execute(command=usermod_cmd)

            if not result.success:
                failed_groups.append(group)
                logger.warning(f"Failed to add user {self.username} to group {group}: {result.stderr}")
            else:
                logger.debug(f"Successfully added user {self.username} to group {group}")

        if failed_groups:
            error_msg = f"Failed to add user {self.username} to groups: {', '.join(failed_groups)}"
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)
        else:
            success_msg = f"Successfully added user {self.username} to groups: {', '.join(groups)}"
            return ExecResult(success=True, return_code=0, stdout=success_msg, stderr="")

    def set_password(self, password: str) -> ExecResult:
        """Set the user's password.

        Args:
            password: The password to set for the user

        Returns:
            ExecResult: Result of the password setting operation
        """
        if not self.exists():
            error_msg = f"User {self.username} does not exist"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

        passwd_cmd = self._commands.set_password(self.username, password)
        result = self.executor.execute(command=passwd_cmd)

        if result.success:
            logger.debug(f"Successfully set password for user: {self.username}")
        else:
            logger.error(f"Failed to set password for user {self.username}: {result.stderr}")

        return result

    def get_home_directory(self) -> ExecResult[str]:
        """Get the user's home directory path.

        Returns:
            ExecResult[str]: Result containing the home directory path if successful
        """
        if not self.exists():
            error_msg = f"User {self.username} does not exist"
            logger.error(error_msg)
            result = ExecResult[str](
                success=False, return_code=1, stdout=None, stderr=error_msg
            )
            result.result = None
            return result

        home_dir_cmd = self._commands.get_user_home_directory(self.username)
        result = self.executor.execute(command=home_dir_cmd)

        if result.success and result.stdout:
            home_path = result.stdout.strip()
            logger.debug(f"Home directory for user {self.username}: {home_path}")
            typed_result = ExecResult[str](
                success=result.success, 
                return_code=result.return_code, 
                stdout=result.stdout, 
                stderr=result.stderr
            )
            typed_result.result = home_path
            return typed_result
        else:
            error_msg = f"Failed to get home directory for user {self.username}"
            logger.error(error_msg)
            typed_result = ExecResult[str](
                success=False, return_code=1, stdout=None, stderr=error_msg
            )
            typed_result.result = None
            return typed_result

    def add_to_sudoers_nopasswd(self) -> ExecResult:
        """Add the user to sudoers with passwordless sudo access.

        Returns:
            ExecResult: Result of the sudoers configuration operation
        """
        if not self.exists():
            error_msg = f"User {self.username} does not exist"
            logger.error(error_msg)
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

        sudoers_cmd = self._commands.add_user_to_sudoers_nopasswd(self.username)
        result = self.executor.execute(command=sudoers_cmd)

        if result.success:
            logger.debug(
                f"Successfully added user {self.username} to sudoers with NOPASSWD"
            )
        else:
            logger.error(
                f"Failed to add user {self.username} to sudoers: {result.stderr}"
            )

        return result

    def has_sudo_access(self) -> bool:
        """Check if the user has sudo access.

        Returns:
            bool: True if user has sudo access, False otherwise
        """
        if not self.exists():
            logger.debug(f"User {self.username} does not exist, cannot have sudo access")
            return False

        sudo_check_cmd = self._commands.check_user_has_sudo_access(self.username)
        result = self.executor.execute(command=sudo_check_cmd)

        has_sudo = result.return_code == 0
        logger.debug(f"User '{self.username}' has sudo access: {has_sudo}")
        return has_sudo
