import json
import logging
import re
from typing import Any, List, Optional

import click
from rich import box
from rich.console import Console
from rich.table import Table

from vcp.datasets.api import (
    Creator,
    CroissantFileObject,
    CroissantLiteModel,
    CrossModalitySchemaFields,
    create_cross_modality_fields_from_dataset,
    get_dataset_api,
    get_dataset_api_raw,
)
from vcp.utils.console import get_term_width as _term_width
from vcp.utils.errors import (
    check_authentication_status,
    validate_dataset_id,
    with_error_handling,
)
from vcp.utils.size import (
    calculate_total_dataset_size,
    format_size_bytes,
    get_file_count_from_dataset,
    parse_content_size,
)
from vcp.utils.token import TokenManager

console = Console()

TOKEN_MANAGER = TokenManager()

logger = logging.getLogger(__name__)


# extract DOI from citeAs field or bibtex string
def extract_doi(cite_as: Optional[str]) -> Optional[str]:
    """Extract DOI from citeAs field or bibtex string."""
    if not cite_as:
        return None

    # DOI regex pattern
    doi_pattern = r"10\.\d{4,9}/[-._;()/:A-Z0-9]+"

    # First try to find DOI directly in the string
    match = re.search(doi_pattern, cite_as, re.IGNORECASE)
    if match:
        return match.group(0)

    # If citeAs contains bibtex, try to extract doi field
    if "@" in cite_as and "{" in cite_as:
        # Look for doi field in bibtex
        bibtex_doi_pattern = r"doi\s*=\s*[{\"']([^}\"']+)[}\"']"
        bibtex_match = re.search(bibtex_doi_pattern, cite_as, re.IGNORECASE)
        if bibtex_match:
            doi_candidate = bibtex_match.group(1)
            # Validate it's a proper DOI
            if re.match(doi_pattern, doi_candidate, re.IGNORECASE):
                return doi_candidate

    return None


# extract organization name from creator field
def extract_organization(
    creator: Optional[Creator | List[Creator]],
) -> Optional[List[str]]:
    """Extract organization names from creator field if it's an Organization type."""
    if not creator:
        return None

    # ensure list
    _creator: List[Creator] = creator if isinstance(creator, list) else [creator]

    # filter to only Organization types
    _creator = list(filter(lambda c: c.type == "Organization", _creator))

    # return names only
    return [c.name for c in _creator] or None


# extract dataset source url
def extract_source_url(md: CroissantLiteModel) -> Optional[str]:
    # prefer url (generally the webpage of the dataset)
    if md.url:
        return str(md.url)

    # fallback to the distribution contentUrl if available
    if md.distribution:
        # ensure list
        _distribution_files = (
            md.distribution if isinstance(md.distribution, list) else [md.distribution]
        )

        # only consider FileObjets with contentUrl
        _distribution_files = list(
            filter(
                lambda d: isinstance(d, CroissantFileObject)
                and d.content_url is not None,
                _distribution_files,
            )
        )

        # get content urls
        urls = [
            fo.content_url
            for fo in _distribution_files
            if isinstance(fo, CroissantFileObject)
        ]
        return str(urls[0]) if urls else None

    return None


# format list values for display
def format_list_values(values: Optional[str | List[str]]) -> str:
    """Format list values with proper comma separation."""
    if values is None:
        return "—"
    elif isinstance(values, str):
        return values
    elif isinstance(values, list):
        if not values:
            return "—"
        return ", ".join(str(v) for v in values)
    return str(values) if values else "—"


# format urls with truncation for display
def truncate_url(url: str, max_width: int) -> str:
    """Truncate URL if it exceeds max width."""
    if len(url) <= max_width:
        return url
    # Keep beginning and end of URL
    keep_start = max_width // 2 - 2
    keep_end = max_width - keep_start - 3
    return f"{url[:keep_start]}...{url[-keep_end:]}"


# print table of basic information
def create_basic_info_table(record: Any) -> Table:
    """Create the Basic Information table."""
    tw = _term_width()

    table = Table(
        title="Basic Information",
        show_header=True,
        header_style="bold magenta",
        expand=True,
        box=box.ROUNDED,
    )

    table.add_column("Field", style="cyan", no_wrap=True, width=25)
    # Use terminal width to set value column max width
    table.add_column("Value", overflow="fold", max_width=tw - 30)

    # Extract metadata from md field if available
    md = record.md

    # Dataset Name
    table.add_row("Dataset Name", record.label or "—")

    # Domain
    table.add_row("Domain", record.domain)

    # Version
    # Try md.version first, then record.version
    version = (md.version if md else None) or record.version
    table.add_row("Version", version or "—")

    # Dataset License Terms
    license_url = md.license if md else None
    table.add_row("Dataset License Terms", str(license_url) if license_url else "—")

    # Dataset Source URL
    citation_url = extract_source_url(md)
    table.add_row("Dataset Source URL", str(citation_url) if citation_url else "—")

    # Dataset Owner (Organization only)
    creator = md.creator if md else None
    owner_name = extract_organization(creator)
    if not owner_name:
        # Fallback to org field if no Organization creator found
        owner_name = record.org if hasattr(record, "org") and record.org else None
    table.add_row("Dataset Owner", format_list_values(owner_name))

    # DOI
    cite_as = md.cite_as if md else None
    doi = extract_doi(cite_as)
    table.add_row("DOI", doi or "—")

    # Total Dataset Size
    total_size = calculate_total_dataset_size(record)
    file_count = get_file_count_from_dataset(record)
    if total_size > 0:
        size_display = f"{format_size_bytes(total_size)}"
        if file_count > 0:
            size_display += f" ({file_count} files)"
    else:
        size_display = "Size information not available"
        if file_count > 0:
            size_display += f" ({file_count} files)"
        else:
            size_display = "Size and file information not available"

    table.add_row("Total Dataset Size", size_display)

    return table


