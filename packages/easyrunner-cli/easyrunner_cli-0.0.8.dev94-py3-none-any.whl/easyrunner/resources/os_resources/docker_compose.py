from ...command_executor import CommandExecutor
from ...commands.base.docker_compose_commands import DockerComposeCommands
from ...types.exec_result import ExecResult
from .os_resource_base import OsResourceBase


class DockerCompose(OsResourceBase):
    def __init__(self, commands: DockerComposeCommands, executor: CommandExecutor):
        self.commands = commands
        self.executor = executor

    def up(self, compose_file: str) -> ExecResult:
        command = self.commands.up(compose_file)
        return self.executor.execute(command)

    def down(self, compose_file: str) -> ExecResult:
        command = self.commands.down(compose_file)
        return self.executor.execute(command)
