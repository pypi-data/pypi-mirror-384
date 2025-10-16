"""Version-related commands for the VCP CLI."""

import click
from rich.console import Console

from vcp.utils.version_check import check_for_updates, get_current_version


@click.command()
@click.option("--check", is_flag=True, help="Check for available updates on PyPI")
def version_command(check: bool) -> None:
    """Show version information and optionally check for updates."""
    console = Console()

    current_version = get_current_version()

    if check:
        console.print(f"Current version: {current_version}")
        console.print("Checking for updates...", style="dim")

        is_update_available, message = check_for_updates()

        if is_update_available:
            console.print(f"⚠️  {message}", style="yellow")
            console.print(
                "Run 'pip install --upgrade vcp-cli' to update", style="dim yellow"
            )
        else:
            console.print(message, style="green")
    else:
        console.print(f"vcp-cli version {current_version}")
