from typing import Optional, Self

from ...command_executor import CommandExecutor
from ...commands.base.podman_commands import PodmanCommands
from ...commands.ubuntu.file_commands_ubuntu import FileCommandsUbuntu
from ...types.compose_project import ComposeProject
from ...types.exec_result import ExecResult
from .file import File
from .os_resource_base import OsResourceBase


class Podman(OsResourceBase):

    def __init__(self: Self, commands: PodmanCommands, executor: CommandExecutor):
        super().__init__(commands=commands, executor=executor)
        self._commands: PodmanCommands = commands
        self._executor: CommandExecutor = executor
        self._file_cmds = FileCommandsUbuntu(cpu_arch=commands.cpu_arch)

    def compose_up(self: Self, compose_file: str) -> ExecResult:
        return self._executor.execute(self._commands.compose_up(compose_file))

    def compose_down(self: Self, compose_file: str) -> ExecResult:
        return self._executor.execute(self._commands.compose_down(compose_file))

    def list_networks(self, filter_name: Optional[str] = None) -> ExecResult:
        """
        Lists all networks or networks matching a filter.
        Returns the raw ExecResult with network list.
        """
        return self._executor.execute(self._commands.network_ls(filter_name))

    def build(
        self,
        containerfile: Optional[str] = None,
        context: Optional[str] = ".",
        tags: Optional[list[str]] = None,
        no_cache: bool = False,
    ) -> ExecResult:
        """
        Build a container image using Podman.
        Args:
            containerfile: Path to the container file (defaults to look for `DockerFile` or `ContainerFile` in the `context` directory)
            context: Build context (default: current directory)
            tag: Tag for the image (default: None)
            no_cache: If True, build without using cache i.e. force build using --no-cache arg (default: False)
        """
        return self._executor.execute(
            self._commands.build(
                containerfile=containerfile,
                context=context,
                tags=tags,
                no_cache=no_cache,
            )
        )

    def enable_sockets(self) -> ExecResult:
        """
        Enable Podman sockets for systemd.
        This allows Podman to be used as a systemd service.
        Returns:
            ExecResult: The result of the command execution.
        """
        # enableSocketCmd: RunnableCommandString = PodmanCommandsUbuntu().enable_socket()
        # self._executor.execute(command=enableSocketCmd)

        return self._executor.execute(self._commands.enable_socket())

    def load_compose_file(self, compose_file_path: str) -> ComposeProject:
        """
        Load a Docker Compose YAML file from disk.
        Args:
            compose_file_path: The path to the Docker Compose YAML file.
        Returns:
            ComposeProject: The parsed compose project as a structured data class.
        """

        compose_file = File(
            commands=self._file_cmds,
            executor=self.executor,
            path=compose_file_path,
        )
        compose_file_read_result: ExecResult = compose_file.open_read()

        if compose_file_read_result.stdout is not None:

            compose_project = ComposeProject.from_compose_yaml(
                compose_yaml=compose_file_read_result.stdout
            )
            return compose_project
        else:
            raise ValueError(
                f"Failed to read compose file {compose_file_path}: {compose_file_read_result.stderr}"
            )

    @staticmethod
    def compose_to_quadlet(
        compose_project: ComposeProject, ignore_ports: bool = False
    ) -> dict[str, str]:
        """
        Convert a Docker Compose project to Podman Quadlet unit files.
        Args:
            compose_project: The ComposeProject instance to convert.
            ignore_ports: If True, skip processing 'ports:' sections (for reverse-proxy-first apps)
        Returns:
            dict[str, str]: A dictionary with filenames as keys and file contents as values . The filenames follow the systemd convention of <service name>.container, <network name>.network, <volume name>.volume.
        """
        results: dict[str, str] = {}

        # Services -> .container files
        for svc_name, svc in compose_project.services.items():
            # Build systemd dependencies
            after_dependencies = []
            requires_dependencies = []

            # Add network dependencies (containers depend on their networks)
            for net in svc.networks:
                network_obj = compose_project.networks[net]
                systemd_net_name = network_obj.systemd_network_name()
                # Fix: Use the correct systemd service naming convention for networks
                # Podman Quadlet generates network services with "-network.service" suffix
                network_service_name = f"{compose_project.name}__{net}-network.service"
                after_dependencies.append(network_service_name)
                requires_dependencies.append(network_service_name)

            # Add service dependencies from depends_on
            for dep_service in svc.depends_on:
                dep_service_name = f"{compose_project.name}__{dep_service}.service"
                after_dependencies.append(dep_service_name)
                requires_dependencies.append(dep_service_name)

            container_unit: list[str] = [
                "[Unit]",
                f"Description={svc_name} container",
            ]

            # Add systemd dependencies if any exist
            if after_dependencies:
                container_unit.append(f"After={' '.join(after_dependencies)}")
            if requires_dependencies:
                container_unit.append(f"Requires={' '.join(requires_dependencies)}")

            container_unit.extend(
                [
                    "",
                    "[Container]",
                    f"Image={svc.image}",
                ]
            )

            # User
            if svc.user:
                container_unit.append(f"User={svc.user}")

            # Ports (only if not ignoring)
            if not ignore_ports:
                for port in svc.ports:
                    container_unit.append(f"PublishPort={port}")

            # Environment
            if svc.environment:
                if isinstance(svc.environment, dict):
                    envs = [f"{k}={v}" for k, v in svc.environment.items()]
                else:
                    envs = svc.environment
                for env in envs:
                    container_unit.append(f"Environment={env}")

            # Volumes
            for vol in svc.volumes:
                container_unit.append(f"Volume={vol}")

            # Networks
            for net in svc.networks:
                # Use systemd network naming convention for network references
                network_obj = compose_project.networks[net]
                systemd_net_name = network_obj.systemd_network_name()
                container_unit.append(f"Network={systemd_net_name}")

            # Labels - convert dict format to "key=value" strings
            if svc.labels:
                for key, value in svc.labels.items():
                    container_unit.append(f"Label={key}={value}")

            # tells systemd what target to symlink the unit into for autostart given transient unit files
            container_unit.append("[Install]")
            container_unit.append("WantedBy=default.target")

            results[f"{svc_name}.container"] = "\n".join(container_unit) + "\n"

        # Networks -> .network files
        for net_name, net in compose_project.networks.items():
            network_unit = [
                "[Unit]",
                f"Description={net_name} network",
                "",
                "[Network]",
            ]
            if net.driver:
                network_unit.append(f"Driver={net.driver}")

            # tells systemd what target to symlink the unit into for autostart given transient unit files
            network_unit.append("[Install]")
            network_unit.append("WantedBy=default.target")

            results[f"{net_name}.network"] = "\n".join(network_unit) + "\n"

        # Volumes -> .volume files
        for vol_name, vol in compose_project.volumes.items():
            volume_unit = [
                "[Unit]",
                f"Description={vol_name} volume",
                "",
                "[Volume]",
            ]
            # tells systemd what target to symlink the unit into for autostart given transient unit files
            volume_unit.append("[Install]")
            volume_unit.append("WantedBy=default.target")

            results[f"{vol_name}.volume"] = "\n".join(volume_unit) + "\n"

        return results

    def ps(
        self: Self, all_containers: bool = False, format_output: Optional[str] = None
    ) -> ExecResult:
        """List containers."""
        return self._executor.execute(
            self._commands.ps(
                all_containers=all_containers, format_output=format_output
            )
        )

    def version(self: Self) -> ExecResult:
        return self._executor.execute(self._commands.version())
