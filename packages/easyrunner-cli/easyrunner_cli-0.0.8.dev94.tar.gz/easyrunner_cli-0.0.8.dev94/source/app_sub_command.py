import logging
from typing import List, Optional, Self

from rich.console import Console
from rich.table import Table
from typer import Argument, Option, Typer, echo, style

from easyrunner import Ssh

# Absolute imports for external packages/projects
from easyrunner.source.command_executor import CommandExecutor
from easyrunner.source.commands.ubuntu.caddy_commands_container_ubuntu import (
    CaddyCommandsContainerUbuntu,
)
from easyrunner.source.resources.os_resources import Caddy, HostServerUbuntu
from easyrunner.source.store.data_models.app import App
from easyrunner.source.store.data_models.server import Server
from easyrunner.source.store.easyrunner_store import EasyRunnerStore
from easyrunner.source.types.cpu_arch_types import CpuArch

# Relative import for internal modules
from . import logger
from .auth.github_token_manager import GitHubTokenManager
from .ssh_config import (
    build_private_key_path,
    ssh_config,
)

name_help_str: str = "The friendly name of the server to select."

NAME_ARG: str = Argument(
    default=..., help="The friendly name of the application to select."
)
SERVER_NAME_ARG: str = Argument(default=..., help=name_help_str)
SERVER_NAME_OPTION: Optional[str] = Option(default=None, help=f"{name_help_str}")


