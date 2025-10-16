import logging
from typing import Optional, Self

import typer
from rich.console import Console
from typer import Option

from .github_device_flow import GitHubDeviceFlow
from .github_oauth_config import GitHubOAuthConfig
from .github_token_manager import GitHubTokenManager

logger = logging.getLogger(__name__)


class LinkSubCommand:
    """Link external services to EasyRunner."""

    typer_app: typer.Typer = typer.Typer(
        name="link",
        no_args_is_help=True,
        rich_markup_mode="rich",
        help="[bold green]Link[/bold green] external services to EasyRunner. Connect GitHub and other service providers.",
    )

    debug: bool = False
    silent: bool = False

    _console: Console = Console()
    _print = _console.print

    # Define progress callback with CLI-specific formatting
    @staticmethod
    def _progress_callback(message: str, end: str) -> None:
        if not LinkSubCommand.silent:
            LinkSubCommand._print(message, end=end)

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
            LinkSubCommand.debug = debug
            LinkSubCommand.silent = silent
            if debug:
                logger.setLevel(logging.DEBUG)
            elif silent:
                logger.setLevel(logging.ERROR)

    @typer_app.command(
        name="github",
        help="Link GitHub to EasyRunner. This will allow EasyRunner to manage deploy keys for your repositories.",
        no_args_is_help=False,
    )
    @staticmethod
    def github_link(
        token: Optional[str] = Option(
            None,
            "--token",
            help="Manually provide a GitHub Personal Access Token instead of using OAuth flow."
        ),
        unlink: bool = Option(
            False,
            "--unlink",
            help="Remove GitHub link and stored credentials."
        ),
        status: bool = Option(
            False,
            "--status", 
            help="Check current GitHub link status."
        )
    ) -> None:
        """Link GitHub for repository access."""

        token_manager = GitHubTokenManager()

        if unlink:
            if token_manager.delete_token():
                LinkSubCommand._progress_callback(
                    "[green]✅ Successfully unlinked GitHub[/green]", "\n"
                )
            else:
                LinkSubCommand._progress_callback(
                    "[red]❌ Failed to remove GitHub link[/red]", "\n"
                )
            return

        if status:
            stored_token = token_manager.get_token()
            if stored_token:
                config = GitHubOAuthConfig()
                device_flow = GitHubDeviceFlow(
                    client_id=config.client_id,
                    scopes=config.scopes,
                    progress_callback=LinkSubCommand._progress_callback,
                )
                if device_flow.test_token(stored_token):
                    LinkSubCommand._progress_callback(
                        "[green]✅ GitHub link active[/green]", "\n"
                    )
                else:
                    LinkSubCommand._progress_callback(
                        "[red]❌ GitHub link invalid (token expired or revoked)[/red]",
                        "\n",
                    )
            else:
                LinkSubCommand._progress_callback(
                    "[yellow]⚠️  GitHub not linked[/yellow]", "\n"
                )
            return

        if token:
            # Manual token input
            config = GitHubOAuthConfig()
            device_flow = GitHubDeviceFlow(
                client_id=config.client_id,
                scopes=config.scopes,
                progress_callback=LinkSubCommand._progress_callback,
            )
            if device_flow.test_token(token):
                if token_manager.store_token(token):
                    LinkSubCommand._progress_callback(
                        "[green]✅ GitHub token saved successfully[/green]", "\n"
                    )
                else:
                    LinkSubCommand._progress_callback(
                        "[red]❌ Failed to save token[/red]", "\n"
                    )
            else:
                LinkSubCommand._progress_callback(
                    "[red]❌ Invalid GitHub token[/red]", "\n"
                )
            return

        # Device Flow - OAuth for CLIs
        try:
            LinkSubCommand._progress_callback(
                "[blue]🔐 Starting GitHub Device Flow linking...[/blue]", "\n"
            )

            config = GitHubOAuthConfig()
            device_flow = GitHubDeviceFlow(
                client_id=config.client_id,
                scopes=config.scopes,
                progress_callback=LinkSubCommand._progress_callback,
            )

            access_token = device_flow.start_device_flow()

            if access_token:
                if token_manager.store_token(access_token):
                    LinkSubCommand._progress_callback(
                        "[green]✅ GitHub linked successfully![/green]", "\n"
                    )
                    LinkSubCommand._progress_callback(
                        "🔑 Access token stored securely in keychain", "\n"
                    )
                    LinkSubCommand._progress_callback(
                        "🚀 EasyRunner can now manage deploy keys for your repositories",
                        "\n",
                    )
                else:
                    LinkSubCommand._progress_callback(
                        "[red]❌ Link succeeded but failed to store token[/red]",
                        "\n",
                    )
            else:
                LinkSubCommand._progress_callback(
                    "[red]❌ GitHub linking failed[/red]", "\n"
                )
                LinkSubCommand._progress_callback(
                    "💡 Try running the command again or use --token to manually provide a token",
                    "\n",
                )

        except KeyboardInterrupt:
            LinkSubCommand._progress_callback(
                "\n[yellow]⚠️  Linking cancelled[/yellow]", "\n"
            )
        except Exception as e:
            LinkSubCommand._progress_callback(
                f"[red]❌ Linking error: {e}[/red]", "\n"
            )
            if LinkSubCommand.debug:
                import traceback
                LinkSubCommand._progress_callback(
                    f"[red]{traceback.format_exc()}[/red]", "\n"
                )

    @typer_app.command(
        name="status",
        help="Show link status for all services.",
        no_args_is_help=False,
    )
    @staticmethod
    def link_status() -> None:
        """Show link status for all services."""
        LinkSubCommand._progress_callback(
            "[bold blue]� Link Status[/bold blue]\n", "\n"
        )

        # Check GitHub
        token_manager = GitHubTokenManager()
        stored_token = token_manager.get_token()

        if stored_token:
            config = GitHubOAuthConfig()
            device_flow = GitHubDeviceFlow(
                client_id=config.client_id,
                scopes=config.scopes,
                progress_callback=LinkSubCommand._progress_callback,
            )
            if device_flow.test_token(stored_token):
                LinkSubCommand._progress_callback(
                    "GitHub: [green]✅ Linked[/green]", "\n"
                )
            else:
                LinkSubCommand._progress_callback(
                    "GitHub: [red]❌ Invalid (token expired or revoked)[/red]", "\n"
                )
        else:
            LinkSubCommand._progress_callback(
                "GitHub: [yellow]⚠️  Not linked[/yellow]", "\n"
            )

        LinkSubCommand._progress_callback(
            "\n💡 Use 'er link github' to link GitHub", "\n"
        )
