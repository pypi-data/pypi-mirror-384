import json
from typing import Literal, Optional

import click
from rich.console import Console

from ...config.config import Config
from ...utils.errors import with_error_handling
from .api import fetch_models_list
from .utils import format_models_table

console = Console()


@click.command(name="list")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (table or json)",
)
@click.option("--config", "-c", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed debug information")
@with_error_handling(resource_type="models", operation="model list")
def list_command(
    format: Literal["table", "json"],
    config: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """List available models and their versions from the VCP Model Hub API."""
    config_obj = Config.load(config)

    if verbose and format != "json":
        console.print(f"Model Hub Base URL: {config_obj.models.base_url}")

    response = fetch_models_list(modelhub_base_url=config_obj.models.base_url)

    if format == "json":
        console.print(json.dumps(response.model_dump(), indent=2))
    else:
        table = format_models_table(response.models)
        console.print(table)
