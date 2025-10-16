import logging
import os
from typing import List, Optional, Self

from rich.console import Console
from rich.table import Table
from typer import Argument, Option, Typer, echo

from easyrunner import Ssh
from easyrunner.source.cloud_providers.cloud_providers import CloudProviders

# Absolute imports for external packages/projects
from easyrunner.source.command_executor import CommandExecutor
from easyrunner.source.command_executor_local import CommandExecutorLocal
from easyrunner.source.commands.base.ssh_keygen_commands import SshKeygenCommands
from easyrunner.source.commands.runnable_command_string import RunnableCommandString
from easyrunner.source.known_host_ssh_keys import KNOWN_HOST_SSH_KEYS
from easyrunner.source.resources.cloud_resources.hetzner import HetznerStack
from easyrunner.source.resources.os_resources import HostServerUbuntu
from easyrunner.source.resources.web_security_scanner import WebSecurityScanner
from easyrunner.source.ssh import with_ssh_retry
from easyrunner.source.store import EasyRunnerStore
from easyrunner.source.store.data_models import Server
from easyrunner.source.types.cpu_arch_types import CpuArch
from easyrunner.source.types.exec_result import ExecResult
from easyrunner.source.types.os_type import OS

# Relative import for internal modules
from . import logger
from .infrastructure_deps import InfrastructureDependencies
from .licensing import LicenseManager
from .ssh_config import (
    build_github_private_key_filename,
    build_github_private_key_path,
    build_github_public_key_path,
    build_private_key_filename,
    build_private_key_path,
    build_public_key_path,
    ssh_config,
)

# shared typer command arguments and options
ADDRESS_ARG: str = Argument(
    default=..., help="The hostname or IPv4 address of the remote server."
)

NAME_ARG: str = Argument(default=..., help="The friendly name of the server.")

CLOUD_PROVIDER_ARG: CloudProviders = Argument(
    default=..., help="The cloud provider to use for creating the server."
)

