"""Download commands for CLI."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from kitech_repository.core.client import KitechClient
from kitech_repository.core.exceptions import AuthenticationError, DownloadError

console = Console()
app = typer.Typer()


@app.command(name="file")
def download_file(
    repository_id: int = typer.Argument(..., help="Repository ID"),
    path: str | None = typer.Option(None, "--path", "-p", help="File or folder path to download"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress bar"),
):
    """Download a single file or folder from repository."""
    try:
        with KitechClient() as client:
            console.print("🔍 Getting download URL...")

            downloaded_path = client.download_file(
                repository_id=repository_id, path=path, output_dir=output, show_progress=not no_progress
            )

            console.print(f"[green]✅ Downloaded to: {downloaded_path}[/green]")
    except AuthenticationError:
        console.print("[red]❌ Authentication required. Please login first with:[/red]")
        console.print("  kitech auth login")
        raise typer.Exit(1)
    except DownloadError as e:
        console.print(f"[red]❌ Download failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="batch")
def download_batch(
    repository_id: int = typer.Argument(..., help="Repository ID"),
    paths: list[str] = typer.Argument(..., help="List of file/folder paths to download"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress bar"),
):
    """Download multiple files from repository."""
    try:
        with KitechClient() as client:
            console.print(f"📦 Preparing batch download for {len(paths)} items...")

            async def run_batch():
                return await client.download_batch(
                    repository_id=repository_id, paths=paths, output_dir=output, show_progress=not no_progress
                )

            downloaded_files = asyncio.run(run_batch())

            console.print(f"[green]✅ Downloaded {len(downloaded_files)} files successfully[/green]")
            for file in downloaded_files:
                console.print(f"  📄 {file.name}")
    except AuthenticationError:
        console.print("[red]❌ Authentication required. Please login first with:[/red]")
        console.print("  kitech auth login")
        raise typer.Exit(1)
    except DownloadError as e:
        console.print(f"[red]❌ Download failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="repo")
def download_repository(
    repository_id: int = typer.Argument(..., help="Repository ID"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress bar"),
):
    """Download entire repository."""
    try:
        with KitechClient() as client:
            console.print(f"📦 Downloading entire repository #{repository_id}...")

            downloaded_path = client.download_file(
                repository_id=repository_id, path=None, output_dir=output, show_progress=not no_progress
            )

            console.print(f"[green]✅ Repository downloaded to: {downloaded_path}[/green]")
    except AuthenticationError:
        console.print("[red]❌ Authentication required. Please login first with:[/red]")
        console.print("  kitech auth login")
        raise typer.Exit(1)
    except DownloadError as e:
        console.print(f"[red]❌ Download failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
