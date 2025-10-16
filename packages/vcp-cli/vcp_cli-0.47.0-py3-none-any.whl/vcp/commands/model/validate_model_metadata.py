import sys
import traceback
from pathlib import Path
from typing import Optional

import click
import requests
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel

from ...config.config import Config
from ...utils.token import TokenManager

console = Console()


# The metadata validation POSTs up the files we're validating. The form field names
# we send the files up as MUST match the server's FastAPI args because it's looking
# for those names exactly and will error otherwise. These are those.
_YAML_FIELD_NAME = "yaml_file"
_MARKDOWN_FIELD_NAME = "markdown_file"


# Route in vcp-model-hub where we validate model metadata
MODEL_METADATA_VALIDATION_ROUTE = "/api/metadata/validate"


# Expected response structure from the model hub server
class ValidationResult(BaseModel):
    """Basic unit for validation results.

    Pulled from vcp-model-hub, circa Sep 2025"""

    valid: bool
    human_readable_error: str | None = None


class MetadataValidationResponse(BaseModel):
    """Validation status and any error messages for each metadata provided.

    Pulled from vcp-model-hub, circa Sep 2025"""

    yaml_validation_result: ValidationResult
    markdown_validation_result: ValidationResult


@click.command()
@click.option(
    "--yaml-metadata-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    default="model_card_metadata.yaml",
    help="Path to the YAML metadata file (default: model_card_metadata.yaml)",
)
@click.option(
    "--markdown-details-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    default="model_card_details.md",
    help="Path to the Markdown details file (default: model_card_details.md)",
)
@click.option("--config", "-c", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed debug information")
def validate_model_metadata_command(
    yaml_metadata_file: str,
    markdown_details_file: str,
    config: Optional[str] = None,
    verbose: bool = False,
):
    """Validates model metadata files against requirements in vcp-model-hub."""
    try:
        # Load configuration
        config_data = Config.load(config)

        # Check for valid tokens and get auth headers
        token_manager = TokenManager()
        headers = token_manager.get_auth_headers()
        if not headers:
            console.print("[red]Not logged in. Please run 'vcp login' first.[/red]")
            return

        yaml_path = Path(yaml_metadata_file)
        markdown_path = Path(markdown_details_file)
        endpoint = f"{config_data.models.base_url}{MODEL_METADATA_VALIDATION_ROUTE}"
        if verbose:
            console.print("\n[bold blue]Validation Details:[/bold blue]")
            console.print(f"YAML metadata: {yaml_path.absolute()}")
            console.print(f"Markdown details: {markdown_path.absolute()}")
            console.print(f"Endpoint: {endpoint}")

        console.print("\n[dim]Validating metadata files...[/dim]")
        with open(yaml_path, "rb") as yf, open(markdown_path, "rb") as mf:
            files = {
                _YAML_FIELD_NAME: (yaml_path.name, yf, "application/x-yaml"),
                _MARKDOWN_FIELD_NAME: (markdown_path.name, mf, "text/markdown"),
            }
            response = requests.post(endpoint, files=files, headers=headers)

        if verbose:
            console.print(
                f"\n[bold blue]Response status:[/bold blue] {response.status_code}"
            )
            # Try to show raw response, but truncate if too long
            MAX_RESPONSE_DISPLAY_CHARACTERS = 5_000
            response_text = response.text
            console.print("[bold blue]Raw response text:[/bold blue]")
            if len(response_text) < MAX_RESPONSE_DISPLAY_CHARACTERS:
                console.print(f"{response_text}", highlight=False)
            else:
                truncated = response_text[:MAX_RESPONSE_DISPLAY_CHARACTERS]
                chars_rem = len(response_text) - MAX_RESPONSE_DISPLAY_CHARACTERS
                console.print(
                    f"{truncated}[dim]... ({chars_rem} more characters)[/dim]",
                    highlight=False,
                )

        # Report validation results / error to user
        if response.status_code == 200:
            # 200 means all validations passed
            console.print(
                Panel(
                    "[green]✓ All metadata validations passed![/green]\n\n"
                    "Your metadata files are ready for submission.",
                    title="Success",
                    border_style="green",
                )
            )

        elif response.status_code == 422:
            # 422 means validation failed (but good request, server didn't error)
            # See vcp-model-hub `MetadataValidationResponse` for structure
            resp_data = MetadataValidationResponse(**response.json())
            yaml_validation_result = resp_data.yaml_validation_result
            markdown_validation_result = resp_data.markdown_validation_result

            if not yaml_validation_result.valid:
                console.print(
                    Panel(
                        yaml_validation_result.human_readable_error,
                        title="[red]YAML Validation Failed[/red]",
                        border_style="red",
                    )
                )

            if not markdown_validation_result.valid:
                if not yaml_validation_result.valid:
                    console.print()  # Space between error panels
                console.print(
                    Panel(
                        markdown_validation_result.human_readable_error,
                        title="[red]Markdown Validation Failed[/red]",
                        border_style="red",
                    )
                )

            console.print(
                "\n[yellow]Please fix the above and run validation again.[/yellow]"
            )
            sys.exit(2)

        else:
            # 400, 500, or other unexpected status
            # Default FastAPI error response is JSON with a "detail" field
            # Try to pull and display that, or fall back to raw response text.
            err_text = response.text
            try:
                err_data = response.json()
                if "detail" in err_data:
                    err_text = err_data["detail"]
            except requests.exceptions.JSONDecodeError:
                pass
            console.print(
                f"[red][bold]Validation request failed (status {response.status_code}):[/bold]\n"
                f"{err_text}[/red]"
            )
            sys.exit(1)

    except Exception as e:
        if verbose:
            console.print("\n[bold red]Detailed Error Information:[/bold red]")
            console.print(traceback.format_exc())
        console.print(f"[red]Error during metadata validation: {str(e)}[/red]")
