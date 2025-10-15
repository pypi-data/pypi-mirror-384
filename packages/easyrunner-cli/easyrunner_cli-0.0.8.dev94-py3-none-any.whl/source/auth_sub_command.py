import logging
from typing import Optional, Self

import typer
from rich.console import Console
from typer import Option

from .auth.github_oauth_config import GitHubOAuthConfig
from .auth.github_oauth_flow import GitHubOAuthFlow
from .auth.github_token_manager import GitHubTokenManager

logger = logging.getLogger(__name__)


class AuthSubCommand:
    """Authentication subcommands for EasyRunner."""

    typer_app: typer.Typer = typer.Typer(
        name="auth",
        no_args_is_help=True,
        rich_markup_mode="rich",
        help="[bold green]Authentication[/bold green] commands for EasyRunner. Manage GitHub OAuth and other authentication providers.",
    )

    debug: bool = False
    silent: bool = False

    _console: Console = Console()
    _print = _console.print

    # Define progress callback with CLI-specific formatting
    @staticmethod
    def _progress_callback(message: str, end: str) -> None:
        if not AuthSubCommand.silent:
            AuthSubCommand._print(message, end=end)

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
            AuthSubCommand.debug = debug
            AuthSubCommand.silent = silent
            if debug:
                logger.setLevel(logging.DEBUG)
            elif silent:
                logger.setLevel(logging.ERROR)

    @typer_app.command(
        name="github",
        help="Authenticate with GitHub using OAuth. This will allow EasyRunner to manage deploy keys for your repositories.",
        no_args_is_help=False,
    )
    @staticmethod
    def github_auth(
        token: Optional[str] = Option(
            None,
            "--token",
            help="Manually provide a GitHub Personal Access Token instead of using OAuth flow."
        ),
        logout: bool = Option(
            False,
            "--logout",
            help="Remove stored GitHub authentication."
        ),
        status: bool = Option(
            False,
            "--status", 
            help="Check current GitHub authentication status."
        )
    ) -> None:
        """Authenticate with GitHub for repository access."""

        token_manager = GitHubTokenManager()

        if logout:
            if token_manager.delete_token():
                AuthSubCommand._progress_callback(
                    "[green]✅ Successfully logged out of GitHub[/green]", "\n"
                )
            else:
                AuthSubCommand._progress_callback(
                    "[red]❌ Failed to remove GitHub authentication[/red]", "\n"
                )
            return

        if status:
            stored_token = token_manager.get_token()
            if stored_token:
                oauth_flow = GitHubOAuthFlow(
                    config=GitHubOAuthConfig(),
                    progress_callback=AuthSubCommand._progress_callback,
                )
                if oauth_flow.test_token(stored_token):
                    AuthSubCommand._progress_callback(
                        "[green]✅ GitHub authentication active[/green]", "\n"
                    )
                else:
                    AuthSubCommand._progress_callback(
                        "[red]❌ GitHub authentication invalid (token expired or revoked)[/red]",
                        "\n",
                    )
            else:
                AuthSubCommand._progress_callback(
                    "[yellow]⚠️  Not authenticated with GitHub[/yellow]", "\n"
                )
            return

        if token:
            # Manual token input
            oauth_flow = GitHubOAuthFlow(
                GitHubOAuthConfig(), AuthSubCommand._progress_callback
            )
            if oauth_flow.test_token(token):
                if token_manager.store_token(token):
                    AuthSubCommand._progress_callback(
                        "[green]✅ GitHub token saved successfully[/green]", "\n"
                    )
                else:
                    AuthSubCommand._progress_callback(
                        "[red]❌ Failed to save token[/red]", "\n"
                    )
            else:
                AuthSubCommand._progress_callback(
                    "[red]❌ Invalid GitHub token[/red]", "\n"
                )
            return

        # OAuth flow
        try:
            AuthSubCommand._progress_callback(
                "[blue]🔐 Starting GitHub OAuth authentication...[/blue]", "\n"
            )

            config = GitHubOAuthConfig()
            oauth_flow = GitHubOAuthFlow(config, AuthSubCommand._progress_callback)

            access_token = oauth_flow.start_oauth_flow()

            if access_token:
                if token_manager.store_token(access_token):
                    AuthSubCommand._progress_callback(
                        "[green]✅ GitHub authentication successful![/green]", "\n"
                    )
                    AuthSubCommand._progress_callback(
                        "🔑 Access token stored securely in keychain", "\n"
                    )
                    AuthSubCommand._progress_callback(
                        "🚀 EasyRunner can now manage deploy keys for your repositories",
                        "\n",
                    )
                else:
                    AuthSubCommand._progress_callback(
                        "[red]❌ Authentication succeeded but failed to store token[/red]",
                        "\n",
                    )
            else:
                AuthSubCommand._progress_callback(
                    "[red]❌ GitHub authentication failed[/red]", "\n"
                )
                AuthSubCommand._progress_callback(
                    "💡 Try running the command again or use --token to manually provide a token",
                    "\n",
                )

        except KeyboardInterrupt:
            AuthSubCommand._progress_callback(
                "\n[yellow]⚠️  Authentication cancelled[/yellow]", "\n"
            )
        except Exception as e:
            AuthSubCommand._progress_callback(
                f"[red]❌ Authentication error: {e}[/red]", "\n"
            )
            if AuthSubCommand.debug:
                import traceback
                AuthSubCommand._progress_callback(
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
        AuthSubCommand._progress_callback(
            "[bold blue]🔐 Authentication Status[/bold blue]\n", "\n"
        )

        # Check GitHub
        token_manager = GitHubTokenManager()
        stored_token = token_manager.get_token()

        if stored_token:
            oauth_flow = GitHubOAuthFlow(
                GitHubOAuthConfig(), AuthSubCommand._progress_callback
            )
            if oauth_flow.test_token(stored_token):
                AuthSubCommand._progress_callback(
                    "GitHub: [green]✅ Authenticated[/green]", "\n"
                )
            else:
                AuthSubCommand._progress_callback(
                    "GitHub: [red]❌ Invalid (token expired or revoked)[/red]", "\n"
                )
        else:
            AuthSubCommand._progress_callback(
                "GitHub: [yellow]⚠️  Not authenticated[/yellow]", "\n"
            )

            AuthSubCommand._progress_callback(
                "\n💡 Use 'er auth github' to authenticate with GitHub", "\n\n"
            )
