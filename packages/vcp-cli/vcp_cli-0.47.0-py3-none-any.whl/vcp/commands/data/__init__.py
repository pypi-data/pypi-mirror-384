import click
from rich.console import Console

from ...config.config import Config
from ...utils.token import TokenManager
from .describe import describe_command
from .download import download_command, generate_credentials_command
from .preview import preview_command
from .search import metadata_list, search_command
from .summary import summary_command


def ensure_authentication(ctx):
    """Login guard to ensure user is authenticated before data operations."""
    token_manager = TokenManager()

    # Load tokens
    tokens = token_manager.load_tokens()
    if not tokens:
        console = Console()
        console.print("Not authenticated. Please run 'vcp login' first.", style="red")
        ctx.exit(1)

    # Check token expiration and refresh if needed
    refreshed_tokens = token_manager.refresh_tokens_if_needed(tokens)

    # Fail if unable to authenticate
    if not refreshed_tokens:
        console = Console()
        console.print(
            "Authentication failed. Please run 'vcp login' again.", style="red"
        )
        ctx.exit(1)

    # Store token manager in context for subcommands to use, so that it can be accessed by the subcommands
    ctx.ensure_object(dict)
    ctx.obj["token_manager"] = token_manager


DATA_HELP = f"""
{click.style("Data usage workflow", fg="cyan", bold=True)}\n
{click.style("1.", fg="cyan", bold=True)} List searchable fields: {click.style("vcp data search --help", fg="green")}\n
{click.style("2.", fg="cyan", bold=True)} Survey datasets based on searchable field: {click.style("vcp data summary $FIELD", fg="green")}\n
{click.style("3.", fg="cyan", bold=True)} Search for datasets: {click.style("vcp data search '$FIELD:$VALUE'", fg="green")}\n
{click.style("3.a", fg="cyan", bold=True)} ... Restrict search: {click.style("vcp data search '$FIELD:$VALUE_1 AND $FIELD:$VALUE_2'", fg="green")}\n
{click.style("3.b", fg="cyan", bold=True)} ... Expand search: {click.style("vcp data search '($FIELD:$VALUE_1 OR $FIELD:$VALUE_3 ) AND ($FIELD:$VALUE_3)'", fg="green")}\n
{click.style("4", fg="cyan", bold=True)} Describe a single dataset: {click.style("vcp data describe $DATASET_ID", fg="green")}\n
{click.style("5", fg="cyan", bold=True)} Download:\n
{click.style("5.a", fg="cyan", bold=True)} ... a single dataset: {click.style("vcp data download $DATASET_ID", fg="green")}\n
{click.style("5.b", fg="cyan", bold=True)} ... multiple datasets matching search: {click.style("vcp data search $QUERY --download", fg="green")}\n
"""


@click.group(epilog=DATA_HELP, context_settings={"max_content_width": 180})
@click.pass_context
def data_command(ctx):
    """Data-related commands"""
    ensure_authentication(ctx)


# Add subcommands to the model group
data_command.add_command(search_command, name="search")
data_command.add_command(metadata_list, name="metadata-list")
data_command.add_command(download_command, name="download")
data_command.add_command(describe_command, name="describe")
data_command.add_command(preview_command, name="preview")
data_command.add_command(summary_command, name="summary")

# Conditionally add credentials command based on feature flag
config = Config.load()
if config.feature_flags.data_subcommands.credentials:
    data_command.add_command(generate_credentials_command, name="credentials")
