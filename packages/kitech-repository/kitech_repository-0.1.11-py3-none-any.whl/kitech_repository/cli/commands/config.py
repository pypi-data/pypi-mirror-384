"""Configuration commands for CLI."""

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from kitech_repository.core.config import Config

console = Console(highlight=False)
app = typer.Typer()


@app.callback(invoke_without_command=True)
def config(ctx: typer.Context):
    """Show current configuration."""
    # If a subcommand is being invoked, skip the default behavior
    if ctx.invoked_subcommand is not None:
        return

    try:
        config_obj = Config.load()
        config_file = config_obj.config_dir / "config.json"

        table = Table(title="KITECH Configuration", show_header=True, header_style="bold cyan")
        table.add_column("Setting", style="dim", width=20)
        table.add_column("Value")

        table.add_row("API Base URL", config_obj.api_base_url)
        table.add_row("Chunk Size", f"{config_obj.chunk_size} bytes")
        table.add_row("Config Directory", str(config_obj.config_dir))
        table.add_row("Download Directory", str(config_obj.download_dir))
        table.add_row("Config File", str(config_file))
        table.add_row("Config File Exists", "✅ Yes" if config_file.exists() else "❌ No (using defaults)")
        table.add_row("", "")  # Empty row for visual separation
        table.add_row("Note", "API version is set at runtime (default: v1)")

        console.print(table)
    except Exception as e:
        console.print(f"[red]❌ Failed to load config: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def reset():
    """Reset configuration to defaults."""
    try:
        config_obj = Config.load()
        config_file = config_obj.config_dir / "config.json"

        if config_file.exists():
            # Confirm with user
            confirm = Prompt.ask(
                f"Are you sure you want to delete {config_file}?", choices=["y", "n"], default="n"
            )

            if confirm.lower() == "y":
                config_file.unlink()
                console.print("[green]✅ Configuration reset to defaults[/green]")

                # Show default config
                default_config = Config()
                console.print(f"\nDefault API Base URL: {default_config.api_base_url}")
            else:
                console.print("Reset cancelled")
        else:
            console.print("⚠️ No config file found - already using defaults")
    except Exception as e:
        console.print(f"[red]❌ Failed to reset config: {e}[/red]")
        raise typer.Exit(1)
