import logging
from typing import Self

import typer
from rich.console import Console
from typer import Option

from .auth.github_device_flow import GitHubDeviceFlow
from .auth.github_oauth_config import GitHubOAuthConfig
from .auth.github_token_manager import GitHubTokenManager

logger = logging.getLogger(__name__)


class LinkSubCommand:
    """Link subcommands for EasyRunner."""

    typer_app: typer.Typer = typer.Typer(
        name="link",
        no_args_is_help=True,
        rich_markup_mode="rich",
        help="[bold green]Link[/bold green] commands for EasyRunner. Manage authentication with external service provider like Github and Hetzner.",
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
        help="Authenticate and link with GitHub using OAuth. This will allow EasyRunner to manage deploy keys for your repositories.",
        no_args_is_help=False,
    )
    @staticmethod
    def github_auth(
        unlink: bool = Option(
            False,
            "--unlink",
            help="Unlink GitHub account by removing the stored GitHub authentication token."
        ),
        status: bool = Option(
            False,
            "--status", 
            help="Check current GitHub authentication status."
        )
    ) -> None:
        """Authenticate with GitHub for repository access."""

        token_manager = GitHubTokenManager()

        if unlink:
            if token_manager.delete_token():
                LinkSubCommand._progress_callback(
                    "[green]✅ Successfully unlinked GitHub account[/green]", "\n"
                )
            else:
                LinkSubCommand._progress_callback(
                    "[red]❌ Failed to remove GitHub authentication[/red]", "\n"
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
                        "[green]✅ GitHub authentication active[/green]", "\n"
                    )
                else:
                    LinkSubCommand._progress_callback(
                        "[red]❌ GitHub authentication invalid (token expired or revoked)[/red]",
                        "\n",
                    )
            else:
                LinkSubCommand._progress_callback(
                    "[yellow]⚠️  Not authenticated with GitHub[/yellow]", "\n"
                )
            return

        # if token:
        #     # Manual token input
        #     config = GitHubOAuthConfig()
        #     device_flow = GitHubDeviceFlow(
        #         client_id=config.client_id,
        #         scopes=config.scopes,
        #         progress_callback=LinkSubCommand._progress_callback,
        #     )
        #     if device_flow.test_token(token):
        #         if token_manager.store_token(token):
        #             LinkSubCommand._progress_callback(
        #                 "[green]✅ GitHub token saved successfully[/green]", "\n"
        #             )
        #         else:
        #             LinkSubCommand._progress_callback(
        #                 "[red]❌ Failed to save token[/red]", "\n"
        #             )
        #     else:
        #         LinkSubCommand._progress_callback(
        #             "[red]❌ Invalid GitHub token[/red]", "\n"
        #         )
        #     return

        # Device Flow - OAuth for CLIs
        try:
            LinkSubCommand._progress_callback(
                "[blue]🔐 Starting GitHub Device Flow authentication...[/blue]", "\n"
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
                        "[green]✅ GitHub authentication successful![/green]", "\n"
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
                        "[red]❌ Authentication succeeded but failed to store token[/red]",
                        "\n",
                    )
            else:
                LinkSubCommand._progress_callback(
                    "[red]❌ GitHub authentication failed[/red]", "\n"
                )
                LinkSubCommand._progress_callback(
                    "💡 Try running the command again or use --token to manually provide a token",
                    "\n",
                )

        except KeyboardInterrupt:
            LinkSubCommand._progress_callback(
                "\n[yellow]⚠️  Authentication cancelled[/yellow]", "\n"
            )
        except Exception as e:
            LinkSubCommand._progress_callback(
                f"[red]❌ Authentication error: {e}[/red]", "\n"
            )
            if LinkSubCommand.debug:
                import traceback
                LinkSubCommand._progress_callback(
                    f"[red]{traceback.format_exc()}[/red]", "\n"
                )

    @typer_app.command(
        name="status",
        help="Show authentication status for all providers.",
        no_args_is_help=False,
    )
    @staticmethod
    def auth_status() -> None:
        """Show authentication status for all providers."""
        LinkSubCommand._progress_callback(
            "[bold blue]🔐 Authentication Status[/bold blue]\n", "\n"
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
                    "GitHub: [green]✅ Authenticated[/green]", "\n"
                )
            else:
                LinkSubCommand._progress_callback(
                    "GitHub: [red]❌ Invalid (token expired or revoked)[/red]", "\n"
                )
        else:
            LinkSubCommand._progress_callback(
                "GitHub: [yellow]⚠️  Not authenticated[/yellow]", "\n"
            )

            LinkSubCommand._progress_callback(
                "\n💡 Use 'er link github' to authenticate with GitHub", "\n\n"
            )
