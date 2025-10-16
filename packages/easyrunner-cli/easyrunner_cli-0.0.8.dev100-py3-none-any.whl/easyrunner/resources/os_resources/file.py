from typing import Literal, Optional

from .... import logger
from ...command_executor import CommandExecutor
from ...commands.base.file_commands import FileCommands
from ...types.exec_result import ExecResult
from ...types.file_info import FileInfo
from .os_resource_base import OsResourceBase


class File(OsResourceBase):
    """Represents a file on the file system.
    
    """

    def __init__(
        self,
        executor: CommandExecutor,
        commands: FileCommands,
        path: str,
        file_info: Optional[FileInfo] = None,
    ) -> None:
        """Initialize a file resource.

        Args:
            executor: CommandExecutor instance for executing commands
            commands: DirCommands instance for file operations
            path: Absolute path of the file including the file name
            file_info: FileInfo instance containing file metadata
        """
        super().__init__(commands=commands, executor=executor)
        self._commands: FileCommands = commands
        self.file_info = file_info
        self.path = path

    def exists(self) -> bool:
        """Check if the file exists.
        
        Returns:
            bool: True if file exists, False otherwise
        """
        exists: bool = False
        result: ExecResult = self.executor.execute(
            command=self._commands.file_exists(file=self.path)
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
        logger.debug(f"File '{self.path}' exists '{exists}'")
        return exists

    def copy(self, destination: str, owner: str, group: str, mode: str = "750") -> bool:
        """Copy the file to a new location.
        
        Args:
            destination: The destination path where the file should be copied
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.exists():
            return False

        # result: ExecResult = self.executor.execute(
        #     command=self._commands.cp(source=self.path, destination=destination)
        # )
        result = self.executor.execute(
            command=self._commands.install(
                src_file_path=self.path,
                dst_file_path=destination,
                owner=owner,
                group=group,
                mode=mode,
            )
        )
        return result.return_code == 0

    def create(self, owner: str, group: str, mode: str = "750") -> ExecResult:
        """Create the file if it does not exist.

        Returns:
            ExecResult: Result of the create operation
        """
        if self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"File '{self.path}' already exists.",
                return_code=1,
                success=False,
            )

        # result: ExecResult = self.executor.execute(
        #     command=self._commands.touch(file_path=self.path)
        # )
        result = self.executor.execute(
            command=self._commands.install(
                dst_file_path=self.path,
                owner=owner,
                group=group,
                mode=mode,
            )
        )
        return result

    def set_permissions(self, mode: str) -> ExecResult:
        """Set permissions on the file using chmod.

        Args:
            mode: Permission mode string (e.g. "755"). Exactly the same as the chmod command.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"File '{self.path}' does not exist. Cannot set permissions.",
                return_code=1,
                success=False,
            )

        result: ExecResult = self.executor.execute(
            command=self._commands.chmod(mode=mode, file=self.path)
        )
        return result

    def set_owner(self, owner_user: str, owner_group: str) -> ExecResult:
        """Set the owner of the file using chown. owner user and group same as chown command.

        Args:
            owner_user: The user to set as the owner
            owner_group: The group to set as the owner

        Returns:
            ExecResult: Result of the chown operation
        """
        if not self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"File '{self.path}' does not exist. Cannot set owner.",
                return_code=1,
                success=False,
            )

        result: ExecResult = self.executor.execute(
            command=self._commands.chown(
                owner=f"{owner_user}:{owner_group}", file=self.path
            )
        )
        return result

    def open_read(self) -> ExecResult[str]:
        """Open the file for reading.

        Returns:
            ExecResult: The contents of the file if successful, or None if not.
        """
        if not self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"File '{self.path}' does not exist. Cannot open_read.",
                return_code=1,
                success=False,
            )

        result: ExecResult[str] = self.executor.execute(
            command=self._commands.open_read(file_path=self.path)
        )
        return result

    def open_write(
        self, content: str, mode: Optional[Literal["APPEND", "OVERWRITE"]] = "APPEND"
    ) -> ExecResult:
        """Open the file for writing. Does NOT create the file.

        Args:
            content: The content to write to the file
            mode: The mode to open the file in (APPEND or OVERWRITE)

        Returns:
            ExecResult: The result of the open operation.
        """

        if not self.exists():
            return ExecResult(
                stdout=None,
                stderr=f"File '{self.path}' does not exist. Cannot open_write to APPEND.",
                return_code=1,
                success=False,
            )

        result: ExecResult = self.executor.execute(
            command=self._commands.open_write(
                file_path=self.path, content=content, mode=mode
            )
        )
        return result