class ServerSubCommand:
    typer_app: Typer = Typer(
        name="server",
        no_args_is_help=True,
        rich_markup_mode="rich",
        help="[bold blue]EasyRunner[/bold blue] commands for managing a server. Prepare a server for app hosting by adding it to EasyRunner and initialising it with the EasyRunner stack. \n\n Copyright (c) 2024 - 2025 Janaka Abeywardhana",
    )
    debug: bool = False
    silent: bool = False

    _store: EasyRunnerStore = EasyRunnerStore()
    _console: Console = Console()

    # Shorter alias for console printing
    _print = _console.print

    # Define progress callback with CLI-specific formatting
    @staticmethod
    def _progress_callback(message: str, end: str = "\n") -> None:
        if not ServerSubCommand.silent:
            ServerSubCommand._print(message, end=end)

    @staticmethod
    def _check_server_limit() -> bool:
        """
        Check if adding a new server would exceed the license limit.

        Returns:
            True if within limit or no limit applies, False if limit exceeded

        Displays error message to user if limit is exceeded.
        """
        # Get license info
        manager = LicenseManager()
        license_info = manager.get_license_info()

        if license_info is None:
            # This shouldn't happen as main.py checks license on startup
            # But handle it gracefully just in case
            ServerSubCommand._print(
                "[red]Error:[/red] No valid license found. Run [cyan]er license status[/cyan] for details."
            )
            return False

        # Get current server count
        current_servers = ServerSubCommand._store.list_servers()
        current_count = len(current_servers)

        # Check if we're at or over the limit
        if current_count >= license_info.server_limit:
            ServerSubCommand._print()
            ServerSubCommand._print(f"[red]✗ Server limit reached[/red]")
            ServerSubCommand._print()
            ServerSubCommand._print(
                f"Your license allows [bold]{license_info.server_limit}[/bold] server(s)."
            )
            ServerSubCommand._print(
                f"You currently have [bold]{current_count}[/bold] server(s) registered."
            )
            ServerSubCommand._print()
            ServerSubCommand._print("To add more servers:")
            ServerSubCommand._print(
                "  • Remove an existing server: [cyan]er server remove <name>[/cyan]"
            )
            ServerSubCommand._print(
                "  • Upgrade your license at [link]https://easyrunner.xyz[/link]"
            )
            ServerSubCommand._print()
            return False

        return True

    @staticmethod
    def _cleanup_ssh_keys(hostname_or_ip: str) -> None:
        """
        Helper method to remove SSH key files for a server from the local client machine.
        Cleans up known_hosts files also.

        Args:
            hostname_or_ip: The hostname or IP address of the server
        """
        private_key_path: str = build_private_key_path(hostname_or_ip)
        public_key_path: str = build_public_key_path(hostname_or_ip)

        if os.path.exists(private_key_path):
            os.remove(private_key_path)
            echo(message=f"Removed private SSH key: {private_key_path}")

        if os.path.exists(public_key_path):
            os.remove(public_key_path)
            echo(message=f"Removed public SSH key: {public_key_path}")

        # Clean up GitHub SSH keys if they exist
        github_private_key_path: str = build_github_private_key_path(hostname_or_ip)
        github_public_key_path: str = build_github_public_key_path(hostname_or_ip)

        if os.path.exists(github_private_key_path):
            os.remove(github_private_key_path)
            echo(message=f"Removed GitHub private SSH key: {github_private_key_path}")
        else:
            echo(
                message=f"No GitHub private SSH key present to remove for {hostname_or_ip}"
            )

        if os.path.exists(github_public_key_path):
            os.remove(github_public_key_path)
            echo(message=f"Removed GitHub public SSH key: {github_public_key_path}")
        else:
            echo(
                message=f"No GitHub public SSH key present to remove for {hostname_or_ip}"
            )

        executor = CommandExecutorLocal()
        ssh_keygen = SshKeygenCommands(os=OS.UBUNTU, cpu_arch=CpuArch.X86_64)
        # Remove the host key from known hosts file on the client machine
        remove_host_key_cmd = ssh_keygen.remove_host_key(hostname_or_ip)
        result = executor.execute(remove_host_key_cmd)

        if result.success:
            echo(
                message=f"Removed host key for {hostname_or_ip} from local known_hosts"
            )
        else:
            echo(
                message=f"Failed to remove host key for {hostname_or_ip} from known_hosts. Error: {result.stderr}"
            )

    @staticmethod
    def _add_server_to_store(name: str, hostname_or_ip: str) -> Server | None:
        """
        Helper method to validate and add a server to the EasyRunner store.

        Args:
            name: The friendly name of the server
            hostname_or_ip: The hostname or IP address of the server

        Returns:
            Server object if successfully added, None if validation failed
        """
        # Check if server name already exists
        server_name_exists: Server | None = ServerSubCommand._store.get_server_by_name(
            name=name
        )
        if server_name_exists:
            ServerSubCommand._print(
                f"⚠️  Server with the name '[bold yellow]{server_name_exists.name}[/bold yellow]' already exists in EasyRunner."
            )
            return None

        # Check if server address already exists
        server_address_exists: Server | None = (
            ServerSubCommand._store.get_server_by_hostname_or_ip(
                hostname_or_ip=hostname_or_ip
            )
        )
        if server_address_exists:
            ServerSubCommand._print(
                f"⚠️  Server with the address '[bold yellow]{server_address_exists.hostname_or_ip}[/bold yellow]' already exists in EasyRunner."
            )
            return None

        # Create and persist the server
        server: Server = Server(
            name=name,
            hostname_or_ip=hostname_or_ip,
        )
        ServerSubCommand._store.add_server(server=server)
        ServerSubCommand._print(
            f"✅ Server [bold green]{server.name}[/bold green]([italic cyan]{server.hostname_or_ip}[/italic cyan]) added to EasyRunner."
        )
        return server

    @staticmethod
    def _cancel_stack(name: str, cloud_provider_name: CloudProviders) -> None:
        """
        Helper method to cancel any running operation and unlock a server stack.

        This is useful when a stack is locked due to a previous operation that didn't complete properly.

        Args:
            name: The server name
            cloud_provider_name: The cloud provider
        """
        # Check and install infrastructure dependencies first
        deps_result = InfrastructureDependencies.ensure_cloud_tools_available()
        if not deps_result.success:
            echo(message=f"Error: {deps_result.stderr}")
            return

        if cloud_provider_name == CloudProviders.HETZNER.value:
            from easyrunner.source.cloud_providers.hetzner_provider import (
                HetznerProvider,
            )

            stack_name = f"{name}-stack"
            provider = HetznerProvider.from_env()
            stack = HetznerStack(
                stack_name=stack_name,
                provider=provider,
            )
            result = stack.cancel()

            if result.success:
                echo(
                    message=f"Stack '{stack_name}' cancelled and unlocked successfully."
                )
            else:
                echo(message=f"Failed to cancel stack '{stack_name}': {result.stderr}")

    @staticmethod
    def _refresh_stack(name: str, cloud_provider_name: CloudProviders) -> None:
        """
        Helper method to refresh a stack's state to match the actual cloud provider state.

        This syncs Pulumi's state with what actually exists in the cloud provider.
        Useful when resources were manually deleted or operations were interrupted.

        Args:
            name: The server name
            cloud_provider_name: The cloud provider
        """
        # Check and install infrastructure dependencies first
        deps_result = InfrastructureDependencies.ensure_cloud_tools_available()
        if not deps_result.success:
            echo(message=f"Error: {deps_result.stderr}")
            return

        if cloud_provider_name == CloudProviders.HETZNER.value:
            from easyrunner.source.cloud_providers.hetzner_provider import (
                HetznerProvider,
            )

            stack_name = f"{name}-stack"
            provider = HetznerProvider.from_env()
            stack = HetznerStack(
                stack_name=stack_name,
                provider=provider,
            )
            result = stack.refresh()

            if result.success:
                echo(message=f"Stack '{stack_name}' state refreshed successfully.")
            else:
                echo(message=f"Failed to refresh stack '{stack_name}': {result.stderr}")

    def __init__(self: Self) -> None:
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
            ServerSubCommand.debug = debug
            ServerSubCommand.silent = silent
            if debug:
                # Set root logger to DEBUG level which affects all loggers
                logger.setLevel(logging.DEBUG)
            elif silent:
                # Set root logger to ERROR level which affects all loggers
                logger.setLevel(logging.ERROR)

    @typer_app.command(
        name="verify", help="Verify the server setup.", no_args_is_help=True
    )
    @staticmethod
    def verify_server(
        name: str = NAME_ARG,
        include_security_scan: bool = Option(
            False,
            "--include-security-scan",
            help="Include web application security scanning for information disclosure."
        )
    ) -> None:
        server = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            ServerSubCommand._print(
                f"[red]✗ Server [bold]{name}[/bold] not found in EasyRunner.[/red]"
            )
            return

        try:
            with Ssh(
                hostname_or_ipv4=server.hostname_or_ip,
                username=ssh_config.username,  # "azureuser",
                key_filename=build_private_key_path(
                    server.hostname_or_ip
                ),  # "~/.ssh/janaka_dev_key",
                debug=ServerSubCommand.debug,
                silent=ServerSubCommand.silent,
            ) as ssh_client:
                executor = CommandExecutor(ssh_client=ssh_client)

                # Create local executor for external connectivity tests
                local_executor = CommandExecutorLocal(
                    debug=ServerSubCommand.debug, silent=ServerSubCommand.silent
                )

                host_server_instance = HostServerUbuntu(
                    easyrunner_username=ssh_config.username,
                    executor=executor,
                    debug=ServerSubCommand.debug,
                    silent=ServerSubCommand.silent,
                    progress_callback=ServerSubCommand._progress_callback,
                )
                if ServerSubCommand.silent:
                    host_server_instance.is_easyrunner_installed()
                else:
                    # Run standard server verification
                    host_server_instance.verify_server_setup()

                    # Run CLI-specific firewall connectivity tests
                    ServerSubCommand._verify_firewall_external_connectivity(
                        server.hostname_or_ip, executor, local_executor
                    )

                    # Run optional security scanning
                    if include_security_scan:
                        try:
                            ServerSubCommand._print("\n🔍 WEB APPLICATION SECURITY SCAN")

                            scanner = WebSecurityScanner(
                                executor=local_executor,
                                progress_callback=ServerSubCommand._progress_callback
                            )
                            scan_results = scanner.scan_server_apps(server)

                            # Display brief summary for verify command
                            total_failed = sum(result.failed_checks for result in scan_results)
                            total_critical_high = sum(
                                result.summary.get("critical", 0) + result.summary.get("high", 0) 
                                for result in scan_results
                            )

                            if total_failed == 0:
                                ServerSubCommand._print(" [green]✔[/green] No information disclosure vulnerabilities detected")
                            else:
                                if total_critical_high > 0:
                                    ServerSubCommand._print(f" [red]✗[/red] {total_failed} security issues found ({total_critical_high} critical/high)")
                                else:
                                    ServerSubCommand._print(f" [yellow]⚠[/yellow] {total_failed} security issues found (medium/low)")

                                ServerSubCommand._print("   Run 'er server security-scan' for detailed results")

                        except Exception as scan_error:
                            ServerSubCommand._print(f" [red]✗[/red] Security scan failed: {scan_error}")

                echo("")  # Final newline
        except ConnectionError as connection_error:
            echo(
                message=f"Failed to connect to the server {name} at {server.hostname_or_ip}. Please check your connectivity to the server, that the server is up, the IP/hostname address is still valid etc. Make sure you have initialised the server by running the `er server init` command. Error: {connection_error}",
                err=True,
            )
            return
        except Exception as e:
            echo(
                message=f"Oops, something went wrong while verifying the server. Run the command again with options --debug or --silent for more information. Error: {e}",
                err=True,
            )

    @typer_app.command(
        name="add",
        help="Register the server in EasyRunner and generates an SSH key pair for it.",
        no_args_is_help=True,
    )
    @staticmethod
    def add_server(
        name: str = Argument(
            ...,
            help="The friendly name used to identify this server. Should be unique. You'll be using this name to reference this server in other commands.",
        ),
        address: str = ADDRESS_ARG,
    ) -> None:

        # Check server limit before adding
        if not ServerSubCommand._check_server_limit():
            return

        server = ServerSubCommand._store.get_server_by_name(name=name)

        if server:
            ServerSubCommand._print(
                f"⚠️  Server with the name '[bold yellow]{server.name}[/bold yellow]' already exists in EasyRunner. Use a different name."
            )
            return

        # Add server to EasyRunner store
        server: Server | None = ServerSubCommand._add_server_to_store(
            name=name, hostname_or_ip=address
        )
        if not server:
            return

        # Generate the SSH key pair for the server
        ServerSubCommand.gen_ssh_key(
            address=address,
            regenerate=False,
        )

        echo(
            message=f"SSH key pair generated for '{address}'. Add the above public key to the server via your VM providers web UI (see docs)."
        )

    @typer_app.command(
        name="init",
        help="Installs the EasyRunner stack on the server.",
        no_args_is_help=True,
    )
    @staticmethod
    @with_ssh_retry()
    def init_server(
        name: str = NAME_ARG,
        username: str = ssh_config.username,
    ) -> None:
        server: Server | None = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(
                f"Server with name: '{name}' not found in EasyRunner. Please add it first using the 'add' command."
            )
            return
        try:
            with Ssh(
                hostname_or_ipv4=server.hostname_or_ip,
                username=username,
                key_filename=build_private_key_path(
                    hostname_or_ipv4=server.hostname_or_ip
                ),
                debug=ServerSubCommand.debug,
                silent=ServerSubCommand.silent,
            ) as ssh_client:

                executor = CommandExecutor(ssh_client=ssh_client)

                host_server_instance = HostServerUbuntu(
                    easyrunner_username=ssh_config.username,
                    executor=executor,
                    debug=ServerSubCommand.debug,
                    silent=ServerSubCommand.silent,
                    progress_callback=ServerSubCommand._progress_callback,
                )

                from easyrunner.source.ssh_key import SshKey

                # Generate a new SSH key pair for the easyrunner ops user for each server being managed.
                # This is achieved by using the host servers hostname or IP address as the key name.
                # Use same filename sanitization as CLI commands to ensure consistency
                ssh_key = SshKey(
                    email=f"easyrunner@{server.hostname_or_ip}",
                    name=build_private_key_filename(server.hostname_or_ip),
                    ssh_key_dir=ssh_config.key_dir,
                    regenerate_if_exists=False,
                )

                # Ensure we have a valid key pair
                if not ssh_key.has_public_key():
                    ssh_key.generate_ed25519_keypair()
                    ssh_key.save_private_key()
                    ssh_key.save_public_key()

                if not host_server_instance.ensure_easyrunner_ops_user_is_setup(
                    ssh_key.public_key_as_string()
                ).success:
                    ServerSubCommand._progress_callback(
                        message=f"EasyRunner ops user setup failed for server {name}({server.hostname_or_ip}). Cannot proceed with setup."
                    )
                    return

                host_server_instance.install_easyrunner()

                # host_server_instance.add_ssh_key_to_user(
                #     username=ssh_config.username,
                #     ssh_public_key_content=ssh_key.public_key_as_string(),
                # )

                ServerSubCommand._progress_callback(
                    message=f"EasyRunner stack installed on server {name}({server.hostname_or_ip})."
                )

        except ConnectionError as connection_error:
            echo(
                message=f"Failed to connect to the server {name} at {server.hostname_or_ip}. Please check your connectivity to the server, that the server is up, the IP/hostname address is still valid etc. Make sure you have initialised the server by running the `er server init` command. Error: {connection_error}"
            )
            return
        except Exception as e:
            echo(
                message=f"Oops, something went wrong while installing EasyRunner on your server. Run the command again with options --debug or --silent for more information. Error: {e}"
            )

    @typer_app.command(
        name="update-details",
        help="Updates the server details in EasyRunner.",
        no_args_is_help=True,
    )
    @staticmethod
    def server_update_details(
        name: str = NAME_ARG,
        address: Optional[str] = None,
        server_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Updates the server details in the EasyRunner store.
        """
        server: Server | None = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(message=f"Server {name} not found in EasyRunner.")
            return

        # Update the server details
        if address:
            server.hostname_or_ip = address
        if server_name:
            server.name = server_name
        if description:
            server.description = description

        ServerSubCommand._store.update_server(server=server)
        echo(message=f"Server '{name}' updated.")

    @typer_app.command(
        "remove",
        help="Destructive. Removes a server from EasyRunner. Uninstalls EasyRunner stack and deployments.",
        no_args_is_help=True,
    )
    @staticmethod
    def remove_server(name: str = NAME_ARG) -> None:
        server = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(message=f"Server {name} not found in EasyRunner.")
            return

        # Remove SSH key files for the server
        ServerSubCommand._cleanup_ssh_keys(server.hostname_or_ip)

        # Remove the server from the store database
        ServerSubCommand._store.remove_server(server_id=server.id)

        echo(
            message=f"Server {server.name}({server.hostname_or_ip}) removed from EasyRunner."
        )

    @typer_app.command(
        name="create",
        help="Creates a new server in EasyRunner. This is a legacy command and will be removed in future versions.",
        no_args_is_help=True,
    )
    @staticmethod
    def create_server(
        name: str = NAME_ARG,
        cloud_provider_name: CloudProviders = CLOUD_PROVIDER_ARG,
        cancel: bool = Option(
            False,
            "--cancel",
            help="Cancel any running operation and unlock the server stack instead of creating.",
        ),
    ) -> None:
        """
        Spin up a new VM/VPS server in cloud provider account.
        """
        # If --cancel is provided, just cancel the stack and return
        if cancel:
            ServerSubCommand._cancel_stack(
                name=name, cloud_provider_name=cloud_provider_name
            )
            return

        # Check server limit before creating
        if not ServerSubCommand._check_server_limit():
            return

        if cloud_provider_name not in CloudProviders:
            ServerSubCommand._progress_callback(
                message=f"Invalid cloud provider '{cloud_provider_name}'. Supported providers: {', '.join([provider.value for provider in CloudProviders])}."
            )
            return

        server = ServerSubCommand._store.get_server_by_name(name=name)
        if server:
            ServerSubCommand._progress_callback(
                message=f"Server with the name '{server.name}' already exists in EasyRunner. Use a different name."
            )
            return

        # Check and install infrastructure dependencies first
        deps_result = InfrastructureDependencies.ensure_cloud_tools_available()
        if not deps_result.success:
            ServerSubCommand._progress_callback(
                message=f"[red]Error[/red]: {deps_result.stderr}"
            )
            return

        if cloud_provider_name == CloudProviders.HETZNER.value:
            from easyrunner.source.cloud_providers.hetzner_provider import (
                HetznerProvider,
            )

            provider = HetznerProvider.from_env()

            ServerSubCommand._progress_callback(
                message=f"Creating Hetzner VM with name: {name}:"
            )

            # Create firewall for the server first
            ServerSubCommand._progress_callback(
                message="[yellow]Creating firewall...[/yellow]"
            )
            from easyrunner.source.resources.cloud_resources.hetzner import (
                HetznerFirewall,
                HetznerStack,
            )
            from easyrunner.source.resources.cloud_resources.hetzner.hetzner_resource_factory import (
                HetznerResourceFactory,
            )
            from easyrunner.source.ssh_key import SshKey

            stack_name = f"{name}-stack"
            firewall_rules = HetznerResourceFactory.create_default_firewall_rules()
            firewall = HetznerFirewall(
                provider=provider,
                stack_name=stack_name,
                name=f"{name}-firewall",
                rules=firewall_rules,
            )

            ServerSubCommand._progress_callback(
                message="[yellow]Creating SSH key...[/yellow]"
            )

            ssh_key = SshKey(
                email=f"easyrunner@{name}",
                name=f"{name}_id_ed25519",
                ssh_key_dir=ssh_config.key_dir,
                regenerate_if_exists=False,
            )

            if not ssh_key.keys_exists:
                ssh_key.generate_ed25519_keypair()
                ssh_key.save_private_key()
                ssh_key.save_public_key()

            vm = HetznerResourceFactory.create_default_virtual_machine(
                name=name,
                provider=provider,
                stack_name=stack_name,
                ssh_public_key=ssh_key.public_key_as_string(),
            )
            vm.labels = {"project": "easyrunner", "environment": "dev"}
            vm.firewalls = [firewall]

            stack = HetznerStack(
                stack_name=stack_name,
                provider=provider,
            )

            # This gets the stack object, but doesn't run it
            pulumi_stack = stack.create_or_select_stack(vm_config=vm)

            # This runs the deployment (equivalent to `pulumi up`)
            result = pulumi_stack.up(on_output=echo)

            if not result.summary.result == "succeeded":
                ServerSubCommand._progress_callback(
                    message=f"[red]Failed to create Hetzner VM '{name}'.[/red] Error: {result.stderr}"
                )

                # Clean up VM stack since VM creation failed
                ServerSubCommand._progress_callback(message="Cleaning up VM stack...")
                stack_destroy_result = stack.destroy()
                if stack_destroy_result.success:
                    stack.remove()
                    ServerSubCommand._progress_callback(
                        message=f"[yellow]Cleaned up stack: {stack_name}[/yellow]"
                    )
                else:
                    ServerSubCommand._progress_callback(
                        message=f"[red]Warning: Failed to clean up stack {stack_name}: {stack_destroy_result.stderr}[/red]"
                    )

                # Clean up SSH keys since VM creation failed
                if os.path.exists(ssh_key.key_path):
                    os.remove(ssh_key.key_path)
                    ServerSubCommand._progress_callback(
                        message=f"Removed private SSH key: {ssh_key.key_path}"
                    )
                if os.path.exists(f"{ssh_key.key_path}.pub"):
                    os.remove(f"{ssh_key.key_path}.pub")
                    ServerSubCommand._progress_callback(
                        message=f"Removed public SSH key: {ssh_key.key_path}.pub"
                    )
                return

            ServerSubCommand._progress_callback(
                message=f"Hetzner VM created successfully: {name}"
            )

            # Type-safe dictionary access for successful results
            if result.outputs:
                server_ip_output = result.outputs.get("server_ip")
                server_ip = (
                    str(server_ip_output.value) if server_ip_output else "Unknown"
                )

                server_id_output = result.outputs.get("server_id")
                server_id = (
                    str(server_id_output.value) if server_id_output else "Unknown"
                )

                echo(f"Server IP: {server_ip}")
                echo(f"Server ID: {server_id}")

                # Add server to EasyRunner store after successful VM creation
                if server_ip != "Unknown":
                    server: Server | None = ServerSubCommand._add_server_to_store(
                        name=name, hostname_or_ip=server_ip
                    )
                    if not server:
                        echo(
                            message="Warning: Server created in cloud provider but failed to add to EasyRunner store."
                        )

                    # Rename SSH key files to use IP address naming convention

                    # Current SSH key paths (using server name)
                    old_private_key_path = ssh_key.key_path
                    old_public_key_path = f"{ssh_key.key_path}.pub"

                    # New SSH key paths (using IP address)
                    new_private_key_path = build_private_key_path(server_ip)
                    new_public_key_path = build_public_key_path(server_ip)

                    # Rename the files if they exist and target doesn't already exist
                    if os.path.exists(old_private_key_path) and not os.path.exists(
                        new_private_key_path
                    ):
                        os.rename(old_private_key_path, new_private_key_path)
                        echo(
                            f"Renamed private key: {old_private_key_path} -> {new_private_key_path}"
                        )

                    if os.path.exists(old_public_key_path) and not os.path.exists(
                        new_public_key_path
                    ):
                        os.rename(old_public_key_path, new_public_key_path)
                        echo(
                            f"Renamed public key: {old_public_key_path} -> {new_public_key_path}"
                        )

                else:
                    echo(
                        "Warning: Could not retrieve server IP address for SSH key renaming"
                    )
            else:
                echo(
                    f"Warning: VM creation succeeded but returned unexpected result format. Outputs: {result.outputs}"
                )

        else:
            echo(message=f"Cloud provider {cloud_provider_name} is not yet supported.")
            return

    @typer_app.command(
        name="delete",
        help="Deletes a server from the cloud provider.",
    )
    @staticmethod
    def delete_server(
        name: str = NAME_ARG,
        cloud_provider_name: CloudProviders = CLOUD_PROVIDER_ARG,
        cancel: bool = Option(
            False,
            "--cancel",
            help="Cancel any running operation and unlock the server stack instead of deleting.",
        ),
        refresh: bool = Option(
            False,
            "--refresh",
            help="Refresh the stack state to match actual cloud provider state instead of deleting. Useful when resources were manually deleted.",
        ),
    ) -> None:
        # If --cancel is provided, just cancel the stack and return
        if cancel:
            ServerSubCommand._cancel_stack(
                name=name, cloud_provider_name=cloud_provider_name
            )
            return

        # If --refresh is provided, just refresh the stack and return
        if refresh:
            ServerSubCommand._refresh_stack(
                name=name, cloud_provider_name=cloud_provider_name
            )
            return

        if cloud_provider_name not in CloudProviders:
            echo(
                message=f"Invalid cloud provider '{cloud_provider_name}'. Supported providers: {', '.join([provider.value for provider in CloudProviders])}."
            )
            return

        # Get server information for SSH key cleanup
        server: Server | None = ServerSubCommand._store.get_server_by_name(name=name)

        if server and len(server.apps) > 0:
            echo(
                message=f"Warning: Server '{name}' has active applications. Please remove them before deleting the server. This friction is intentionally added because `server delete` is a highly destructive and unrecoverable operation."
            )
            return

        # Check and install infrastructure dependencies first
        deps_result = InfrastructureDependencies.ensure_cloud_tools_available()
        if not deps_result.success:
            echo(message=f"Error: {deps_result.stderr}")
            return

        if cloud_provider_name == CloudProviders.HETZNER.value:
            from easyrunner.source.cloud_providers.hetzner_provider import (
                HetznerProvider,
            )

            stack_name = f"{name}-stack"
            provider = HetznerProvider.from_env()
            stack = HetznerStack(
                stack_name=stack_name,
                provider=provider,
            )
            result = stack.destroy()
            # result = provider.destroy_pulumi_stack(
            #     stack_name=stack_name,
            # )
            if result.success:
                echo(
                    message=f"Hetzner VM server stack '{name}' destroyed successfully."
                )

                stack = HetznerStack(
                    stack_name=stack_name,
                    provider=provider,
                )

                result = stack.remove()
                if result.success:
                    echo(message=f"Stack '{stack_name}' state removed.")
                else:
                    echo(
                        message=f"Warning: Failed to remove stack state for '{stack_name}': {result.stderr}"
                    )

                if server:
                    # Clean up SSH keys after successful VM stack destroy
                    ServerSubCommand._cleanup_ssh_keys(server.hostname_or_ip)
                    echo(
                        message=f"SSH keys for server '{name}' cleaned up successfully."
                    )
                    # Remove the server entry from EasyRunner database
                    ServerSubCommand._store.remove_server(server_id=server.id)
                    echo(message=f"Server '{name}' removed from EasyRunner database.")
                else:
                    echo(
                        message=f"Warning: Server '{name}' not found in EasyRunner database. SSH keys may need to be cleaned up manually."
                    )
            else:
                echo(message=f"Failed to delete Hetzner VM '{name}': {result.stderr}.")

    @typer_app.command(
        name="gen-ssh-key",
        help="(Re)Generates a new SSH key pair for EasyRunner to access a host server.",
        no_args_is_help=True,
    )
    @staticmethod
    def gen_ssh_key(
        address: str = ADDRESS_ARG,
        regenerate: Optional[bool] = Option(
            False,
            help="If True, regenerates and overwrites the key if it already exists. Defaults to False.",
        ),
    ) -> None:
        from easyrunner.source.ssh_key import SshKey

        ssh_key = SshKey(
            email=f"easyrunner@{address}",
            name=build_private_key_filename(address),
            ssh_key_dir=ssh_config.key_dir,
            regenerate_if_exists=regenerate,
        )
        # Print the public key to the console
        if not regenerate and ssh_key.keys_exists:
            echo(
                message=f"Key already exists at {ssh_key.key_path}. Use --regenerate to overwrite or show_ssh_key to get the public key."
            )
        elif not ssh_key.keys_exists or regenerate:
            ssh_key.generate_ed25519_keypair()
            ssh_key.save_private_key()
            ssh_key.save_public_key()

        echo(message=ssh_key.public_key_as_string())

    @typer_app.command(
        "show-ssh-key",
        help="Displays the EasyRunner public SSH key for the server",
        no_args_is_help=True,
    )
    @staticmethod
    def show_ssh_public_key(name: str = NAME_ARG) -> None:
        server = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(message=f"Server {name} not found in EasyRunner.")
            return

        ssh_public_key_path = build_public_key_path(server.hostname_or_ip)
        # Check if the public key file exists
        if not os.path.exists(ssh_public_key_path):
            print(ssh_public_key_path)
            echo(
                message=f"Public key file not found for host '{name}'. Have you run the 'gen-ssh-key' command?"
            )
            return

        # Read the public key file
        with open(ssh_public_key_path, "r") as public_key_file:
            public_key = public_key_file.read()
            print(public_key)

    @typer_app.command(
        "list",
        help="Lists all servers in EasyRunner.",
        no_args_is_help=False,
    )
    @staticmethod
    def list_servers() -> None:
        """
        Lists all servers in the EasyRunner store.
        """

        servers: List[Server] = ServerSubCommand._store.list_servers()
        if not servers:
            ServerSubCommand._print(
                "📝 No servers yet. Add a server using the '[bold cyan]add[/bold cyan]' command."
            )
            return

        # Create a table for displaying servers
        table = Table(title="EasyRunner Servers")
        table.add_column("Server Name", style="cyan", no_wrap=True)
        table.add_column("Hostname/IP", style="blue")
        table.add_column("Description", style="dim")
        table.add_column("Apps Count", style="green", justify="center")

        for server in servers:
            app_count = len(server.apps)
            table.add_row(
                server.name,
                server.hostname_or_ip,
                server.description or "",
                str(app_count)
            )

        ServerSubCommand._print(table)
        ServerSubCommand._print(f"\n📊 Total Servers: {len(servers)}")

    @typer_app.command(
        name="config-gh-ssh-key",
        help="Generates a new SSH key pair _for the server_ for GitHub access. The public key will be printed to the console. You need to add this public key to your GitHub account under Settings > SSH and GPG keys. \n\nThis key will be used by the server to pull code from GitHub.",
        no_args_is_help=True,
    )
    @staticmethod
    def config_ssh_key_for_github(
        name: str = NAME_ARG,
    ) -> None:

        server: Server | None = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(message=f"Server {name} not found in EasyRunner.")
            return

        from easyrunner.source.ssh_key import SshKey

        echo(message="Configuring the server with a SSH key for GitHub...")

        ssh_private_key_filename: str = build_github_private_key_filename(
            server.hostname_or_ip
        )
        ssh_key: SshKey = SshKey(
            email=f"easyrunner@{server.hostname_or_ip}",
            name=ssh_private_key_filename,
            ssh_key_dir=ssh_config.key_dir,
            regenerate_if_exists=False,
        )

        # Generate a new ed25519 SSH key pair in-memory
        # strictly do not save this locally.
        ssh_key.generate_ed25519_keypair()

        # put the private key on the server and configure it for GitHub access
        try:
            with Ssh(
                hostname_or_ipv4=server.hostname_or_ip,
                username=ssh_config.username,
                key_filename=build_private_key_path(
                    hostname_or_ipv4=server.hostname_or_ip
                ),
                debug=ServerSubCommand.debug,
                silent=ServerSubCommand.silent,
            ) as ssh_client:

                executor = CommandExecutor(ssh_client=ssh_client)

                host_server_instance = HostServerUbuntu(
                    easyrunner_username=ssh_config.username,
                    executor=executor,
                    debug=ServerSubCommand.debug,
                    silent=ServerSubCommand.silent,
                )

                # add private key to the server
                host_server_instance.add_private_key(
                    hostname="github.com",
                    username="git",
                    private_key=ssh_key.private_key_as_string(),
                    private_key_filename=ssh_private_key_filename,
                )

                # Github's public ssh keys to the known hosts file.
                for key in KNOWN_HOST_SSH_KEYS["github.com"]:
                    host_server_instance.add_key_to_known_hosts(ssh_key=key)

            echo(
                message=f"Add the following SSH public key to your Github account:\n\n{ssh_key.public_key_as_string()}\n\n"
            )
        except ConnectionError as connection_error:
            echo(
                message=f"Failed to connect to the server {name} at {server.hostname_or_ip}. Please check your connectivity to the server, that the server is up, the IP/hostname address is still valid etc. Make sure you have initialised the server by running the `er server init` command. Error: {connection_error}"
            )
            return
        except Exception as e:
            echo(
                message=f"Oops, something went wrong while configuring GitHub SSH key on your server. Run the command again with options --debug or --silent for more information. Error: {e}"
            )

    @typer_app.command(
        help="temp command for running any sudo command directly. TO BE REMOVED before prod.",
        no_args_is_help=True,
    )
    @staticmethod
    def run_sudo(name: str = NAME_ARG, command: str = Argument()) -> None:
        server: Server | None = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(message=f"Server {name} not found in EasyRunner.")
            return
        try:

            with Ssh(
                hostname_or_ipv4=server.hostname_or_ip,
                username=ssh_config.username,
                key_filename=build_private_key_path(
                    hostname_or_ipv4=server.hostname_or_ip
                ),
                debug=ServerSubCommand.debug,
                silent=ServerSubCommand.silent,
            ) as ssh_client:
                executor = CommandExecutor(ssh_client=ssh_client)
                result: ExecResult = executor.execute(
                    command=RunnableCommandString(command=command, sudo=True)
                )

            print(result.stderr)
        except ConnectionError as connection_error:
            echo(
                message=f"Failed to connect to the server at {server.hostname_or_ip}. Please check your connectivity to the server, that the server is up, the IP/hostname address is still valid etc. Make sure you have initialised the server by running the `er server init` command. Error: {connection_error}"
            )
            return
        except Exception as e:
            echo(
                message=f"Oops, something went wrong while running the sudo command. Run the command again with options --debug or --silent for more information. Error: {e}"
            )

    # App deploy command moved to app_sub_command.py

    @typer_app.command(
        name="easyrunner-start",
        help="Starts the EasyRunner stack on the server. Starts the Caddy Server container.",
        no_args_is_help=True,
    )
    @staticmethod
    def easyrunner_start(name: str = NAME_ARG) -> None:
        server: Server | None = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(message=f"Server {name} not found in EasyRunner.")
            return

        try:
            with Ssh(
                hostname_or_ipv4=server.hostname_or_ip,
                username=ssh_config.username,
                key_filename=build_private_key_path(
                    hostname_or_ipv4=server.hostname_or_ip
                ),
                debug=ServerSubCommand.debug,
                silent=ServerSubCommand.silent,
            ) as ssh_client:
                executor = CommandExecutor(ssh_client=ssh_client)
                host_server_instance = HostServerUbuntu(
                    easyrunner_username=ssh_config.username,
                    executor=executor,
                    debug=ServerSubCommand.debug,
                    silent=ServerSubCommand.silent,
                )

                host_server_instance.start_easyrunner_stack()
        except ConnectionError as connection_error:
            echo(
                message=f"Failed to connect to the server {name} at {server.hostname_or_ip}. Please check your connectivity to the server, that the server is up, the IP/hostname address is still valid etc. Make sure you have initialised the server by running the `er server init` command. Error: {connection_error}"
            )
            return
        except Exception as e:
            echo(
                message=f"Oops, something went wrong while starting EasyRunner on your server. Run the command again with options --debug or --silent for more information. Error: {e}"
            )

    @typer_app.command(
        name="easyrunner-stop",
        help="Stops the EasyRunner stack on the server. Stops the Caddy Server container.",
        no_args_is_help=True,
    )
    @staticmethod
    def easyrunner_stop(name: str = NAME_ARG) -> None:
        server: Server | None = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(message=f"Server {name} not found in EasyRunner.")
            return

        try:
            with Ssh(
                hostname_or_ipv4=server.hostname_or_ip,
                username=ssh_config.username,
                key_filename=build_private_key_path(
                    hostname_or_ipv4=server.hostname_or_ip
                ),
                debug=ServerSubCommand.debug,
                silent=ServerSubCommand.silent,
            ) as ssh_client:
                executor = CommandExecutor(ssh_client=ssh_client)
                host_server_instance = HostServerUbuntu(
                    easyrunner_username=ssh_config.username,
                    executor=executor,
                    debug=ServerSubCommand.debug,
                    silent=ServerSubCommand.silent,
                )

                host_server_instance.stop_easyrunner_stack()
        except ConnectionError as connection_error:
            echo(
                message=f"Failed to connect to the server {name} at {server.hostname_or_ip}. Please check your connectivity to the server, that the server is up, the IP/hostname address is still valid etc. Make sure you have initialised the server by running the `er server init` command. Error: {connection_error}"
            )
            return
        except Exception as e:
            echo(
                message=f"Oops, something went wrong while stopping EasyRunner on your server. Run the command again with options --debug or --silent for more information. Error: {e}"
            )

    @typer_app.command(
        name="ssh-connect-test",
        help="Tests SSH connection to the server. Useful for debugging SSH issues.",
        no_args_is_help=True,
    )
    @staticmethod
    def ssh_connect_test(
        name: str = NAME_ARG,
        username: str = ssh_config.username,
    ) -> None:
        server: Server | None = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            echo(message=f"Server {name} not found in EasyRunner.")
            return

        try:
            with Ssh(
                hostname_or_ipv4=server.hostname_or_ip,
                username=username,
                key_filename=build_private_key_path(
                    hostname_or_ipv4=server.hostname_or_ip
                ),
                debug=ServerSubCommand.debug,
                silent=ServerSubCommand.silent,
            ) as ssh_client:

                executor = CommandExecutor(ssh_client=ssh_client)
                result: ExecResult = executor.execute(
                    command=RunnableCommandString(
                        command="echo 'SSH connection successful!'", sudo=True
                    )
                )

                echo(
                    message=f"SSH connection test: {'succeeded' if result.success else 'failed'}.\nOutput: {result.stdout}"
                    + (
                        f"\nError: {result.stderr}"
                        if not result.success and result.stderr
                        else ""
                    )
                )
        except ConnectionError as connection_error:
            echo(
                message=f"Failed to connect to the server {name} at {server.hostname_or_ip}. Please check your connectivity to the server, that the server is up, the IP/hostname address is still valid etc. Make sure you have initialised the server by running the `er server init` command. Error: {connection_error}"
            )
            return
        except Exception as e:
            echo(
                message=f"Oops, something went wrong while testing SSH connection to your server. Run the command again with options --debug or --silent for more information. Error: {e}"
            )

    @staticmethod
    def _verify_firewall_external_connectivity(
        server_ip: str,
        remote_executor: CommandExecutor,
        local_executor: CommandExecutorLocal,
    ) -> None:
        """Verify external connectivity by testing allowed and blocked ports.

        Args:
            server_ip: IP address of the server to test
            remote_executor: Remote command executor for server operations
            local_executor: Local command executor for external connectivity tests
        """
        from easyrunner.source.commands.ubuntu.ip_tables_commands_ubuntu import (
            IpTablesCommandsUbuntu,
        )
        from easyrunner.source.resources.os_resources import IpTables
        from easyrunner.source.types.cpu_arch_types import CpuArch

        # Create IpTables resource for connectivity testing
        ipt = IpTables(IpTablesCommandsUbuntu(cpu_arch=CpuArch.X86_64), remote_executor)

        ServerSubCommand._print("\n  🔍 External Connectivity:")

        # Test allowed ports (should work)
        ServerSubCommand._print("  🌐 External Access (Should Allow):")

        # Test HTTP access (port 80) - should work
        http_result = ipt.test_external_http_access(server_ip, local_executor)
        http_accessible = (
            http_result.success
            and http_result.stdout is not None
            and "Hello, caddyfile-static-hello is running!" in http_result.stdout
        )
        http_icon = " [green]✔[/green]" if http_accessible else " [red]✗[/red]"
        ServerSubCommand._print(
            f"{http_icon} HTTP (port 80) - Should be accessible externally"
        )

        # Test blocked ports (should fail)
        ServerSubCommand._print("  🚫 External Access (Should Block):")

        # Test direct access to port 8080 - should be blocked
        http_direct_result = ipt.test_external_port_blocked(
            server_ip, 8080, local_executor, "http"
        )
        http_blocked = not http_direct_result.success  # Should fail/timeout
        http_block_icon = " [green]✔[/green]" if http_blocked else " [red]✗[/red]"
        ServerSubCommand._print(
            f"{http_block_icon} HTTP direct (port 8080) - Should be blocked externally"
        )

        # Test direct access to port 8443 - should be blocked
        https_direct_result = ipt.test_external_port_blocked(
            server_ip, 8443, local_executor, "https"
        )
        https_blocked = not https_direct_result.success  # Should fail/timeout
        https_block_icon = " [green]✔[/green]" if https_blocked else " [red]✗[/red]"
        ServerSubCommand._print(
            f"{https_block_icon} HTTPS direct (port 8443) - Should be blocked externally"
        )

        # Test Caddy API access - should be blocked
        caddy_api_result = ipt.test_external_caddy_api_blocked(
            server_ip, local_executor
        )
        caddy_blocked = not caddy_api_result.success  # Should fail/timeout
        caddy_block_icon = " [green]✔[/green]" if caddy_blocked else " [red]✗[/red]"
        ServerSubCommand._print(
            f"{caddy_block_icon} Caddy API (port 2019) - Should be blocked externally"
        )

    @typer_app.command(
        name="security-scan",
        help="Scan deployed applications for information disclosure vulnerabilities.",
        no_args_is_help=True,
    )
    @staticmethod
    def security_scan(
        name: str = NAME_ARG,
        categories: Optional[List[str]] = Option(
            None, 
            "--category", 
            help="Scan categories to run. Available: infrastructure, frameworks, development, files. If not specified, runs all categories."
        ),
        url: Optional[str] = Option(
            None,
            "--url",
            help="Specific URL to scan. If not provided, scans the server's main URL and all deployed apps."
        ),
        scan_all_apps: bool = Option(
            True,
            "--scan-all-apps/--no-scan-all-apps",
            help="Scan all deployed applications on the server. Default is True."
        )
    ) -> None:
        """
        Perform security scanning for information disclosure vulnerabilities.
        
        This command scans deployed applications from an external perspective to detect:
        - Infrastructure disclosure (Caddy server information)  
        - Framework version disclosure (React, Next.js, Django, Flask, FastAPI, Express, Node.js)
        - Development mode artifacts (source maps, debug pages, hot reload endpoints)
        - Exposed sensitive files (.env, config files, etc.)
        
        By default, scans all deployed applications on the server. Use --url to scan a specific URL only.
        """
        server = ServerSubCommand._store.get_server_by_name(name=name)
        if not server:
            ServerSubCommand._print(
                f"[red]✗ Server [bold]{name}[/bold] not found in EasyRunner.[/red]"
            )
            return

        try:
            # Create local executor for external scanning perspective
            local_executor = CommandExecutorLocal(
                debug=ServerSubCommand.debug, silent=ServerSubCommand.silent
            )

            # Initialize security scanner with progress callback
            scanner = WebSecurityScanner(
                executor=local_executor,
                progress_callback=ServerSubCommand._progress_callback
            )

            if url:
                # Scan specific URL only
                target_url = url
                if not target_url.startswith(('http://', 'https://')):
                    target_url = f"https://{target_url}"

                scan_result = scanner.scan_target(target_url, categories)
                if not ServerSubCommand.silent:
                    ServerSubCommand._display_security_scan_results(scan_result)

            elif scan_all_apps:
                # Scan all deployed apps on the server
                scan_results = scanner.scan_server_apps(server, categories)

                if not scan_results:
                    if not ServerSubCommand.silent:
                        ServerSubCommand._print("No applications found to scan on this server.")
                    return

                # Display results for each scanned URL
                total_issues = 0
                total_critical_high = 0

                for scan_result in scan_results:
                    if not ServerSubCommand.silent:
                        ServerSubCommand._display_security_scan_results(scan_result)
                    total_issues += scan_result.failed_checks
                    total_critical_high += scan_result.summary.get("critical", 0) + scan_result.summary.get("high", 0)
                    if not ServerSubCommand.silent:
                        ServerSubCommand._print("")  # Separator between results

                # Display overall summary
                if len(scan_results) > 1 and not ServerSubCommand.silent:
                    ServerSubCommand._print("📊 Overall Summary:")
                    ServerSubCommand._print(f"Scanned {len(scan_results)} URL(s)")
                    if total_issues == 0:
                        ServerSubCommand._print("🎉 No security issues found across all applications!", style="green bold")
                    else:
                        severity_color = "red" if total_critical_high > 0 else "yellow"
                        ServerSubCommand._print(f"⚠️  Total of {total_issues} security issues found ({total_critical_high} critical/high)", style=f"{severity_color} bold")
            else:
                # Scan only the main server URL
                target_url = f"https://{server.hostname_or_ip}"
                ServerSubCommand._print(f"🔍 Starting security scan of {target_url} (main server only)")
                scan_result = scanner.scan_target(target_url, categories)
                ServerSubCommand._display_security_scan_results(scan_result)

        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            echo(
                message=f"Security scan failed. Run with --debug for more details. Error: {e}",
                err=True,
            )

    @staticmethod
    def _display_security_scan_results(scan_result) -> None:
        """Display security scan results in formatted output."""

        console = Console()

        # Display header
        console.print(f"\n🔍 Security Scan Results - {scan_result.target_url}", style="bold")
        console.print(f"Timestamp: {scan_result.timestamp}")
        console.print(f"Total checks: {scan_result.total_checks}")

        # Display summary
        if scan_result.failed_checks > 0:
            summary_color = "red" if scan_result.summary.get("critical", 0) > 0 or scan_result.summary.get("high", 0) > 0 else "yellow"
        else:
            summary_color = "green"

        console.print(f"Status: {scan_result.passed_checks} passed, {scan_result.failed_checks} failed", style=summary_color)

        if scan_result.failed_checks > 0:
            console.print(f"Issues by severity: {scan_result.summary.get('critical', 0)} critical, "
                         f"{scan_result.summary.get('high', 0)} high, "
                         f"{scan_result.summary.get('medium', 0)} medium, "
                         f"{scan_result.summary.get('low', 0)} low")

        # Group checks by category
        categories = {}
        for check in scan_result.checks:
            category = check.category or "other"
            if category not in categories:
                categories[category] = []
            categories[category].append(check)

        # Display results by category
        for category, checks in categories.items():
            console.print(f"\n📋 {category.upper()}", style="bold")

            for check in checks:
                if check.passed:
                    icon = "[green]✓[/green]"
                else:
                    if check.severity == "critical":
                        icon = "[red]✗[/red]"
                    elif check.severity == "high":
                        icon = "[red]✗[/red]"
                    elif check.severity == "medium":
                        icon = "[yellow]⚠[/yellow]"
                    else:
                        icon = "[blue]ℹ[/blue]"

                status_text = "PASSED" if check.passed else f"FAILED ({check.severity.upper()})"
                console.print(f"  {icon} {check.description} - {status_text}")

                if not check.passed and check.details:
                    console.print(f"    Details: {check.details}", style="dim")

                if not check.passed and check.remediation:
                    console.print(f"    Remediation: {check.remediation}", style="cyan")

        # Display final summary
        console.print()
        if scan_result.failed_checks == 0:
            console.print("🎉 All security checks passed! No information disclosure detected.", style="green bold")
        else:
            console.print(f"⚠️  {scan_result.failed_checks} security issues detected. Review and remediate the findings above.", style="red bold")
