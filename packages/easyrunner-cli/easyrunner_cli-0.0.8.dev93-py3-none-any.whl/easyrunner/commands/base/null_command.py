from easyrunner.source.types.os_type import OS

from ...commands.runnable_command_string import RunnableCommandString
from ...types.cpu_arch_types import CpuArch
from ..base.command_base import CommandBase


class NullCommand(CommandBase):
  """A null object implementation of CommandBase that returns None for all commands."""

  def __init__(self):
    """Initialize NullCommand with default values."""
    super().__init__(
      os=OS.NONE,
      cpu_arch=CpuArch.NONE,
      command_name="none",
      pkg_name="none"
    )

  def version(self) -> RunnableCommandString:
    """Returns None as a RunnableCommandString."""
    return RunnableCommandString(command="")
