"""Login command - combines server setup and login."""

import typer
from rich.console import Console
from rich.prompt import Prompt

from kitech_repository.core.auth import AuthManager
from kitech_repository.core.client import KitechClient
from kitech_repository.core.config import Config

console = Console(highlight=False)
app = typer.Typer()


@app.callback(invoke_without_command=True)
def login(
    ctx: typer.Context,
    server_url: str = typer.Argument(None, help="Server URL (will prompt if not provided)"),
    token: str = typer.Option(None, "--token", "-t", help="API token (will prompt if not provided)"),
    max_retries: int = typer.Option(3, "--retries", help="Maximum number of retry attempts"),
):
    """Login to KITECH server (setup + authentication)."""
    # Get server URL
    url = server_url
    if not url:
        console.print("\n[bold]KITECH Server Login[/bold]")
        console.print("Examples:")
        console.print("  - http://localhost:6300")
        console.print("  - http://server:6300")
        console.print("  - https://kitech-manufacturing-api.wimcorp.dev")
        console.print("")
        url = Prompt.ask("Server URL")

    url = url.strip()
    if not url:
        console.print("[red]❌ URL cannot be empty[/red]")
        raise typer.Exit(1)

    # Save server URL
    try:
        config = Config.load()
        config.api_base_url = url.rstrip("/")
        config.save()
        console.print(f"[green]✅ Server configured: {config.api_base_url}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to save server config: {e}[/red]")
        raise typer.Exit(1)

    # Login
    attempt = 0
    app_key = token
    while attempt < max_retries:
        if not app_key or attempt > 0:
            if attempt > 0:
                console.print(f"Attempt {attempt + 1}/{max_retries}")
            app_key = Prompt.ask("App Key", password=True)

        if not app_key.startswith("kt_"):
            console.print("[red]❌ Invalid app key format. App key should start with 'kt_'[/red]")
            app_key = None
            attempt += 1
            continue

        try:
            auth_manager = AuthManager()

            # Save app key temporarily
            auth_manager.login(app_key=app_key)

            # Test connection
            with KitechClient() as client:
                result = client.test_connection()

            # Update with user info
            user = result.get('user', {})
            auth_manager.login(
                app_key=app_key,
                user_id=result.get("userId"),
                expires_at=result.get("expiresAt"),
            )

            console.print("\n[green]✅ Login successful![/green]")
            console.print(f"사용자 이름: {user.get('name', 'N/A')}")
            console.print(f"사용자 이메일: {user.get('email', 'N/A')}")
            if result.get("expiresAt"):
                console.print(f"만료일: {result.get('expiresAt')}")
            return
        except Exception as e:
            console.print(f"[red]❌ Login failed: {e}[/red]")
            app_key = None
            attempt += 1
            if attempt < max_retries:
                console.print("Please try again with a valid app key.")

    console.print(f"[red]❌ Login failed after {max_retries} attempts[/red]")
    raise typer.Exit(1)