# print table of biological metadata
def create_biological_metadata_table(xms_data: CrossModalitySchemaFields) -> Table:
    """Create the Biological Metadata table using CrossModalitySchemaFields."""
    tw = _term_width()

    table = Table(
        title="Biological Metadata",
        show_header=True,
        header_style="bold magenta",
        expand=True,
        box=box.ROUNDED,
    )

    table.add_column("Field", style="cyan", no_wrap=True, width=35)
    table.add_column("Value", overflow="fold", max_width=tw - 40)

    # Get biological metadata fields from CrossModalitySchemaFields
    # These will be in the order they were defined in the model
    xms_fields = CrossModalitySchemaFields.model_fields

    # Iterate through fields in their definition order
    for field_name, field_info in xms_fields.items():
        # Get the value from the xms_data instance
        value = getattr(xms_data, field_name, None)
        # Use alias if available, otherwise format field name
        display_name = field_info.alias or field_name.replace("_", " ").title()
        table.add_row(display_name, format_list_values(value))

    return table


# print table of distribution information
def create_distribution_table(record: Any) -> Table:
    """Create the Distribution/Assets table."""
    tw = _term_width()

    table = Table(
        title="Distribution / Assets",
        show_header=True,
        header_style="bold magenta",
        expand=True,
        box=box.ROUNDED,
    )

    table.add_column("Format", style="cyan", no_wrap=True, width=20)
    table.add_column("Size", style="green", no_wrap=True, width=15)
    # Use terminal width for URL column
    url_max_width = max(40, tw - 40)
    table.add_column("URL", overflow="fold", max_width=url_max_width)

    # Get distribution from md field if available
    md = record.md
    distribution = md.distribution if md else []

    if distribution:
        for asset in distribution:
            if isinstance(asset, dict):
                encoding_format = asset.get("encodingFormat", "—")
                content_size = asset.get("contentSize")
                content_url = asset.get("contentUrl", "—")
            else:
                # Handle CroissantFileObject
                encoding_format = getattr(asset, "encoding_format", "—")
                content_size = asset.content_size
                content_url = str(getattr(asset, "content_url", "—"))

            # Format size using our utility function
            size_bytes = parse_content_size(content_size)
            formatted_size = format_size_bytes(size_bytes) if size_bytes > 0 else "—"

            # Truncate very long URLs if needed
            if len(str(content_url)) > url_max_width:
                content_url = truncate_url(str(content_url), url_max_width)
            table.add_row(encoding_format, formatted_size, str(content_url))
    elif hasattr(record, "distribution") and record.distribution:
        # Fallback to record.distribution
        for f in record.distribution:
            encoding_format = (
                f.encoding_format if hasattr(f, "encoding_format") else "—"
            )
            content_url = str(f.content_url) if hasattr(f, "content_url") else "—"
            if len(content_url) > url_max_width:
                content_url = truncate_url(content_url, url_max_width)
            table.add_row(encoding_format, "—", content_url)
    elif hasattr(record, "locations") and record.locations:
        # Final fallback to locations
        for loc in record.locations:
            scheme = loc.scheme if hasattr(loc, "scheme") else "—"
            path = str(loc.path) if hasattr(loc, "path") else "—"
            if len(path) > url_max_width:
                path = truncate_url(path, url_max_width)
            table.add_row(scheme, "—", path)
    else:
        table.add_row("No assets available", "—", "—")

    return table


@click.command("describe")
@click.argument("dataset_id")
@click.option(
    "--full",
    is_flag=True,
    default=False,
    help="Show the complete DatasetRecord as pretty-printed JSON and exit.",
)
@click.option(
    "--raw", is_flag=True, default=False, help="Show the raw returned record."
)
@with_error_handling(resource_type="dataset", operation="data describe")
def describe_command(dataset_id: str, full: bool = False, raw: bool = False):
    """
    Describe a dataset with comprehensive metadata in tabular format.

    Displays:
    • Basic Information (name, version, license, owner, DOI)
    • Biological Metadata (assays, organisms, tissues, diseases, etc.)
    • Distribution/Assets (download locations and formats)
    """

    # Validate dataset ID format first
    validate_dataset_id(dataset_id, "data describe")

    # session management
    tokens = TOKEN_MANAGER.load_tokens()
    check_authentication_status(tokens, "data describe")

    # call data api
    if raw:
        record = get_dataset_api_raw(tokens.id_token, dataset_id, download=False)
        click.echo(json.dumps(record, indent=2))
        return

    record = get_dataset_api(tokens.id_token, dataset_id, download=False)

    if full:
        # dump the entire model, preserving original JSON field names
        click.echo(record.model_dump_json(indent=2, by_alias=True))
        return

    # Create and display tables
    console.print()

    # Basic Information Table
    basic_table = create_basic_info_table(record)
    console.print(basic_table)
    console.print()

    # Extract biological metadata using factory function
    xms_data = create_cross_modality_fields_from_dataset(record)

    # Biological Metadata Table
    bio_table = create_biological_metadata_table(xms_data)
    console.print(bio_table)
    console.print()

    # Distribution/Assets Table
    dist_table = create_distribution_table(record)
    console.print(dist_table)
    console.print()
