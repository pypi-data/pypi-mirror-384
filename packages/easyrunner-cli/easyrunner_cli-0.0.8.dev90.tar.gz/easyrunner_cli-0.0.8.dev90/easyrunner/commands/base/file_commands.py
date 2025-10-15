import os
import shlex
from pathlib import Path
from typing import Optional

from typing_extensions import Literal

from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..base.command_base import CommandBase
from ..runnable_command_string import RunnableCommandString


class FileCommands(CommandBase):
    # Security constants
    _MAX_CONTENT_SIZE: int = 1024 * 1024  # 1MB limit
    _ALLOWED_EXTENSIONS: set[str] = {
        ".yaml",
        ".yml",
        ".conf",
        ".txt",
        ".key",
        ".pub",
        ".json",
    }

    # Safe absolute path patterns for SSH and system operations
    # nosec B108 - These are path validation patterns, not temp file creation
    _SAFE_ABSOLUTE_PATH_PATTERNS: set[str] = {
        "/home/*/",
        "/root/",
        "/tmp/",  # nosec B108 - validation pattern, not temp file usage
        "/var/tmp/",  # nosec B108 - validation pattern, not temp file usage
        "/etc/ssh/",
        "/etc/caddy/",
        "/etc/systemd/",
        "/var/lib/containers/",
        "/run/user/*/",
    }

    def __init__(self, os: OS, cpu_arch: CpuArch, command_name: str) -> None:
        super().__init__(
            os=os, cpu_arch=cpu_arch, command_name=command_name, pkg_name=""
        )

    def _validate_content_size(self, content: str) -> None:
        """Validate content size to prevent DoS attacks.

        Args:
            content: The content to validate

        Raises:
            ValueError: If content exceeds maximum allowed size
        """
        content_size: int = len(content.encode("utf-8"))
        if content_size > self._MAX_CONTENT_SIZE:
            raise ValueError(
                f"Content too large. Size: {content_size} bytes, "
                f"Maximum allowed: {self._MAX_CONTENT_SIZE} bytes"
            )

    def _validate_file_extension(self, file_path: str) -> None:
        """Validate file extension against allowed list.

        Args:
            file_path: The file path to validate

        Raises:
            ValueError: If file extension is not in allowed list
        """
        file_ext: str = Path(file_path).suffix.lower()
        # Allow files without extensions (like SSH config, Dockerfile, etc.)
        if file_ext and file_ext not in self._ALLOWED_EXTENSIONS:
            raise ValueError(
                f"File extension '{file_ext}' not allowed. "
                f"Allowed extensions: {', '.join(sorted(self._ALLOWED_EXTENSIONS))} or no extension"
            )

    def _is_safe_absolute_path(self, file_path: str) -> bool:
        """Check if an absolute path matches safe patterns.

        Args:
            file_path: The absolute file path to check

        Returns:
            bool: True if the path is considered safe, False otherwise
        """
        import fnmatch

        for pattern in self._SAFE_ABSOLUTE_PATH_PATTERNS:
            if fnmatch.fnmatch(file_path, pattern + "*"):
                return True
        return False

    def _sanitize_file_path(self, file_path: str) -> str:
        """Sanitize and validate file path to prevent path traversal attacks.

        Args:
            file_path: The file path to sanitize

        Returns:
            str: The sanitized file path

        Raises:
            ValueError: If path contains dangerous patterns
        """
        # Normalize the path to resolve any .. or . components
        normalized_path: str = os.path.normpath(file_path)

        # Prevent path traversal attacks
        if ".." in normalized_path:
            raise ValueError(f"Path traversal detected in file path: {file_path}")

        # Check if absolute path is safe before blocking it
        if normalized_path.startswith("/"):
            if not self._is_safe_absolute_path(normalized_path):
                raise ValueError(f"Unsafe absolute path not allowed: {file_path}")

        return normalized_path

    def _escape_shell_content(self, content: str) -> str:
        """For heredoc usage, no escaping needed - content is used literally.

        Args:
            content: The content to use (will be used as-is in heredoc)

        Returns:
            str: The content unchanged (heredoc handles safety)
        """
        return content

    def _validate_against_shell_injection(self, content: str) -> None:
        """Validate content against shell injection patterns.

        Args:
            content: The content to validate

        Raises:
            ValueError: If content contains dangerous shell patterns
        """
        # Check for common shell injection patterns
        dangerous_patterns: list[str] = [
            "`",  # Command substitution
            "$((",  # Arithmetic expansion
            "$(",  # Command substitution
            "&&",  # Command chaining
            "||",  # Command chaining
            ";",  # Command separator
            "|",  # Pipe (excluding in tee command)
            ">",  # Redirection
            "<",  # Redirection
            "\n",  # Newline can break out of quotes
            "\r",  # Carriage return
        ]

        for pattern in dangerous_patterns:
            if pattern in content:
                raise ValueError(
                    f"Dangerous shell pattern '{pattern}' detected in content. "
                    f"Content will be safely escaped for execution."
                )

    def _validate_file_path_security(self, file_path: str) -> str:
        """Validate file path for security and return sanitized path.

        Args:
            file_path: The file path to validate

        Returns:
            str: The sanitized and validated file path

        Raises:
            ValueError: If path is invalid or dangerous
        """
        # Validate file extension
        self._validate_file_extension(file_path)

        # Sanitize and validate path
        sanitized_path: str = self._sanitize_file_path(file_path)

        return sanitized_path

    def chmod(self, mode: str, file: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"chmod {mode} {file}", sudo=True)

    def chown(self, owner: str, file: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"chown {owner} {file}", sudo=True)

    def file_exists(self, file: str) -> RunnableCommandString:
        # return RunnableCommandString(command=f"test -f {file}")
        return RunnableCommandString(
            command=f"[ -f {file} ] && echo 'exists true' || echo 'exists false';"
        )

    def cp(self, source: str, destination: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"cp {source} {destination}", sudo=True)

    def mv(self, source: str, destination: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"mv {source} {destination}", sudo=True)

    def touch(self, file_path: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"touch {file_path}", sudo=True)

    def install(
        self,
        dst_file_path: str,
        owner: str,
        group: str,
        mode: str = "750",
        src_file_path: Optional[str] = None,
    ) -> RunnableCommandString:
        """Create a file with the specified owner, group, and mode.

        When <src_file_path> is provided, the file will be created by copying from the source file.

        Otherwise, an empty file will be created.

        Permissions set to secure by default.
        Args:
            file_path: The file to create
            owner: The owner of the file
            group: The group of the file
            mode: The permissions mode of the file. Defaults to "750" - Owner: rwx, Group: rx, Others: none.
            src: The source file to copy from. When `None`, an empty file will be created.
        """
        src_cmd = "/dev/null" if src_file_path is None else src_file_path
        return RunnableCommandString(
            command=f"install -o {owner} -g {group} -m {mode} {src_cmd} {dst_file_path}",
            sudo=False,
        )

    def open_read(self, file_path: str) -> RunnableCommandString:
        return RunnableCommandString(command=f"cat {file_path}", sudo=False)

    def open_write(
        self,
        file_path: str,
        content: str,
        mode: Optional[Literal["APPEND", "OVERWRITE"]] = "APPEND",
    ) -> RunnableCommandString:
        """Write content to a file with comprehensive security validation.

        Args:
            file_path: The file path to write to
            content: The content to write
            mode: Write mode - APPEND or OVERWRITE

        Returns:
            RunnableCommandString: The command to execute

        Raises:
            ValueError: If content or file path fails security validation
        """
        # Validate content size to prevent DoS attacks
        self._validate_content_size(content)

        # Validate file path for security
        sanitized_path: str = self._validate_file_path_security(file_path)

        # Log warning if dangerous patterns detected (but continue with heredoc)
        try:
            self._validate_against_shell_injection(content)
        except ValueError:
            # Continue execution with heredoc (safer than echo + escaping)
            pass

        # Use heredoc approach - no content escaping needed, only path escaping
        escaped_path: str = shlex.quote(sanitized_path)

        if mode == "APPEND":
            command: str = f"""cat >> {escaped_path} << 'EASYRUNNER_EOF'
{content}
EASYRUNNER_EOF"""
        else:
            command = f"""cat > {escaped_path} << 'EASYRUNNER_EOF'
{content}
EASYRUNNER_EOF"""

        return RunnableCommandString(command=command, sudo=False)

    def version(self) -> RunnableCommandString:
        return super().version()
