"""License management commands for EasyRunner CLI."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typer import Argument, Option, Typer

from .licensing import LicenseManager


class LicenseSubCommand:
    """License management commands."""

    typer_app = Typer(
        name="license",
        help="Manage EasyRunner license. Install, view status, and validate licenses.",
        no_args_is_help=True,
    )

    console = Console()

    @typer_app.command(
        name="install",
        help="Install a license file for EasyRunner.",
        no_args_is_help=True,
    )
    @staticmethod
    def install_license(
        license_file: str = Argument(
            ..., help="Path to the license file to install (e.g., ~/Downloads/license.jwt)"
        ),
    ) -> None:
        """Install a license file."""
        try:
            source_path = Path(license_file).expanduser().resolve()
            
            if not source_path.exists():
                LicenseSubCommand.console.print(
                    f"[red]Error:[/red] License file not found: {source_path}"
                )
                return

            manager = LicenseManager()
            license_info = manager.install_license(source_path)

            # Display success message
            LicenseSubCommand.console.print()
            LicenseSubCommand.console.print("[green]✓ License installed successfully![/green]")
            LicenseSubCommand.console.print()

            # Display license details
            LicenseSubCommand._display_license_info(license_info)

            LicenseSubCommand.console.print()
            LicenseSubCommand.console.print(
                f"License saved to: [cyan]{manager.license_path}[/cyan]"
            )
            LicenseSubCommand.console.print()

        except ValueError as e:
            LicenseSubCommand.console.print(f"[red]Error:[/red] {str(e)}")
        except Exception as e:
            LicenseSubCommand.console.print(
                f"[red]Error:[/red] Failed to install license: {str(e)}"
            )

    @typer_app.command(
        name="status",
        help="Display information about the installed license.",
    )
    @staticmethod
    def license_status() -> None:
        """Display current license status."""
        manager = LicenseManager()
        license_info = manager.get_license_info()

        if license_info is None:
            LicenseSubCommand.console.print()
            LicenseSubCommand.console.print("[yellow]No license installed[/yellow]")
            LicenseSubCommand.console.print()
            LicenseSubCommand.console.print("To install a license:")
            LicenseSubCommand.console.print(
                "  [cyan]er license install <path-to-license-file>[/cyan]"
            )
            LicenseSubCommand.console.print()
            LicenseSubCommand.console.print(
                "Don't have a license? Visit [link]https://easyrunner.xyz[/link] to purchase."
            )
            LicenseSubCommand.console.print()
            return

        LicenseSubCommand.console.print()
        LicenseSubCommand._display_license_info(license_info)
        LicenseSubCommand.console.print()

    @typer_app.command(
        name="validate",
        help="Validate the installed license without displaying details.",
    )
    @staticmethod
    def validate_license() -> None:
        """Validate the installed license."""
        manager = LicenseManager()
        
        if manager.validate_license():
            LicenseSubCommand.console.print("[green]✓ License is valid[/green]")
        else:
            LicenseSubCommand.console.print(
                "[red]✗ No valid license found[/red]"
            )
            LicenseSubCommand.console.print()
            LicenseSubCommand.console.print(
                "Run [cyan]er license status[/cyan] for more information."
            )

    @typer_app.command(
        name="remove",
        help="Remove the installed license.",
    )
    @staticmethod
    def remove_license(
        confirm: bool = Option(
            False,
            "--yes",
            "-y",
            help="Skip confirmation prompt",
        ),
    ) -> None:
        """Remove the installed license."""
        manager = LicenseManager()

        if not manager.license_path.exists():
            LicenseSubCommand.console.print("[yellow]No license installed[/yellow]")
            return

        if not confirm:
            LicenseSubCommand.console.print()
            response = input("Are you sure you want to remove the license? (y/N): ")
            if response.lower() != "y":
                LicenseSubCommand.console.print("Cancelled")
                return

        if manager.remove_license():
            LicenseSubCommand.console.print("[green]✓ License removed[/green]")
        else:
            LicenseSubCommand.console.print("[yellow]No license was installed[/yellow]")

    @staticmethod
    def _display_license_info(license_info) -> None:
        """Display formatted license information."""
        # Create table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value")

        # Add license details
        table.add_row("Customer", license_info.customer_email)
        table.add_row("Server Limit", str(license_info.server_limit))
        table.add_row("License Type", license_info.license_type.title())
        table.add_row(
            "Issued On", license_info.issued_at.strftime("%Y-%m-%d")
        )
        table.add_row(
            "Updates Until", license_info.updates_until.strftime("%Y-%m-%d")
        )

        # Update period status
        if license_info.is_update_period_valid:
            status = "[green]✓ Active[/green]"
        else:
            status = "[yellow]⚠ Expired[/yellow] (version remains usable)"
        table.add_row("Update Period", status)

        table.add_row("License ID", f"[dim]{license_info.license_id}[/dim]")

        # Display in a panel
        LicenseSubCommand.console.print(
            Panel(
                table,
                title="[bold]EasyRunner License[/bold]",
                border_style="green" if license_info.is_update_period_valid else "yellow",
            )
        )

        # Show warning if update period expired
        if not license_info.is_update_period_valid:
            LicenseSubCommand.console.print()
            LicenseSubCommand.console.print(
                "[yellow]⚠ Your update period has expired.[/yellow]"
            )
            LicenseSubCommand.console.print(
                "  You can continue using this version of EasyRunner."
            )
            LicenseSubCommand.console.print(
                "  To receive updates, please renew at [link]https://easyrunner.xyz[/link]"
            )
