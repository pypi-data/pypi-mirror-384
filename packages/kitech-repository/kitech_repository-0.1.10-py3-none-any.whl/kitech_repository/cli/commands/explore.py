"""Interactive explore commands for CLI."""

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from kitech_repository.core.client import KitechClient
from kitech_repository.core.exceptions import AuthenticationError

console = Console(highlight=False)
app = typer.Typer()


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def display_repositories(repositories):
    """Display repositories in table format with numbers for selection."""
    from rich.table import Table

    table = Table(title="📦 Repository 목록", header_style="", border_style="")
    table.add_column("번호", width=4)
    table.add_column("이름")
    table.add_column("소유자")
    table.add_column("공개여부", width=8)

    for i, repo in enumerate(repositories, 1):
        status = "공개" if repo.is_public else "비공개"

        table.add_row(str(i), repo.name, repo.owner_name, status)

    console.print("\n")
    console.print(table)
    console.print()


def display_files(files, repository_name, current_path=""):
    """Display files in table format with numbers for selection."""
    from rich.table import Table

    title = f"📁 Repository: {repository_name}"
    if current_path:
        title += f" / {current_path}"

    table = Table(title=title, header_style="", border_style="")
    table.add_column("번호", width=4)
    table.add_column("타입", width=4)
    table.add_column("이름")
    table.add_column("크기", width=12, justify="right")

    for i, file in enumerate(files, 1):
        if file.is_directory:
            table.add_row(str(i), "📁", f"{file.name}/", "-")
        else:
            table.add_row(str(i), "📄", file.name, format_size(file.size))

    console.print("\n")
    console.print(table)
    console.print()


@app.command()
def start():
    """Start interactive repository exploration."""
    try:
        with KitechClient() as client:
            while True:
                # Get repositories
                console.print("[green]🔍 Repository 목록을 가져오는 중...[/green]")
                result = client.list_repositories(limit=50, include_shared=True)

                if not result["repositories"]:
                    console.print("[red]❌ 접근 가능한 Repository가 없습니다.[/red]")
                    return

                repositories = result["repositories"]
                display_repositories(repositories)

                # Repository selection
                while True:
                    choice = Prompt.ask(f"Repository 선택 (1-{len(repositories)}) 또는 'exit'", default="exit")

                    if choice.lower() == "exit":
                        console.print("👋 탐색을 종료합니다.")
                        return

                    try:
                        repo_index = int(choice) - 1
                        if 0 <= repo_index < len(repositories):
                            selected_repo = repositories[repo_index]
                            break
                        else:
                            console.print(f"[red]❌ 1-{len(repositories)} 범위의 숫자를 입력하세요.[/red]")
                    except ValueError:
                        console.print("[red]❌ 올바른 숫자를 입력하세요.[/red]")

                # Explore selected repository
                explore_repository(client, selected_repo)

                # Ask if continue
                if not Confirm.ask("\n다른 Repository를 탐색하시겠습니까?"):
                    console.print("👋 탐색을 종료합니다.")
                    break

    except AuthenticationError:
        console.print("[red]❌ 인증이 필요합니다. 먼저 로그인하세요:[/red]")
        console.print("  kitech auth login")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 오류 발생: {e}[/red]")
        raise typer.Exit(1)


def explore_repository(client, repository):
    """Explore files in a repository."""
    current_path = ""
    path_history = []

    while True:
        try:
            # Get files in current path
            console.print("[green]🔍 파일 목록을 가져오는 중...[/green]")
            result = client.list_files(repository.id, prefix=current_path)

            if not result["files"]:
                console.print("[yellow]⚠️ 이 경로에는 파일이 없습니다.[/yellow]")
                if not path_history:
                    break
                current_path = path_history.pop()
                continue

            files = result["files"]
            display_files(files, repository.name, current_path)

            # Show navigation options
            options = []
            if path_history:
                options.append("'back' (상위 폴더)")
            options.append("'download' (현재 폴더 전체 다운로드)")
            options.append("'list' (Repository 목록으로)")
            options.append("'exit' (종료)")

            options_str = " | ".join(options)
            console.print(f"\n💡 옵션: {options_str}")

            # File/folder selection
            while True:
                choice = Prompt.ask(f"선택 (1-{len(files)}) 또는 명령어", default="back" if path_history else "list")

                if choice.lower() == "exit":
                    console.print("👋 탐색을 종료합니다.")
                    raise typer.Exit(0)
                elif choice.lower() == "list":
                    return
                elif choice.lower() == "back" and path_history:
                    current_path = path_history.pop()
                    break
                elif choice.lower() == "back":
                    console.print("[yellow]⚠️ 이미 루트 경로입니다.[/yellow]")
                    continue
                elif choice.lower() == "download":
                    # Download current folder or entire repository
                    download_path = current_path if current_path else None
                    download_name = current_path.split("/")[-1] if current_path else repository.name

                    if Confirm.ask(f"'{download_name}' 전체를 다운로드하시겠습니까?"):
                        console.print(f"[green]📥 {download_name} 다운로드를 시작합니다...[/green]")
                        try:
                            downloaded_path = client.download_file(
                                repository_id=repository.id, path=download_path, show_progress=True
                            )
                            console.print(f"[green]✅ 다운로드 완료: {downloaded_path}[/green]")
                        except Exception as e:
                            console.print(f"[red]❌ 다운로드 실패: {e}[/red]")
                    continue

                try:
                    file_index = int(choice) - 1
                    if 0 <= file_index < len(files):
                        selected_file = files[file_index]

                        if selected_file.is_directory:
                            # Enter directory
                            path_history.append(current_path)
                            current_path = selected_file.path
                            break
                        else:
                            # Handle file selection
                            console.print(f"\n📄 선택된 파일: {selected_file.name}")
                            console.print(f"📏 크기: {format_size(selected_file.size)}")
                            console.print(f"📍 경로: {selected_file.path}")

                            if Confirm.ask("이 파일을 다운로드하시겠습니까?"):
                                console.print(f"[green]📥 {selected_file.name} 다운로드를 시작합니다...[/green]")
                                try:
                                    downloaded_path = client.download_file(
                                        repository_id=repository.id, path=selected_file.path, show_progress=True
                                    )
                                    console.print(f"[green]✅ 다운로드 완료: {downloaded_path}[/green]")
                                except Exception as e:
                                    console.print(f"[red]❌ 다운로드 실패: {e}[/red]")
                            break
                    else:
                        console.print(f"[red]❌ 1-{len(files)} 범위의 숫자를 입력하세요.[/red]")
                except ValueError:
                    console.print("[red]❌ 올바른 숫자 또는 명령어를 입력하세요.[/red]")

        except Exception as e:
            console.print(f"[red]❌ 오류 발생: {e}[/red]")
            break
