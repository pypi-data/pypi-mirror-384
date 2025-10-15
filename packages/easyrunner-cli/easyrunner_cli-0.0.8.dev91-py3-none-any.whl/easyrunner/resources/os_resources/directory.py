from typing import List, Optional, Self, Union

from .... import logger
from ...command_executor import CommandExecutor
from ...commands.base.dir_commands import DirCommands
from ...types.dir_info import DirInfo
from ...types.exec_result import ExecResult
from ...types.file_info import FileInfo
from .os_resource_base import OsResourceBase


class Directory(OsResourceBase):
    """Represents a directory on the file system.

    This resource provides functionality to check if a directory exists
    and create it if necessary. It uses UtilityCommands under the hood
    to perform these operations.
    """

    def __init__(
        self,
        executor: CommandExecutor,
        commands: DirCommands,
        path: str,
        dir_info: Optional[DirInfo] = None,
    ) -> None:
        """Initialize a directory resource.

        Args:
            executor: CommandExecutor instance for executing commands
            commands: DirCommands instance for directory operations
            path: Absolute path of the directory
            dir_info: Parsed directory information
        """
        super().__init__(commands=commands, executor=executor)
        self._commands: DirCommands = commands
        self.dir_info = dir_info
        self.path = path

    def exists(self) -> bool:
        """Check if the directory exists.

        Returns:
            bool: True if directory exists, False otherwise
        """
        exists: bool = False
        result: ExecResult = self.executor.execute(
            command=self._commands.dir_exists(directory=self.path)
        )
        logger.debug(
            f"{result}, {result.return_code}, {result.stdout}, {result.stderr}, {result.success}"
        )
        if result.success:
            exists = (
                True
                if result.stdout is not None and "exists true" in result.stdout
                else False
            )
        logger.debug(f"Directory '{self.path}' exists '{exists}'")
        return exists

    def create(
        self: Self,
        owner: str,
        group: str,
        mode: str = "750",
    ) -> ExecResult[bool]:
        """Create the directory if it doesn't exist.

        Uses `install -d <owner> -g <group> -m <mode> <path>`

        Mode is 750 to be secure by default because other users have no permissions.

        Args:
            owner: The owner username of the directory
            group: The group name of the directory
            mode: The permissions mode of the directory. Defaults to "750" - Owner: rwx, Group: rx, Others: none

        Returns:
            bool: True if successful, False otherwise
        """
        if self.exists():
            result = ExecResult(stdout=None, stderr=None, return_code=0, success=True)
            result.result = True
            return result

        result: ExecResult = self.executor.execute(
            command=self._commands.install(
                directory=self.path, owner=owner, group=group, mode=mode
            )
        )
        if result.success and self.exists():
            logger.debug(f"Directory '{self.path}' created successfully.")
            result.result = True
            return result
        else:
            logger.debug(f"Directory '{self.path}' creation failed.")
            result = ExecResult[bool](
                stdout=None,
                stderr=f"Directory '{self.path}' creation failed.",
                return_code=1,
                success=False,
            )
            result.result = False
            return result

    def remove(self: Self) -> ExecResult:
        """Remove the directory.

        Uses `rm -rf <path>` to remove the directory and all its contents.

        Returns:
            ExecResult: Result of the removal operation
        """
        if not self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"Directory '{self.path}' does not exist.",
                return_code=1,
                success=False,
            )

        return self.executor.execute(command=self._commands.rm(directory=self.path))

    def set_permissions(self, mode: str) -> ExecResult:
        """Set permissions on the directory.

        Args:
            mode: Permission mode string (e.g. "755"). Exactly the same as the chmod command.

        Returns:
            ExecResult: Result of the chmod operation
        """
        if not self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"Directory '{self.path}' does not exist.",
                return_code=1,
                success=False,
            )

        result: ExecResult = self.executor.execute(
            command=self._commands.chmod(mode=mode, directory=self.path)
        )
        return result

    def set_owner(
        self, owner_user: str, owner_group: str, recursive: bool = False
    ) -> ExecResult:
        """Set the owner of the directory using chown.

        Args:
            owner_user: The user to set as the owner
            owner_group: The group to set as the owner
            recursive: Whether to apply the ownership change recursively to all the sub folders as well.

        Returns:
            ExecResult: Result of the chown operation
        """
        if not self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"Directory '{self.path}' does not exist.",
                return_code=1,
                success=False,
            )

        result: ExecResult = self.executor.execute(
            command=self._commands.chown(
                owner=f"{owner_user}:{owner_group}",
                directory=self.path,
                recursive=recursive,
            )
        )
        return result

    def list(
        self: Self, filter: Optional[str] = None
    ) -> ExecResult[List[Union[DirInfo, FileInfo]]]:
        """List the contents of the directory.

        Args:
            filter: Optional glob expression. this will be appended to the path.
        Returns:
            ExecResult: The contents of the directory if successful, or None if not.
        """
        if not self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"Directory '{self.path}' does not exist.",
                return_code=1,
                success=False,
            )

        result: ExecResult = self.executor.execute(
            command=self._commands.ls(
                directory=self.path + (f"/{filter}" if filter else "")
            )
        )

        dir_list: List[Union[DirInfo, FileInfo]] = self._parse_ls_asl_output(
            result.stdout or ""
        )
        dir_list_result = ExecResult[List[Union[DirInfo, FileInfo]]](
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.return_code,
            success=result.success,
        )

        dir_list_result.result = dir_list
        return dir_list_result

    @staticmethod
    def _parse_ls_asl_output(ls_output: str) -> List[Union[DirInfo, FileInfo]]:
        """Parse ls -asl output into File and Directory instances."""

        entries: List[Union[DirInfo, FileInfo]] = []
        for line in ls_output.splitlines():
            line = line.strip()
            if not line or line.startswith("total"):
                continue
            parts = line.split(None, 9)
            if len(parts) < 10:
                continue
            if parts[1].startswith("d"):
                dir_info = DirInfo.from_ls_entry(parts)
                entries.append(dir_info)
            else:
                file_info = FileInfo.from_ls_entry(parts)
                entries.append(file_info)
        return entries
