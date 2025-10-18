import logging
from abc import ABC, abstractmethod

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString


class CommandBase(ABC):
    def __init__(
        self, os: OS, cpu_arch: CpuArch, command_name: str, pkg_name: str
    ) -> None:
        # setup logger for this class with correct logger namespace hierarchy
        self._logger: logging.Logger = logging.getLogger(__name__)
        # Critical for libs to prevent log messages from propagating to the root logger and causing dup logs and config issues.
        self._logger.addHandler(logging.NullHandler())

        """Represents a command line interface program/executable.
        Sub commands are represented as methods of this class.
        Sub command options are represented as keyword arguments to the sub command methods.

        Args:
            os (OS): The operating system the command is intended to run on.
            cpu_arch (CpuArch): The CPU architecture of the system.
            command_name (str): The name of the primary command/executable. E.g.: git, apt-get etc.
        """
        self.os: OS = os
        self.cpu_arch: CpuArch = cpu_arch
        self.command_name: str = command_name
        self.pkg_name: str = pkg_name

    @abstractmethod
    def version(self) -> RunnableCommandString:
        """command that returns the version of the command line program."""
        pass

    def version_response_prefix(self) -> str:
        """The prefix of the response string that contains the version information.
        This is used to verify that the command executed successfully and returned the expected output.
        """
        return f"{self.command_name} version"
