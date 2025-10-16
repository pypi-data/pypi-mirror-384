"""VCP CLI Model Status Command

This command queries the VCP Model Hub API to get the status of all model submissions.
"""

import json
import traceback
from pathlib import Path
from typing import Optional

import click
import requests
from rich.console import Console
from rich.table import Table

from ...config.config import Config
from ...utils.token import TokenManager

console = Console()


@click.command()
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (table or json)",
)
@click.option("--config", "-c", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed debug information")
@click.option(
    "--work-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the model repository work directory where model configuration is located",
)
# --username is a hidden flag for testing purposes
# user will not see this flag in the help message
# this is for internal testing purposes
@click.option(
    "--username",
    hidden=True,  # Hidden flag for testing purposes
    help="Filter by username (testing purposes only)",
)
def status_command(
    format: str,
    config: Optional[str] = None,
    verbose: bool = False,
    work_dir: Optional[str] = None,
    username: Optional[str] = None,
):
    """Query and display the status of all model submissions from the VCP Model Hub.

    This command shows the current status of all models that have been initialized
    or submitted to the VCP Model Hub.

    \b
    Examples:
    • vcp model status                    # Show all submissions in table format
    • vcp model status --format json     # Show all submissions in JSON format
    • vcp model status --verbose         # Show detailed debug information
    """
    try:
        # Load configuration
        config_data = Config.load(config)

        if verbose:
            console.print("\n[bold blue]Configuration loaded:[/bold blue]")
            console.print(f"Base URL: {config_data.models.base_url}")

        # Check for valid tokens and get auth headers
        token_manager = TokenManager()
        headers = token_manager.get_auth_headers()

        if not headers:
            console.print("[red]Not logged in. Please run 'vcp login' first.[/red]")
            return

        # Build the API URL
        url = f"{config_data.models.base_url}/api/models/status"

        # Add username query parameter if provided (for testing)
        params = {}
        if username:
            params["username"] = username
            if verbose:
                console.print(
                    f"[yellow]Testing mode: Filtering by username: {username}[/yellow]"
                )

        if verbose:
            console.print("\n[bold blue]Debug Information:[/bold blue]")
            console.print(f"API URL: {url}")
            if params:
                console.print(f"Query Parameters: {params}")

        # Make API request
        response = requests.get(url, headers=headers, params=params)

        if verbose:
            console.print(f"Response Status Code: {response.status_code}")

        if response.status_code != 200:
            console.print(f"[red]Error: {response.text}[/red]")
            return

        response_data = response.json()

        if verbose:
            console.print(
                f"Retrieved {len(response_data.get('submissions', []))} submissions"
            )

        # Display results
        if format == "json":
            console.print(json.dumps(response_data, indent=2))
        else:
            # Create table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Model Name", style="cyan", no_wrap=True)
            table.add_column("Version", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Feedback", style="white", max_width=50)

            # Add status styling
            status_styles = {
                "repository_created": "yellow",
                "initialized": "blue",
                "submitted": "green",
                "pending": "blue",
                "failed": "red",
                "processing": "blue",
                "under_review": "magenta",
                "accepted": "green",
                "denied": "red",
            }

            submissions = response_data.get("submissions", [])
            total_count = response_data.get("total_count", len(submissions))

            for submission in submissions:
                model_name = submission.get("model_name", "Unknown")
                model_version = submission.get("model_version", "Unknown")
                status = submission.get("status", "Unknown")

                # Apply status-specific styling
                status_style = status_styles.get(status, "white")

                # Get feedback for under_review submissions
                feedback_text = ""
                if status == "under_review":
                    feedback_text = "[yellow]Unresolved Feedback Comments[/yellow]"

                table.add_row(
                    model_name,
                    model_version,
                    f"[{status_style}]{status}[/{status_style}]",
                    feedback_text,
                )

            console.print(table)
            console.print(f"\n[green]Total submissions: {total_count}[/green]")

            # Update model metadata to indicate that status command was run
            # This helps the workflow assistant know that the status step is completed
            try:
                # Determine work directory to use
                if work_dir:
                    work_dir_path = Path(work_dir)
                else:
                    # Check current directory first, then look for metadata file
                    current_dir = Path.cwd()
                    current_metadata_file = current_dir / ".model-metadata"

                    if current_metadata_file.exists():
                        work_dir_path = current_dir
                    else:
                        # No metadata in current directory, skip metadata update
                        if verbose:
                            console.print(
                                "[yellow]Debug: No metadata file found in current directory, skipping metadata update[/yellow]"
                            )
                        work_dir_path = None

                if work_dir_path:
                    metadata_file = work_dir_path / ".model-metadata"

                if verbose:
                    console.print(
                        f"[blue]Debug: Looking for metadata file at: {metadata_file}[/blue]"
                    )
                    console.print(
                        f"[blue]Debug: Metadata file exists: {metadata_file.exists()}[/blue]"
                    )

                if metadata_file.exists():
                    if verbose:
                        # Read existing metadata for debug info only
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        console.print(
                            f"[blue]Debug: Current metadata: {metadata}[/blue]"
                        )
                        console.print(
                            f"[blue]Debug: Resubmit flag: {metadata.get('resubmit', False)}[/blue]"
                        )
                else:
                    if verbose:
                        console.print(
                            f"[yellow]Debug: No metadata file found at {metadata_file}[/yellow]"
                        )
            except Exception as e:
                if verbose:
                    console.print(f"[red]Debug: Error updating metadata: {e}[/red]")
                # If we can't update the metadata, it's not critical
                pass

            # Show simple message for under_review submissions
            under_review_submissions = [
                s for s in submissions if s.get("status") == "under_review"
            ]
            if under_review_submissions:
                for submission in under_review_submissions:
                    model_name = submission.get("model_name", "Unknown")
                    model_version = submission.get("model_version", "Unknown")

                    console.print(f"\n[bold cyan]Model: {model_name}[/bold cyan]")
                    console.print(f"[dim]Version: {model_version}[/dim]")
                    console.print(
                        "[yellow]Review comments have been posted on your submission, please check your email for details.[/yellow]"
                    )

            # Show status legend
            console.print("\n[bold]Status Legend:[/bold]")
            console.print("[blue]initialized[/blue] - Model has been initialized")
            console.print("[green]submitted[/green] - Model submitted to VCP Model Hub")
            console.print(
                "[magenta]under_review[/magenta] - Model under review (check feedback column)"
            )
            console.print("[green]accepted[/green] - Model has been accepted")
            console.print("[red]denied[/red] - Model has been denied")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error communicating with VCP Model Hub API: {e}[/red]")
        if verbose:
            console.print(
                f"[red]Response: {getattr(e, 'response', {}).text if hasattr(e, 'response') else 'No response'}[/red]"
            )
        console.print("[yellow]Recovery suggestions:[/yellow]")
        console.print("  • Check your internet connection")
        console.print("  • Verify you're logged in: vcp login")
        console.print("  • Try again in a few moments")
    except Exception as e:
        console.print(f"[red]Error querying model status: {e}[/red]")
        if verbose:
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
