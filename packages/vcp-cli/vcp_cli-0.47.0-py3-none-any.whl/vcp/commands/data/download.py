from urllib.parse import urlparse

import click
from rich.console import Console

from vcp.commands.data.search import search_command
from vcp.datasets.api import DatasetSizeModel, LocationModel, get_dataset_api
from vcp.datasets.download import S3Credentials, download_locations
from vcp.utils.errors import (
    check_authentication_status,
    validate_dataset_id,
    with_error_handling,
)
from vcp.utils.size import (
    calculate_total_dataset_size,
    format_size_bytes,
    get_file_count_from_dataset,
)
from vcp.utils.token import TokenManager

console = Console()

TOKEN_MANAGER = TokenManager()

EPILOG = f"""
{click.style("Examples:", fg="cyan", bold=True)} \n
- Download a {click.style("SINGLE", bold=True)} dataset by its exact ID\n
\t {click.style("vcp data download --id $DATASET_ID", fg="green")} \n
- Download {click.style("MULTIPLE", bold=True)} datasets matching a search query\n
\t {click.style("vcp data download --query $QUERY", fg="green")} \n
\t ... equivalent to {click.style("vcp data search $QUERY --download", fg="green")} \n
"""


def has_s3_locations(locations):
    """Check if any location contains S3 URLs."""
    for loc in locations:
        if isinstance(loc, LocationModel):
            if loc.scheme == "s3":
                return True
        elif isinstance(loc, DatasetSizeModel):
            if urlparse(loc.url).scheme == "s3":
                return True
        else:
            # Handle string URLs
            if urlparse(str(loc)).scheme == "s3":
                return True
    return False


@click.command(
    "download",
    epilog=EPILOG,
    context_settings={"ignore_unknown_options": False, "allow_extra_args": True},
)
@click.option(
    "--id",
    "dataset_id",
    default=None,
    help="Dataset ID to download a single dataset",
)
@click.option(
    "--query", "-q", default=None, help="Search query to download multiple datasets"
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=str),
    default=".",
    help="Directory to write the files.",
)
@click.option(
    "--exact",
    "-e",
    default=False,
    help="Use exact match when passing --query",
    is_flag=True,
)
@click.pass_context
@with_error_handling(resource_type="dataset", operation="data download")
def download_command(ctx, dataset_id: str, query: str, outdir: str, exact: bool):
    """
    Download dataset(s) by ID or search query. At least one of --id or --query is required.
    """
    # Check for extra args (likely someone using old positional syntax)
    if ctx.args:
        raise click.UsageError(
            f"Unexpected argument(s): {' '.join(ctx.args)}\n\n"
            "Use '--id DATASET_ID' to download a specific dataset, or '--query SEARCH_QUERY' to search and download."
        )

    # Validate that at least one of --id or --query is provided
    if dataset_id is None and query is None:
        raise click.UsageError(
            "At least one of --id or --query must be provided.\n"
            "Use '--id DATASET_ID' to download a specific dataset, or '--query SEARCH_QUERY' to search and download."
        )

    # If query is provided, delegate to search command
    if query is not None:
        ctx.invoke(search_command, term=query, download=True, exact=exact)
        return

    # Validate dataset ID
    validate_dataset_id(dataset_id, "data download")

    # session management
    tokens = TOKEN_MANAGER.load_tokens()
    check_authentication_status(tokens, "data download")

    # call data api
    data = get_dataset_api(tokens.id_token, dataset_id, download=True)

    if getattr(data, "credentials", None) is None and has_s3_locations(data.locations):
        console.print(
            f"[red]Error: Failed to get S3 credentials to download dataset {dataset_id}[/red]"
        )
        return None
    else:
        # Calculate and display size information
        total_size = calculate_total_dataset_size(data)
        file_count = get_file_count_from_dataset(data)

        if total_size > 0:
            size_display = format_size_bytes(total_size)
            if file_count > 0:
                console.print(
                    f"Total download size: {size_display} ({file_count} files)"
                )
            else:
                console.print(f"Total download size: {size_display}")
        else:
            if file_count > 0:
                console.print(
                    f"Dataset contains {file_count} files (size information not available)"
                )
            else:
                console.print("Download size information not available")

        # Ask for confirmation
        if not click.confirm("Continue with download?", default=True):
            console.print("Download cancelled.")
            return None

        # Only create S3Credentials if they exist, otherwise pass None
        credentials = S3Credentials(**data.credentials) if data.credentials else None
        download_locations(data.locations, credentials, outdir)


@click.command("credentials")
@click.argument("dataset_id")
@with_error_handling(resource_type="dataset", operation="data credentials")
def generate_credentials_command(dataset_id: str) -> None:
    """
    Get the credentials for a specific dataset by id. If you do not know the id, first use the search command to find the id.
    """
    # TODO: this should be able to download multiple datasets

    # Validate dataset ID
    validate_dataset_id(dataset_id, "data credentials")

    # session management
    tokens = TOKEN_MANAGER.load_tokens()
    check_authentication_status(tokens, "data credentials")

    # call data api
    data = get_dataset_api(tokens.id_token, dataset_id, download=True)

    if getattr(data, "error", None):
        console.print(f"[red]Error: {data['error']}[/red]")
    elif getattr(data, "credentials", None) is None:
        console.print("No credentials available for this dataset.", style="yellow")
    else:
        credentials = S3Credentials(**data.credentials)
        console.print(credentials.model_dump())
