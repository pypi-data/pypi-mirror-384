"""Logout command."""

import typer
from rich.console import Console

from kitech_repository.core.auth import AuthManager

console = Console(highlight=False)
app = typer.Typer()


@app.callback(invoke_without_command=True)
def logout(ctx: typer.Context):
    """Logout from KITECH server."""
    try:
        auth_manager = AuthManager()
        if auth_manager.logout():
            console.print("[green]✅ Logged out successfully![/green]")
        else:
            console.print("⚠️  You were not logged in")
    except Exception as e:
        console.print(f"[red]❌ Logout failed: {e}[/red]")
        raise typer.Exit(1)
