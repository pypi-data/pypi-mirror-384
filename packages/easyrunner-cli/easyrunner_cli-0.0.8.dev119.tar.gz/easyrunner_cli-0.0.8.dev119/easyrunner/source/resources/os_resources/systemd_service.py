from typing import Optional

from ...command_executor import CommandExecutor
from ...commands.base.systemctl_commands import SystemctlCommands
from ...commands.runnable_command_string import RunnableCommandString
from ...types.exec_result import ExecResult
from .os_resource_base import OsResourceBase


class SystemdService(OsResourceBase):
    """Resource for managing systemd services via systemctl on Ubuntu."""

    def __init__(
        self,
        commands: SystemctlCommands,
        executor: CommandExecutor,
        ServiceName: str,
        user_mode: bool = True,
        target_username: Optional[str] = None,
    ) -> None:
        super().__init__(commands=commands, executor=executor)
        self._commands: SystemctlCommands = commands
        self._executor: CommandExecutor = executor
        self._service_name: str = ServiceName
        self._user_mode: bool = user_mode
        self._target_username: Optional[str] = target_username

    def start(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.start(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def stop(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.stop(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def restart(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.restart(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def status(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.status(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def enable(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.enable(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def disable(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.disable(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def enable_now(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.enable_now(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def daemon_reload(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.daemon_reload(
            user_mode=self._user_mode, target_username=self._target_username
        )
        return self.executor.execute(command=cmd)

    def is_active(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.is_active(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def is_enabled(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.is_enabled(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)

    def is_failed(self) -> ExecResult:
        cmd: RunnableCommandString = self._commands.is_failed(
            service_name=self._service_name,
            user_mode=self._user_mode,
            target_username=self._target_username,
        )
        return self.executor.execute(command=cmd)