class AppSubCommand:
    typer_app: Typer = Typer(
        name="app",
        no_args_is_help=True,
        rich_markup_mode="rich",
        help="[bold green]Commands[/bold green] for managing applications.",
    )
    debug: bool = False
    silent: bool = False

    _store: EasyRunnerStore = EasyRunnerStore()

    _console: Console = Console()

    # Shorter alias for console printing
    _print = _console.print

    # Define progress callback with CLI-specific formatting
    @staticmethod
    def _progress_callback(message: str, end: str) -> None:
        if not AppSubCommand.silent:
            AppSubCommand._print(message, end=end)

    def __init__(self: Self) -> None:
        self.apps = []

        @self.typer_app.callback(invoke_without_command=True)
        def set_global_options(  # type: ignore
            debug: bool = Option(
                False,
                "--debug",
                help="Enables extra debug messages to be output. Independent of --silent.",
                rich_help_panel="Global Options",
            ),
            silent: bool = Option(
                False,
                "--silent",
                help="Suppresses all output messages.",
                rich_help_panel="Global Options",
            ),
        ) -> None:
            AppSubCommand.debug = debug
            AppSubCommand.silent = silent
            if debug:
                # Set root logger to DEBUG level which affects all loggers
                logger.setLevel(logging.DEBUG)
            elif silent:
                # Set root logger to ERROR level which affects all loggers
                logger.setLevel(logging.ERROR)

    @typer_app.command(
        name="deploy",
        help="Deploys the application to the server.",
        no_args_is_help=True,
    )
    @staticmethod
    def app_deploy(
        name: str = NAME_ARG,
        server_name: str = SERVER_NAME_ARG,
    ) -> None:

        try:
            server: Server | None = AppSubCommand._store.get_server_by_name(
                name=server_name
            )
            if not server:
                AppSubCommand._print(f"Server with name '{server_name}' not found.")
                return
            app = next((app for app in server.apps if app.name == name), None)
            if not app:
                AppSubCommand._print(
                    f"App with name '{name}' not found on server '{server_name}'."
                )
                return

            if not app.custom_domain:
                AppSubCommand._print(
                    f"App with name '{name}' must have a custom domain name set because this is used to uniquely identify this app in configuration. The custom domain name must be unique amongst all the apps on each server."
                )
                return

            hostname_or_ipv4: str = server.hostname_or_ip

            # Initial deployment info
            AppSubCommand._print("🚀 [bold blue]Starting deployment...[/bold blue]")

            # Get GitHub access token from keyring for automatic deploy key management
            token_manager = GitHubTokenManager()
            github_access_token = token_manager.get_token()
            if not github_access_token:
                AppSubCommand._print(
                    "❌ No GitHub token found. Please run 'er auth login github' first."
                )
                return

            with Ssh(
                hostname_or_ipv4=hostname_or_ipv4,
                username=ssh_config.username,
                key_filename=build_private_key_path(hostname_or_ipv4),
                debug=AppSubCommand.debug,
                silent=AppSubCommand.silent,
            ) as ssh_client:
                executor = CommandExecutor(ssh_client=ssh_client)
                host_server_instance = HostServerUbuntu(
                    easyrunner_username=ssh_config.username,
                    executor=executor,
                    debug=AppSubCommand.debug,
                    silent=AppSubCommand.silent,
                    progress_callback=AppSubCommand._progress_callback,
                )

                host_server_instance.deploy_app_flow_a(
                    repo_url=app.repo_url,
                    custom_app_domain_name=app.custom_domain,
                    github_access_token=github_access_token,
                )
        except Exception as e:
            AppSubCommand._print(
                f"[red]Oops, something went wrong while deploying the app:[/red] {str(e)}"
            )

    @typer_app.command(
        name="start",
        help="Starts the application on the server.",
        no_args_is_help=True,
    )
    @staticmethod
    def app_start(
        hostname_or_ipv4: str,
        repo_name: str,
    ) -> None:
        """
        Starts the application on the server.
        """
        with Ssh(
            hostname_or_ipv4=hostname_or_ipv4,
            username=ssh_config.username,
            key_filename=build_private_key_path(hostname_or_ipv4=hostname_or_ipv4),
            debug=AppSubCommand.debug,
            silent=AppSubCommand.silent,
        ) as ssh_client:
            executor = CommandExecutor(ssh_client=ssh_client)
            host_server_instance = HostServerUbuntu(
                easyrunner_username=ssh_config.username,
                executor=executor,
                debug=AppSubCommand.debug,
                silent=AppSubCommand.silent,
            )

            host_server_instance.start_application_compose(
                repo_name=repo_name,
            )

    @typer_app.command(
        name="stop",
        help="Stops the application on the server.",
        no_args_is_help=True,
    )
    @staticmethod
    def app_stop(
        hostname_or_ipv4: str,
        repo_name: str,
    ) -> None:
        """
        Stops the application on the server.
        """
        with Ssh(
            hostname_or_ipv4=hostname_or_ipv4,
            username=ssh_config.username,
            key_filename=build_private_key_path(hostname_or_ipv4=hostname_or_ipv4),
            debug=AppSubCommand.debug,
            silent=AppSubCommand.silent,
        ) as ssh_client:
            executor = CommandExecutor(ssh_client=ssh_client)
            host_server_instance = HostServerUbuntu(
                easyrunner_username=ssh_config.username,
                executor=executor,
                debug=AppSubCommand.debug,
                silent=AppSubCommand.silent,
            )

            host_server_instance.stop_application_compose(
                repo_name=repo_name,
            )

    @typer_app.command(
        name="list",
        help="List all applications on all servers.",
        no_args_is_help=False,
    )
    @staticmethod
    def list_servers(name: Optional[str] = SERVER_NAME_OPTION) -> None:
        servers: List[Server] = []
        if name:
            server: Server | None = AppSubCommand._store.get_server_by_name(name=name)
            if server:
                servers.append(server)
            else:
                echo(message=f"Server with name '{name}' not found.")

        else:
            servers = AppSubCommand._store.list_servers()

        total_servers: int = len(servers)
        total_apps: int = sum(len(server.apps) for server in servers)

        # Create a table for displaying apps
        table = Table(title="Applications")
        table.add_column("App Name", style="cyan", no_wrap=True)
        table.add_column("Server Name", style="green")
        table.add_column("Description", style="dim")
        table.add_column("Custom Domain", style="magenta")
        table.add_column("Repository", style="blue")

        for server in servers:
            for app in server.apps:
                table.add_row(
                    app.name,
                    server.name,
                    app.description or "",
                    app.custom_domain or "",
                    app.repo_url,
                )

        AppSubCommand._print(table)
        AppSubCommand._print(
            f"\nTotal Servers: {total_servers}, Total Apps: {total_apps}\n\n", end="\n"
        )

    @typer_app.command(
        name="add",
        help="Add a new application to the server.",
        no_args_is_help=True,
    )
    @staticmethod
    def add_app(
        name: str = NAME_ARG,
        server_name: str = SERVER_NAME_ARG,
        description: str = Option(
            default="",
            help="A short description of the application.",
        ),
        custom_domain: Optional[str] = Option(
            default=None,
            help="The custom domain the application will be accessible at. Configure the hostname header matching on Caddy server.",
        ),
        repo_url: str = Argument(
            default=...,
            help="The HTTPS URL of the application repository. Currently only supports GitHub repositories.",
        ),
    ) -> None:
        server: Server | None = AppSubCommand._store.get_server_by_name(
            name=server_name
        )
        if not server:
            echo(message=f"Server with name '{server_name}' not found.")
            return

        if not any(app.name == name for app in server.apps):
            server.apps.append(
                App(
                    name=name,
                    repo_url=repo_url,
                    description=description,
                    custom_domain=custom_domain,
                )
            )
            AppSubCommand._store.update_server(server=server)
            echo(message=f"App '{name}' added to server '{server.name}'.")
        else:
            echo(
                message=f"App with name '{name}' already exists on server '{server_name}'."
            )

    @typer_app.command(
        name="remove",
        help="Remove an application from the server.",
        no_args_is_help=True,
    )
    @staticmethod
    def remove_app(
        name: str = NAME_ARG,
        server_name: str = SERVER_NAME_ARG,
    ) -> None:
        server: Server | None = AppSubCommand._store.get_server_by_name(
            name=server_name
        )
        if not server:
            echo(message=f"Server with name '{server_name}' not found.")
            return

        app_to_remove: App | None = next(
            (app for app in server.apps if app.name == name), None
        )
        if app_to_remove:
            server.apps.remove(app_to_remove)
            AppSubCommand._store.update_server(server=server)
            echo(message=f"App '{name}' removed from server '{server.name}'.")
        else:
            echo(message=f"App with name '{name}' not found on server '{server_name}'.")

    @typer_app.command(
        name="update-details",
        help="Update an existing application on the server.",
        no_args_is_help=True,
    )
    @staticmethod
    def update_app_details(
        name: str = NAME_ARG,
        server_name: str = SERVER_NAME_ARG,
        app_name: Optional[str] = Option(
            default=None,
            help="The friendly name of the application.",
        ),
        description: Optional[str] = Option(
            default=None,
            help="A short description of the application.",
        ),
        custom_domain: Optional[str] = Option(
            default=None,
            help="The custom domain the application will be accessible at. Configures the hostname header matching on Caddy server. Changes only apply the next time the app is deployed.",
        ),
        repo_url: Optional[str] = Option(
            default=None,
            help="The SSH URL of the application repository. Currently only supports GitHub repositories and SSH.",
        ),
    ) -> None:
        server: Server | None = AppSubCommand._store.get_server_by_name(
            name=server_name
        )
        if not server:
            echo(message=f"Server with name '{server_name}' not found.")
            return

        app: App | None = next((app for app in server.apps if app.name == name), None)
        if app:
            app.repo_url = repo_url if repo_url else app.repo_url
            app.name = app_name if app_name else app.name
            app.description = description if description else app.description
            app.custom_domain = custom_domain if custom_domain else app.custom_domain
            AppSubCommand._store.update_server(server=server)
            echo(message=f"App '{name}' updated on server '{server.name}'.")
        else:
            echo(message=f"App with name '{name}' not found on server '{server_name}'.")

    @typer_app.command(
        name="status",
        help="Show the status of an application's container on the server.",
        no_args_is_help=True,
    )
    @staticmethod
    def app_status(
        name: str = NAME_ARG,
        server_name: str = SERVER_NAME_ARG,
    ) -> None:
        try:
            server: Server | None = AppSubCommand._store.get_server_by_name(
                name=server_name
            )
            if not server:
                echo(message=f"Server with name '{server_name}' not found.")
                return
            app = next((app for app in server.apps if app.name == name), None)
            if not app:
                echo(
                    message=f"App with name '{name}' not found on server '{server_name}'."
                )
                return

            hostname_or_ipv4: str = server.hostname_or_ip

            with Ssh(
                hostname_or_ipv4=hostname_or_ipv4,
                username=ssh_config.username,
                key_filename=build_private_key_path(hostname_or_ipv4),
                debug=AppSubCommand.debug,
                silent=AppSubCommand.silent,
            ) as ssh_client:
                executor = CommandExecutor(ssh_client=ssh_client)
                host_server = HostServerUbuntu(
                    easyrunner_username=ssh_config.username,
                    executor=executor,
                    debug=AppSubCommand.debug,
                    silent=AppSubCommand.silent,
                )

                # Get app repository name from URL
                repo_name = app.repo_url.split("/")[-1].replace(".git", "")

                # Check if app is running using HostServerUbuntu resource
                app_running = host_server.is_app_running(repo_name)

                # Get container names for deployment status check
                container_names = host_server.get_app_container_names(repo_name)

                if app_running:
                    echo("🟢 App Status: Running")
                    if AppSubCommand.debug:
                        # Get running container details for debug output
                        running_containers = host_server.get_app_running_containers(
                            repo_name
                        )
                        for container_detail in running_containers:
                            echo(f"   {container_detail}")
                elif container_names:
                    echo("🔴 App Status: Not running")
                    echo("   Use 'er app deploy' to start the application")
                else:
                    echo("🔴 App Status: Not deployed")
                    echo("   Use 'er app deploy' to deploy the application")

                # Show detailed systemd service status only in debug mode
                if AppSubCommand.debug:
                    echo()
                    echo("=== Debug Information ===")

                    # Get service names using helper method
                    service_names = host_server.get_app_service_names(repo_name)

                    if service_names:
                        echo(f"SystemD Services ({len(service_names)}):")
                        for service_name in service_names:
                            echo(f"  • {service_name}")
                    else:
                        echo("No SystemD services found for this app")

                    if container_names:
                        echo(f"Containers ({len(container_names)}):")
                        for container_name in container_names:
                            echo(f"  • {container_name}")
                    else:
                        echo("No containers found for this app")

        except Exception as e:
            echo(
                message=f"Oops, something went wrong while checking app status: {str(e)}",
                err=True,
            )

    @typer_app.command(
        name="show-details",
        help="Show details of an application on the server.",
        no_args_is_help=True,
    )
    @staticmethod
    def app_show_details(
        name: str = NAME_ARG,
        server_name: str = SERVER_NAME_ARG,
    ) -> None:
        server: Server | None = AppSubCommand._store.get_server_by_name(
            name=server_name
        )
        if not server:
            echo(message=f"Server with name '{server_name}' not found.")
            return

        app: App | None = next((app for app in server.apps if app.name == name), None)
        if app:
            echo()
            for attr_name in app.__dict__:
                attr_value = getattr(app, attr_name)
                # Convert attribute name from snake_case to Title Case for display
                display_name = attr_name.replace("_", " ").title()
                echo(message=f"{display_name}: {attr_value}", color=True)

            echo(message=f"Server Name: {server.name}", color=True)
            echo(message=f"Server Hostname/IP: {server.hostname_or_ip}", color=True)
        else:
            echo()
            echo(
                message=f"App with name '{name}' not found on server '{server_name}'.",
                color=True,
            )
        echo()

    @typer_app.command(
        name="test",
        help="Test the application.",
    )
    @staticmethod
    def app_test(server_name: str = SERVER_NAME_ARG) -> None:
        """
        A simple test command to verify that the AppSubCommand is working.
        """
        server: Server | None = AppSubCommand._store.get_server_by_name(
            name=server_name
        )
        if not server:
            echo(message=f"Server with name '{server_name}' not found.")
            return

        hostname_or_ipv4: str = server.hostname_or_ip
        with Ssh(
            hostname_or_ipv4=hostname_or_ipv4,
            username=ssh_config.username,
            key_filename=build_private_key_path(hostname_or_ipv4=hostname_or_ipv4),
            debug=AppSubCommand.debug,
            silent=AppSubCommand.silent,
        ) as ssh_client:
            executor = CommandExecutor(ssh_client=ssh_client)

            echo(message="AppSubCommand is working!", color=True)
            caddy: Caddy = Caddy(
                commands=CaddyCommandsContainerUbuntu(cpu_arch=CpuArch.X86_64),
                executor=executor,
            )

            result1 = caddy.get_server_config("svr0")

            echo(
                message=style(f"Server Config for 'svr0': {repr(result1)}", fg="green"),
                color=True,
            )

            result2 = caddy.server_exists("svr0")

            echo(
                message=style(f"Server 'svr0' exists: {repr(result2)}", fg="green"),
                color=True,
            )
