from dataclasses import dataclass, field
from typing import Dict, Literal, Optional


@dataclass
class RunnableCommandString:
    """A command string that can be run on a system."""

    command: str
    """The command string to run."""
    env: Optional[Dict[str, str]] = field(default_factory=dict)
    """Environment variables to set before running the command."""
    sudo: bool = False
    """Whether to run the command with `sudo` (True) or not (False)."""
    output_to_file: Optional[str] = None
    """name of a file to send command output to. If None, output is sent to stdio."""
    append_or_overwrite: Optional[Literal["APPEND", "OVERWRITE"]] = "APPEND"
    """When output_to_file is defined, whether to append or overwrite the file. Defaults to APPEND."""

    def __str__(self) -> str:
        return self.command
