import logging
from io import BytesIO
from pathlib import Path

from fabric import Result as InvokeResult
from fabric.transfer import Result as TransferResult

from .commands.runnable_command_string import RunnableCommandString
from .ssh import Ssh
from .types.exec_result import ExecResult


class CommandExecutor:
    """This class is responsible for executing commands on the remote machine"""
    def __init__(self, ssh_client: Ssh):
        # setup logger for this class with correct logger namespace hierarchy
        self._logger: logging.Logger = logging.getLogger(__name__)
        # Critical for libs to prevent log messages from propagating to the root logger and causing dup logs and config issues.
        self._logger.addHandler(logging.NullHandler())

        self.ssh_client: Ssh = ssh_client

    def execute(self, command: RunnableCommandString) -> ExecResult:
        """
        Execute a command on the remote host.

        Args:
            command: Command to execute
        """

        if command.output_to_file is not None:
            redirect_operator = ">>" if command.append_or_overwrite == "APPEND" else ">"
            command = RunnableCommandString(
                command=f"{command.command} {redirect_operator} {command.output_to_file}"
            )

        with self.ssh_client as ssh:
            result: InvokeResult = (
                ssh.run_sudo(command=command)
                if command.sudo
                else ssh.run(command=command)
            )
            mapped_result = self._map_invoke_result(result, command=command)

            self._logger.debug(
                "Command Executed > '%r', On Remote Host: '%s:%s'\n\n",
                mapped_result,
                ssh.hostname,
                ssh.port,
            )
            return mapped_result

    def put_file(self, source: Path | str | BytesIO, remote_path: str) -> ExecResult:
        """
        Transfer a file from local machine where this method is executed to remote host.

        See https://docs.fabfile.org/en/latest/api/transfer.html#fabric.transfer.Transfer.put
        Args:
            local_path: Path to local file or a file-like object as io.StringIO(content_str).
            remote_path: Remote destination path
        """
        try:
            with self.ssh_client as ssh:
                self._logger.debug(
                    "Transferring file to remote host. Remote path: '%s'",
                    remote_path,
                )
                result: TransferResult = ssh.connection.put(
                    local=source, remote=remote_path, preserve_mode=False
                )

                return ExecResult(
                    stdout=f"Transferring file '{result.local}' to remote '{result.remote}' successfully",
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

            # raise RuntimeError(
            #     f"CommandExecutor.put_file() - Failed to transfer file to remote host: {str(e)}"
            # )

    def _map_invoke_result(
        self, result: InvokeResult, command: RunnableCommandString
    ) -> ExecResult:
        return ExecResult(
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.return_code,
            success=result.return_code == 0,
            command=command,
        )
