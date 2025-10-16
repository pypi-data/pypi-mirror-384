import sys
from importlib.metadata import PackageNotFoundError, version

import typer
from rich.console import Console

from .app_sub_command import AppSubCommand
from .license_sub_command import LicenseSubCommand
from .licensing import LicenseManager
from .link_sub_command import LinkSubCommand
from .servers_sub_command import ServerSubCommand


def version_callback(value: bool) -> None:
    """Callback for --version flag."""
    if value:
        console = Console()
        try:
            pkg_version = version("easyrunner_cli")
            console.print(
                f"[bold green]EasyRunner CLI[/bold green] version [cyan]{pkg_version}[/cyan]"
            )
        except PackageNotFoundError:
            console.print(
                "[bold green]EasyRunner CLI[/bold green] [yellow](development version)[/yellow]"
            )
        raise typer.Exit()


root_app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
    help="[bold green]EasyRunner[/bold green] - Self hosting PaaS. Configures a server as a web host + CI/CD. Easily self-host your project web applications on a VM or VPS. Run a command without any arguments or options to get help. \n\n[grey]Copyright (c) 2024 - 2025 Janaka Abeywardhana[/grey]",
)


@root_app.callback(invoke_without_command=True)
def check_license(
    ctx: typer.Context,
    version_flag: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Check if a valid license exists before running commands (except license commands)."""
    # Skip license check if --help is requested
    if "--help" in sys.argv or "-h" in sys.argv:
        return

    # Skip license check if no command is being invoked (showing help)
    if ctx.invoked_subcommand is None:
        return

    # Skip license check for license commands
    if ctx.invoked_subcommand == "license":
        return

    # Check for valid license
    manager = LicenseManager()
    license_info = manager.get_license_info()

    if license_info is None:
        console = Console()
        console.print()
        console.print("[red]✗ No valid EasyRunner license found[/red]")
        console.print()
        console.print("EasyRunner requires a license to operate.")
        console.print()
        console.print("To install your license:")
        console.print("  [cyan]er license install <path-to-license-file>[/cyan]")
        console.print()
        console.print("Don't have a license yet?")
        console.print("  Visit [link]https://easyrunner.xyz[/link] to purchase")
        console.print()
        raise typer.Exit(code=1)

    # License exists and is valid - show warning if update period expired
    if not license_info.is_update_period_valid:
        console = Console()
        console.print()
        console.print("[yellow]⚠ Your update period has expired[/yellow]")
        console.print(
            f"  Updates valid until: {license_info.updates_until.strftime('%Y-%m-%d')}"
        )
        console.print("  You can continue using this version.")
        console.print("  To receive updates, visit [link]https://easyrunner.xyz[/link]")
        console.print()


root_app.add_typer(LicenseSubCommand().typer_app)
root_app.add_typer(LinkSubCommand().typer_app)
root_app.add_typer(ServerSubCommand().typer_app)
root_app.add_typer(AppSubCommand().typer_app)


if __name__ == "__main__":
    root_app()
