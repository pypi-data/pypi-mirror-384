"""Status command - show connection and authentication status."""

import typer
from rich.console import Console

from kitech_repository.core.auth import AuthManager
from kitech_repository.core.client import KitechClient
from kitech_repository.core.config import Config

console = Console(highlight=False)
app = typer.Typer()


@app.callback(invoke_without_command=True)
def status(ctx: typer.Context):
    """Show connection and authentication status."""
    try:
        config = Config.load()
        auth_manager = AuthManager(config=config)

        # Show server info
        console.print(f"\n[bold]Server:[/bold] {config.api_base_url}")

        # Check authentication
        if auth_manager.is_authenticated():
            try:
                with KitechClient() as client:
                    result = client.test_connection()
                    user = result.get('user', {})

                    console.print("[green]✅ Authenticated[/green]")
                    console.print(f"사용자 이름: {user.get('name', 'N/A')}")
                    console.print(f"사용자 이메일: {user.get('email', 'N/A')}")

                    # Show expiry if available
                    metadata = auth_manager._load_metadata()
                    if metadata.get("expires_at"):
                        console.print(f"만료일: {metadata.get('expires_at')}")

                    console.print("")
            except Exception as e:
                console.print(f"[red]❌ Authentication failed: {e}[/red]")
                console.print("Please reconnect: [cyan]kitech-dev connect[/cyan]")
        else:
            console.print("[yellow]⚠️  Not authenticated[/yellow]")
            console.print("Please connect first: [cyan]kitech-dev connect[/cyan]")
            console.print("")

    except Exception as e:
        console.print(f"[red]❌ Error checking status: {e}[/red]")
        raise typer.Exit(1)
