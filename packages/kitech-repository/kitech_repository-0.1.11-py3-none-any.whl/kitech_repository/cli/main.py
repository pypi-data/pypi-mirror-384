"""Main CLI application for KITECH Repository."""

import typer
from rich.console import Console

from kitech_repository import __version__
from kitech_repository.cli.commands import config, login, logout, server, start, status

console = Console()
app = typer.Typer(
    name="kitech",
    help="KITECH Manufacturing Data Repository CLI",
    add_completion=False,
)

# Register top-level commands
app.add_typer(login.app, name="login", help="Login to KITECH server (setup + authentication)")
app.add_typer(logout.app, name="logout", help="Logout from KITECH server")
app.add_typer(status.app, name="status", help="Show connection and authentication status")
app.add_typer(start.app, name="start", help="Start TUI file manager")
app.add_typer(server.app, name="server", help="Manage server configuration")
app.add_typer(config.app, name="config", help="Show or reset configuration")


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold blue]KITECH Repository CLI[/bold blue] v{__version__}")


if __name__ == "__main__":
    app()
