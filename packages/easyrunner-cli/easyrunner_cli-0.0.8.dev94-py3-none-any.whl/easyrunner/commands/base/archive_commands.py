from typing import List, Optional

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class ArchiveCommands(CommandBase):
    """Base class for archive-related commands (tar, etc.)."""

    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str = "tar") -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name="tar"
        )

    def create(self, archive_name: str, files: List[str], compress: bool = True) -> RunnableCommandString:
        """Create a tar archive.
        
        Args:
            archive_name: Name of the archive to create (should end in .tar or .tar.gz)
            files: List of files/directories to include in the archive
            compress: Whether to use gzip compression (creates .tar.gz)
        """
        compress_flag = "czf" if compress else "cf"
        files_str = " ".join(files)
        return RunnableCommandString(
            command=f"{self.command_name} -{compress_flag} {archive_name} {files_str}"
        )

    def extract(self, archive_name: str, target_dir: Optional[str] = None) -> RunnableCommandString:
        """Extract a tar archive.
        
        Args:
            archive_name: Name of the archive to extract
            target_dir: Optional directory to extract to. If None, extracts to current directory.
        """
        extract_flags = "xf"
        if archive_name.endswith('.gz') or archive_name.endswith('.tgz'):
            extract_flags = "xzf"

        target_dir_str = f" -C {target_dir}" if target_dir else ""
        return RunnableCommandString(
            command=f"{self.command_name} -{extract_flags} {archive_name}{target_dir_str}"
        )

    def list_contents(self, archive_name: str) -> RunnableCommandString:
        """List the contents of a tar archive.
        
        Args:
            archive_name: Name of the archive to list contents of
        """
        list_flags = "tf"
        if archive_name.endswith('.gz') or archive_name.endswith('.tgz'):
            list_flags = "tzf"

        return RunnableCommandString(
            command=f"{self.command_name} -{list_flags} {archive_name}"
        )

    def version(self) -> RunnableCommandString:
        """Get the version of tar."""
        return RunnableCommandString(command=f"{self.command_name} --version")
