"""Cache management commands for vcp-cli."""

import click
from rich.console import Console
from rich.table import Table

from ..utils.cache import (
    clean_upload_state,
    clear_cache,
    get_benchmark_cache_dir,
    get_cache_size,
    get_upload_cache_dir,
    get_vcp_cache_dir,
    get_version_cache_dir,
    list_upload_history,
)

console = Console()


@click.group()
def cache_command():
    """Manage vcp-cli cache and upload state."""
    pass


@cache_command.command("info")
def cache_info():
    """Show cache information and statistics."""
    try:
        cache_dir = get_vcp_cache_dir()
        sizes = get_cache_size()

        # Create info table
        table = Table(title="VCP CLI Cache Information")
        table.add_column("Component", style="cyan")
        table.add_column("Location", style="yellow")
        table.add_column("Size", style="green")

        def format_size(bytes_size):
            """Format bytes to human readable size."""
            for unit in ["B", "KB", "MB", "GB"]:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.1f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.1f} TB"

        table.add_row("Total Cache", str(cache_dir), format_size(sizes["total"]))
        table.add_row(
            "Upload States", str(get_upload_cache_dir()), format_size(sizes["uploads"])
        )
        table.add_row(
            "Benchmarks",
            str(get_benchmark_cache_dir()),
            format_size(sizes["benchmarks"]),
        )
        table.add_row(
            "Version Checks",
            str(get_version_cache_dir()),
            format_size(sizes["version"]),
        )

        console.print(table)

        # Show recent upload history
        history = list_upload_history(5)
        if history:
            console.print("\n[bold]Recent Upload History:[/bold]")
            for i, upload in enumerate(history, 1):
                model = upload.get("model", "Unknown")
                version = upload.get("version", "Unknown")
                last_updated = upload.get("last_updated", "Unknown")
                completed = len(upload.get("completed_files", []))
                failed = len(upload.get("failed_files", []))

                status = (
                    "✅ Complete"
                    if failed == 0 and completed > 0
                    else f"⚠️  {failed} failed"
                )
                console.print(
                    f"  {i}. {model} v{version} - {completed} files - {status}"
                )
                console.print(f"     Last updated: {last_updated}")

    except Exception as e:
        console.print(f"[red]Error getting cache info: {str(e)}[/red]")


@cache_command.command("clear")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["all", "uploads", "benchmarks", "version"]),
    default="all",
    help="Type of cache to clear",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def cache_clear(type: str, force: bool):
    """Clear cache data."""
    try:
        if type == "all":
            cache_type = None
            message = "all cache data"
        else:
            cache_type = type
            message = f"{type} cache data"

        if not force:
            if not click.confirm(f"Are you sure you want to clear {message}?"):
                console.print("Cache clear cancelled.")
                return

        success = clear_cache(cache_type)

        if success:
            console.print(f"[green]✅ Successfully cleared {message}[/green]")
        else:
            console.print(f"[red]❌ Failed to clear {message}[/red]")

    except Exception as e:
        console.print(f"[red]Error clearing cache: {str(e)}[/red]")


@cache_command.command("history")
@click.option("--limit", "-l", default=10, help="Number of recent uploads to show")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def cache_history(limit: int, verbose: bool):
    """Show upload history from cache."""
    try:
        history = list_upload_history(limit)

        if not history:
            console.print("[yellow]No upload history found in cache.[/yellow]")
            return

        console.print(f"[bold]Upload History (last {len(history)} uploads):[/bold]\n")

        for i, upload in enumerate(history, 1):
            model = upload.get("model", "Unknown")
            version = upload.get("version", "Unknown")
            data_path = upload.get("data_path", "Unknown")
            last_updated = upload.get("last_updated", "Unknown")
            started_at = upload.get("started_at", "Unknown")
            completed = upload.get("completed_files", [])
            failed = upload.get("failed_files", [])

            # Status determination
            if len(failed) == 0 and len(completed) > 0:
                status = "[green]✅ Complete[/green]"
            elif len(failed) > 0:
                status = f"[red]❌ {len(failed)} failed[/red]"
            else:
                status = "[yellow]⏳ In progress[/yellow]"

            console.print(f"[bold cyan]{i}. {model} v{version}[/bold cyan] {status}")
            console.print(f"   Files: {len(completed)} completed, {len(failed)} failed")
            console.print(f"   Last updated: {last_updated}")

            if verbose:
                console.print(f"   Data path: {data_path}")
                console.print(f"   Started: {started_at}")
                if failed:
                    console.print(f"   Failed files: {', '.join(failed[:3])}")
                    if len(failed) > 3:
                        console.print(f"   ... and {len(failed) - 3} more")

            console.print()  # Empty line between entries

    except Exception as e:
        console.print(f"[red]Error getting upload history: {str(e)}[/red]")


@cache_command.command("clean-uploads")
@click.option("--model", "-m", help="Clean uploads for specific model")
@click.option("--version", "-v", help="Clean uploads for specific version")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def cache_clean_uploads(model: str, version: str, force: bool):
    """Clean specific upload states from cache."""
    try:
        if model and version:
            message = f"upload state for {model} v{version}"
        elif model:
            message = f"all upload states for model {model}"
        else:
            message = "all upload states"

        if not force:
            if not click.confirm(f"Are you sure you want to clean {message}?"):
                console.print("Upload state cleanup cancelled.")
                return

        if model and version:
            success = clean_upload_state(model, version)
            if success:
                console.print(
                    f"[green]✅ Cleaned upload state for {model} v{version}[/green]"
                )
            else:
                console.print(
                    f"[yellow]No upload state found for {model} v{version}[/yellow]"
                )
        else:
            # Clean all uploads or all for a model
            success = clear_cache("uploads")
            if success:
                console.print(f"[green]✅ Cleaned {message}[/green]")
            else:
                console.print(f"[red]❌ Failed to clean {message}[/red]")

    except Exception as e:
        console.print(f"[red]Error cleaning upload states: {str(e)}[/red]")


# Add help text
cache_command.help = """
Manage vcp-cli cache and upload state.

The cache is used for embeddings, benchmark results, uploads
(to allow resuming upon interruption), and new version checks

\b
Examples:
  vcp cache info                    # Show cache information
  vcp cache clear --type uploads    # Clear upload states
  vcp cache history --limit 5       # Show last 5 uploads
  vcp cache clean-uploads -m model1 -v 1.0  # Clean specific upload
"""
