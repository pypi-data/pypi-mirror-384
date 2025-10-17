"""Authentication commands for CLI."""

import typer
from rich.console import Console
from rich.prompt import Prompt

from kitech_repository.cli.utils import get_cli_command_name
from kitech_repository.core.auth import AuthManager
from kitech_repository.core.client import KitechClient

console = Console(highlight=False)
app = typer.Typer()


@app.command()
def login(
    token: str = typer.Option(None, "--token", "-t", help="API token (will prompt if not provided)"),
    max_retries: int = typer.Option(3, "--retries", help="Maximum number of retry attempts"),
):
    """Login to KITECH Repository."""
    attempt = 0
    app_key = token  # Initialize from command line option
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

            # First save the app key temporarily
            auth_manager.login(app_key=app_key)

            # Test connection with the saved app key
            with KitechClient() as client:
                result = client.test_connection()

            # Update app key with user info
            user = result.get('user', {})
            auth_manager.login(
                app_key=app_key,
                user_id=result.get("userId"),
                expires_at=result.get("expiresAt"),  # If server provides expiry
            )

            console.print("[green]✅ Login successful![/green]")
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


@app.command()
def logout():
    """Logout from KITECH Repository."""
    try:
        auth_manager = AuthManager()
        if auth_manager.logout():
            console.print("[green]✅ Logged out successfully![/green]")
        else:
            console.print("⚠️ You were not logged in")
    except Exception as e:
        console.print(f"[red]❌ Logout failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Check authentication status."""
    try:
        auth_manager = AuthManager()
        if auth_manager.is_authenticated():
            with KitechClient() as client:
                result = client.test_connection()
                user = result.get('user', {})
                console.print("[green]✅ 인증됨[/green]")
                console.print(f"사용자 이름: {user.get('name', 'N/A')}")
                console.print(f"사용자 이메일: {user.get('email', 'N/A')}")
        else:
            cmd_name = get_cli_command_name()
            console.print("⚠️ 인증되지 않음")
            console.print(f"'{cmd_name} auth login' 명령어로 로그인하세요")
    except Exception as e:
        console.print(f"[red]❌ Error checking status: {e}[/red]")
        raise typer.Exit(1)
