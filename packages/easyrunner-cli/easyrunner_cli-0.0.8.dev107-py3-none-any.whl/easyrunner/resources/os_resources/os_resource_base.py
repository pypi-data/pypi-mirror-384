import logging

from ...command_executor import CommandExecutor
from ...commands.base.command_base import CommandBase
from ..resource_base import ResourceBase


class OsResourceBase(ResourceBase):
    """Represents the state of a system component. A system component is a part of a stack that forms a complete working system.
    In the context of Easyrunner that's a host server running the stack.
    """

    def __init__(self, commands: CommandBase, executor: CommandExecutor):
        # setup logger for this class with correct logger namespace hierarchy
        self._logger: logging.Logger = logging.getLogger(__name__)
        # Critical for libs to prevent log messages from propagating to the root logger and causing dup logs and config issues.
        self._logger.addHandler(logging.NullHandler())

        self._commands = commands
        self.executor = executor
