"""File manager command for CLI."""

import typer
from rich.console import Console
from rich.prompt import Prompt

from kitech_repository.cli.utils import get_cli_command_name
from kitech_repository.core.auth import AuthManager
from kitech_repository.core.client import KitechClient
from kitech_repository.core.exceptions import AuthenticationError
from kitech_repository.tui import KitechTUI

console = Console(highlight=False)
app = typer.Typer()

# Constants
REPOSITORIES_PER_PAGE = 50


def _select_repository_with_pagination(client):
    """Select repository with pagination support."""
    page = 0

    while True:
        console.print(f"[green]🔍 Loading repositories (page {page + 1})...[/green]")
        result = client.list_repositories(page=page, limit=REPOSITORIES_PER_PAGE)
        repositories = result["repositories"]
        total_count = result.get("total_count", 0)

        if not repositories:
            if page == 0:
                console.print("[red]❌ No repositories found.[/red]")
                return None
            else:
                console.print("[yellow]⚠️ No more repositories.[/yellow]")
                page -= 1  # Go back to previous page
                continue

        # Display repositories as table
        from rich.box import SQUARE
        from rich.table import Table

        total_pages = (total_count + REPOSITORIES_PER_PAGE - 1) // REPOSITORIES_PER_PAGE
        table = Table(
            title=f"🗂️  전체 리포지토리 (전체 {total_count}개 - {page + 1}/{total_pages} 페이지)", box=SQUARE, show_header=True, header_style="none"
        )
        table.add_column("번호", width=6, style="none")
        table.add_column("리포지토리 이름", style="none")
        table.add_column("소유자", style="none")
        table.add_column("공개여부", width=10, style="none")
        table.add_column("내 권한", width=10, style="none")

        for i, repo in enumerate(repositories, page * REPOSITORIES_PER_PAGE + 1):
            status = "공개" if repo.is_public else "비공개"

            # Convert role to Korean
            role = repo.user_role if hasattr(repo, "user_role") else "VIEWER"
            role_map = {"OWNER": "소유자", "ADMIN": "관리자", "VIEWER": "뷰어", "NONE": "없음"}
            user_role = role_map.get(role.upper(), role)

            table.add_row(str(i), repo.name, repo.owner_name, status, user_role)

        console.print("\n")
        console.print(table)

        # Get user selection
        while True:
            start_num = page * REPOSITORIES_PER_PAGE + 1
            end_num = page * REPOSITORIES_PER_PAGE + len(repositories)
            options = [f"{start_num}" if len(repositories) == 1 else f"{start_num}-{end_num}"]
            if page > 0:
                options.append("prev")
            if (page + 1) * REPOSITORIES_PER_PAGE < total_count:
                options.append("next")
            options.append("exit")

            options_str = " / ".join(options)
            choice = Prompt.ask(
                f"\n리포지토리 번호 입력 ({options_str})", default=str(start_num) if repositories else "exit"
            )

            if choice.lower() == "exit":
                console.print("👋 Cancelled.")
                return None
            elif choice.lower() == "next" and (page + 1) * REPOSITORIES_PER_PAGE < total_count:
                page += 1
                break
            elif choice.lower() == "prev" and page > 0:
                page -= 1
                break
            else:
                try:
                    repo_num = int(choice)
                    # Convert global repo number to page index
                    repo_index = repo_num - (page * REPOSITORIES_PER_PAGE + 1)
                    if 0 <= repo_index < len(repositories):
                        return repositories[repo_index]
                    else:
                        console.print(f"[red]❌ Please enter number {start_num}-{end_num}[/red]")
                except ValueError:
                    console.print(f"[red]❌ Invalid input. Use: {options_str}[/red]")


@app.command()
def start():
    """Start dual-panel file manager."""
    try:
        # Check authentication first
        auth_manager = AuthManager()
        if not auth_manager.is_authenticated():
            cmd_name = get_cli_command_name()
            console.print("[red]❌ 로그인 정보가 없습니다.[/red]")
            console.print(f"먼저 로그인하세요: {cmd_name} auth login")
            raise typer.Exit(1)

        # First, let user select repository with pagination
        with KitechClient() as client:
            selected_repo = _select_repository_with_pagination(client)
            if not selected_repo:
                return

            console.print(f"\n🚀 Starting file manager for: {selected_repo.name}")

            # Start new Textual TUI with selected repository
            tui_app = KitechTUI(client=client, initial_repo_id=selected_repo.id)
            tui_app.run()

    except AuthenticationError:
        cmd_name = get_cli_command_name()
        console.print("[red]❌ 인증 오류[/red]")
        console.print(f"먼저 로그인하세요: [cyan]{cmd_name} auth login[/cyan]")
        raise typer.Exit(1)
    except typer.Exit:
        # Re-raise typer.Exit without showing error trace
        raise
    except KeyboardInterrupt:
        console.print("\n👋 File manager closed.")
    except Exception as e:
        import traceback

        console.print(f"[red]❌ Error: {e}[/red]")
        console.print(f"[red]Type: {type(e).__name__}[/red]")
        console.print(f"[red]Details: {traceback.format_exc()}[/red]")
        raise typer.Exit(1)
