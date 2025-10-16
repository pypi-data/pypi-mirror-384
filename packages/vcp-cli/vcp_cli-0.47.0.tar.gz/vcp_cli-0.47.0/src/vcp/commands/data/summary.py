import click
from rich import box
from rich.console import Console
from rich.table import Table

from vcp.datasets.api import (
    CrossModalitySchemaFields,
    FacetBucket,
    SummaryResponse,
    summary_data_api,
)
from vcp.utils.console import get_term_width
from vcp.utils.errors import (
    check_authentication_status,
    validate_search_term,
    with_error_handling,
)
from vcp.utils.token import TokenManager

# initialize services
TOKEN_MANAGER = TokenManager()
console = Console()


# constants
SUMMARY_EXAMPLES = f"""

{click.style("Examples:", fg="cyan", bold=True)} \n
- Summarize by a Cross Modality field \n
\t{click.style("vcp data summary assay", fg="green")} \n
\t{click.style("vcp data summary assay_ontology_term_id", fg="green")} \n
- Filter Summary by an additional search query \n
\t{click.style("vcp data summary assay --query brain", fg="green")} \n
"""


# ---- Helper Functions ---- #
# print table of distribution information
def create_distribution_table(items: list[FacetBucket], field: str) -> Table:
    """Create the Distribution/Assets table."""
    tw = get_term_width()

    # initialize width
    table = Table(
        title="Summary: Dataset Counts by Field Value",
        show_header=True,
        header_style="bold magenta",
        expand=True,
        box=box.ROUNDED,
    )

    table.add_column(field, style="cyan", no_wrap=True, width=50)
    table.add_column("Count", style="green", no_wrap=True, width=tw - 50)

    # Get distribution from md field if available
    for item in items:
        table.add_row(str(item.value), str(item.count))

    return table


class FriendlyChoice(click.Choice):
    def convert(self, value, param, ctx):
        try:
            # Let Click do normal conversion first
            return super().convert(value, param, ctx)
        except click.BadParameter:
            # Build your custom error message
            error_message = f'[red] Metadata FIELD "{value}" is not supported by summary command.[/red]'
            hint_message = (
                "\nTry: [cyan]`vcp data summary --help`[/cyan] to see supported fields"
            )
            message = "\n".join(["", error_message, hint_message, ""])
            console.print(message)
            if ctx:
                ctx.exit(1)


XMS_CHOICE = FriendlyChoice(
    list(CrossModalitySchemaFields.__pydantic_fields__), case_sensitive=False
)


# ---- Commands ---- #
@click.command(epilog=SUMMARY_EXAMPLES)
@click.argument("field", type=XMS_CHOICE)
@click.option("--query", "-q", default="*", help="Search query to filter datasets.")
@click.pass_context
@with_error_handling(resource_type="datasets", operation="data summary")
def summary_command(ctx: click.Context, field: str, query: str):
    """Summarize counts of matched datasets against a specified FIELD."""

    # Validate search query (only if not wildcard)
    if query != "*":
        validate_search_term(query, "data summary")

    # get authorization credentials
    tokens = TOKEN_MANAGER.load_tokens()
    check_authentication_status(tokens, "data summary")

    # issue request
    summary: SummaryResponse = summary_data_api(
        id_token=tokens.id_token, field=field, term=query
    )

    # pagination for users
    page_size = 20  # #NOTE: this could be a tool-wide constant to improve consistency
    page = 0
    total = len(summary.facets)

    while True:
        # get next page of items
        start, end = page * page_size, (page + 1) * page_size
        items = summary.facets[start:end]

        # print page
        title = (
            f"Page {page + 1}: Showing items {start} to {min(end, total)} of {total}"
        )
        console.print(title, style="bold")
        console.print(create_distribution_table(items, field=summary.field))

        # prompt users for next action
        if end >= total:
            break
        else:
            console.print("\n<RETURN> next page | q + <RETURN> quit")
            if input().strip().lower() == "q":
                break
            page += 1
