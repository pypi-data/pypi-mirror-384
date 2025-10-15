import logging
from io import BytesIO
from pathlib import Path

from invoke import run
from invoke.runners import Result as InvokeResult

from .commands.runnable_command_string import RunnableCommandString
from .types.exec_result import ExecResult


class CommandExecutorLocal:
    """ This class is responsible for executing commands on the local machine"""
    def __init__(self, debug: bool = False, silent: bool = True):
        # setup logger for this class with correct logger namespace hierarchy
        self._logger: logging.Logger = logging.getLogger(__name__)
        # Critical for libs to prevent log messages from propagating to the root logger and causing dup logs and config issues.
        self._logger.addHandler(logging.NullHandler())

        self.debug: bool = debug
        self.silent: bool = silent

        # Configure hide behavior like your SSH class
        if self.debug:
            self._hide: bool | str = False
        elif self.silent:
            self._hide = "both"
        else:
            # self._hide = False
            self._hide = "both"

    def execute(self, command: RunnableCommandString) -> ExecResult:
        """
        Execute a command on the local machine.

        Args:
            command: Command to execute
        """

        if command.output_to_file is not None:
            redirect_operator = ">>" if command.append_or_overwrite == "APPEND" else ">"
            command = RunnableCommandString(
                command=f"{command.command} {redirect_operator} {command.output_to_file}"
            )

        # Build the actual command to execute
        cmd = f"sudo {command.command}" if command.sudo else command.command

        try:
            result: InvokeResult | None = run(
                command=cmd,
                env=command.env,
                hide=self._hide,
                warn=True  # Don't raise on non-zero exit codes
            )
            mapped_result = self._map_invoke_result(result, command=command)

            self._logger.debug(
                "Command Executed > '%r', On Local Machine\n\n",
                mapped_result,
            )
            return mapped_result
        except Exception as e:
            self._logger.error(
                "Command didn't reach an exit code. Command: %s", cmd
            )
            return ExecResult(
                stdout="",
                stderr=str(e),
                return_code=1,
                success=False,
                command=command,
            )

    def put_file(self, source: Path | str | BytesIO, remote_path: str) -> ExecResult:
        """
        Copy a file locally from source to destination.

        Args:
            source: Path to source file or a file-like object as BytesIO.
            remote_path: Local destination path
        """
        try:
            dest_path = Path(remote_path)

            # Create parent directories if they don't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(source, (str, Path)):
                # Copy from file path
                source_path = Path(source)
                if not source_path.exists():
                    return ExecResult(
                        stdout="",
                        stderr=f"Source file does not exist: {source}",
                        return_code=1,
                        success=False,
                    )

                import shutil
                shutil.copy2(source_path, dest_path)
                self._logger.debug(
                    "File copied locally from '%s' to '%s'",
                    source_path,
                    dest_path,
                )

            elif isinstance(source, BytesIO):
                # Write from BytesIO object
                with open(dest_path, 'wb') as f:
                    f.write(source.getvalue())
                self._logger.debug(
                    "Content written to file '%s' from BytesIO object",
                    dest_path,
                )

            return ExecResult(
                stdout=f"File copied successfully from '{source}' to '{dest_path}'",
                stderr="",
                return_code=0,
                success=True,
            )

        except Exception as e:
            return ExecResult(
                stdout="",
                stderr=str(e),
                return_code=1,
                success=False,
            )

    def _map_invoke_result(
        self, result: InvokeResult | None, command: RunnableCommandString
    ) -> ExecResult:
        if result is None:
            return ExecResult(
                stdout="",
                stderr="InvokeResult was None",
                return_code=1,
                success=False,
                command=command,
            )

        return ExecResult(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            return_code=result.return_code,
            success=result.return_code == 0,
            command=command,
        )
