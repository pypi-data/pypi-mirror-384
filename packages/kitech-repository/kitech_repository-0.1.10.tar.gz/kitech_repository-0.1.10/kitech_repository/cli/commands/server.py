"""Server management command."""

import typer
from rich.console import Console
from rich.prompt import Prompt

from kitech_repository.core.config import Config

console = Console(highlight=False)
app = typer.Typer()


@app.callback(invoke_without_command=True)
def server(
    ctx: typer.Context,
    url: str = typer.Argument(None, help="Server URL to set (shows current server if not provided)"),
):
    """Manage KITECH server configuration."""
    if not url:
        # Show current server
        try:
            config = Config.load()
            console.print(f"\n[bold]Current Server:[/bold] {config.api_base_url}\n")
        except Exception as e:
            console.print(f"[red]❌ Failed to load config: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Set new server
        url = url.strip()
        if not url:
            console.print("[red]❌ URL cannot be empty[/red]")
            raise typer.Exit(1)

        try:
            config = Config.load()
            config.api_base_url = url.rstrip("/")
            config.save()

            console.print(f"[green]✅ Server configured: {config.api_base_url}[/green]")
            console.print("\n[yellow]⚠️  Please login again: kitech-dev connect[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Failed to save config: {e}[/red]")
            raise typer.Exit(1)
