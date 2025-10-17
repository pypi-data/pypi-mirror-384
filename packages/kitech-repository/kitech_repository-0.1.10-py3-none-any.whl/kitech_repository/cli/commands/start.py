"""Start command - launch TUI file manager."""

import typer
from rich.console import Console

from kitech_repository.cli.utils import get_cli_command_name
from kitech_repository.core.auth import AuthManager
from kitech_repository.core.client import KitechClient
from kitech_repository.core.config import Config
from kitech_repository.core.exceptions import AuthenticationError
from kitech_repository.tui import KitechTUI

console = Console(highlight=False)
app = typer.Typer()


@app.callback(invoke_without_command=True)
def start(
    ctx: typer.Context,
    repository_id: int = typer.Argument(None, help="Repository ID (optional - will show selection screen if not provided)"),
):
    """Start TUI file manager with Textual interface."""
    try:
        # Check authentication first
        auth_manager = AuthManager()
        if not auth_manager.is_authenticated():
            console.print("[red]❌ Not authenticated.[/red]")
            console.print(f"Please login first: [cyan]{get_cli_command_name()} login[/cyan]")
            raise typer.Exit(1)

        # Initialize client (will automatically use AuthManager internally)
        config = Config.load()
        client = KitechClient(config=config)

        # Launch Textual TUI
        tui_app = KitechTUI(client=client, initial_repo_id=repository_id)
        tui_app.run()

    except AuthenticationError:
        console.print("[red]❌ Authentication error[/red]")
        console.print(f"Please login first: [cyan]{get_cli_command_name()} login[/cyan]")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n👋 File manager closed.")
    except Exception as e:
        import traceback

        console.print(f"[red]❌ Error: {e}[/red]")
        console.print(f"[red]Type: {type(e).__name__}[/red]")
        console.print(f"[red]Details: {traceback.format_exc()}[/red]")
        raise typer.Exit(1)
