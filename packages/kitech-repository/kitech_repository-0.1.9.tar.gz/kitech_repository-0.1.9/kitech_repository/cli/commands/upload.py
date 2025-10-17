"""Upload commands for CLI."""

from pathlib import Path

import typer
from rich.console import Console

from kitech_repository.core.client import KitechClient
from kitech_repository.core.exceptions import AuthenticationError, UploadError

console = Console()
app = typer.Typer()


@app.command()
def file(
    repository_id: int = typer.Argument(..., help="Repository ID"),
    file_path: Path = typer.Argument(..., help="Path to file to upload", exists=True),
    remote_path: str | None = typer.Option("", "--path", "-p", help="Remote path/folder in repository"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress bar"),
):
    """Upload a file to repository."""
    try:
        if not file_path.is_file():
            console.print(f"[red]❌ {file_path} is not a file[/red]")
            raise typer.Exit(1)

        with KitechClient() as client:
            console.print(f"📤 Uploading {file_path.name}...")

            result = client.upload_file(
                repository_id=repository_id, file_path=file_path, remote_path=remote_path, show_progress=not no_progress
            )

            console.print("[green]✅ Upload successful![/green]")
            console.print(f"   File: {result.get('fileName')}")
            console.print(f"   Size: {result.get('fileSize')} bytes")
            if remote_path:
                console.print(f"   Path: {remote_path}")
    except AuthenticationError:
        console.print("[red]❌ Authentication required. Please login first with:[/red]")
        console.print("  kitech auth login")
        raise typer.Exit(1)
    except UploadError as e:
        console.print(f"[red]❌ Upload failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def directory(
    repository_id: int = typer.Argument(..., help="Repository ID"),
    directory_path: Path = typer.Argument(..., help="Path to directory to upload", exists=True),
    remote_path: str | None = typer.Option("", "--path", "-p", help="Remote path/folder in repository"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress bar"),
):
    """Upload all files from a directory to repository."""
    try:
        if not directory_path.is_dir():
            console.print(f"[red]❌ {directory_path} is not a directory[/red]")
            raise typer.Exit(1)

        files = list(directory_path.glob("**/*"))
        files = [f for f in files if f.is_file()]

        if not files:
            console.print(f"[yellow]⚠️ No files found in {directory_path}[/yellow]")
            return

        console.print(f"📤 Uploading {len(files)} files from {directory_path.name}...")

        with KitechClient() as client:
            uploaded = 0
            failed = 0

            for file_path in files:
                relative_path = file_path.relative_to(directory_path)
                full_remote_path = f"{remote_path}/{relative_path}".replace("\\", "/").strip("/")

                try:
                    console.print(f"  📄 Uploading {relative_path}...")
                    client.upload_file(
                        repository_id=repository_id,
                        file_path=file_path,
                        remote_path=full_remote_path,
                        show_progress=False,
                    )
                    uploaded += 1
                except Exception as e:
                    console.print(f"    [red]❌ Failed: {e}[/red]")
                    failed += 1

        console.print("\n[green]✅ Upload complete![/green]")
        console.print(f"   Uploaded: {uploaded} files")
        if failed > 0:
            console.print(f"   Failed: {failed} files")
    except AuthenticationError:
        console.print("[red]❌ Authentication required. Please login first with:[/red]")
        console.print("  kitech auth login")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
