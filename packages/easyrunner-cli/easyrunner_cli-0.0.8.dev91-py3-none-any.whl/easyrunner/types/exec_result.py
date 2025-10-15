from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar, Union

from ..commands.runnable_command_string import RunnableCommandString

T = TypeVar("T")


@dataclass
class ExecResult(Generic[T]):
    """
    Represents the result of executing a command on a remote server. T is a generic
    type parameter used to specify the expected type of the result.

    This class encapsulates all information related to command execution, including
    the output streams (stdout, stderr), success status, return code, and the
    original command that was executed. It is primarily used as the return type
    for CommandExecutor.execute() and serves as a consistent interface for command
    execution results throughout the EasyRunner system.

    The class provides string representation methods for both human-readable output
    and detailed debugging information, as well as equality comparison and hashing
    capabilities for use in collections.

    Attributes:
        success (bool): Indicates whether the command executed successfully. True when the return code is 0 otherwise False.
        stdout (Optional[str]): The standard output captured from the command execution, if any.
        stderr (Optional[str]): The standard error captured from the command execution, if any.
        return_code (Optional[int]): The numeric exit code returned by the command.
        command (Optional[RunnableCommandString]): The command that was executed.
    """

    success: bool = False
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    command: Optional[RunnableCommandString] = None

    _result: Optional[T] = field(init=False, default=None, repr=True)

    @property
    def result(self) -> Union[T, None]:
        """Get the result value."""
        return self._result

    @result.setter
    def result(self, value: Union[T, None]) -> None:
        """Set the result value."""
        self._result = value

    def __str__(self) -> str:
        """Return a human-readable string representation focusing on command output."""
        if self.stdout:
            return self.stdout
        elif self.stderr:
            return self.stderr
        return "<No output>"
