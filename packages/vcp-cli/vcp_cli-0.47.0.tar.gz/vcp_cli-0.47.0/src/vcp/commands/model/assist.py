"""
VCP CLI Model Assist Command

This command provides model submission status checking and guidance for the VCP model workflow.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from ...config.config import Config
from .workflow_assistant import get_workflow_assistant

console = Console()


@click.command()
@click.option(
    "--work-dir",
    help="Path to the model repository work directory (defaults to current directory)",
)
@click.option(
    "--step",
    type=click.Choice([
        "init",
        "status",
        "metadata",
        "weights",
        "package",
        "stage",
        "submit",
    ]),
    help="Get detailed guidance for a specific workflow step",
)
@click.option("--config", "-c", help="Path to config file")
def assist_command(work_dir: str = None, step: str = None, config: str = None):
    """Check model submission status and get guidance for VCP model commands.

    This command helps you understand where you are in the model submission
    process and what the next steps should be.

    \b
    Examples:
    • vcp model assist                    # Check current directory status
    • vcp model assist --work-dir ./my-model  # Check specific work directory
    • vcp model assist --step init        # Get init step guidance
    • vcp model assist --step metadata    # Get metadata step guidance
    • vcp model assist --step stage       # Get stage step guidance
    • vcp model assist --step submit      # Get submit step guidance
    """
    try:
        # Use current directory if work_dir not specified
        if not work_dir:
            work_dir = str(Path.cwd())

        # Load config (same pattern as other model commands)
        config_data = Config.load(config)

        # Get workflow assistant with config
        assistant = get_workflow_assistant(config_data)

        if step:
            # Show specific step guidance
            guidance = assistant.get_step_guidance(step, work_dir)
            console.print(
                Panel(
                    guidance,
                    title=f"[bold blue]Step Guidance: {step.upper()}[/bold blue]",
                )
            )
        else:
            # Show workflow status
            assistant.display_workflow_status(work_dir)

    except Exception as e:
        console.print(f"[red]Error checking model submission status: {e}[/red]")
