import click
from rich.console import Console
from rich.panel import Panel

from ..auth.oauth import AuthConfig, login
from ..config.config import Config
from ..utils.token import TokenManager

console = Console()


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force login even if valid tokens exist",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--username",
    "-u",
    help="Username for direct login",
)
def login_command(config: str, force: bool, verbose: bool, username: str):
    """Login to the Virtual Cells Platform"""
    try:
        # Load configuration
        config_data = Config.load(config)
        if verbose:
            console.print("\n[bold blue]Configuration loaded:[/bold blue]")
            console.print(f"  Domain: {config_data.aws.cognito.domain}")
            console.print(f"  Client ID: {config_data.aws.cognito.client_id}")
            console.print(f"  Region: {config_data.aws.region}")

        # If username is provided, force the password flow, otherwise use the configured flow
        if username is not None:
            flow = "password"
        else:
            flow = config_data.aws.cognito.flow

        # Create OAuth configuration
        oauth_config = AuthConfig(
            user_pool_id=config_data.aws.cognito.user_pool_id,
            client_id=config_data.aws.cognito.client_id,
            client_secret=config_data.aws.cognito.client_secret,
            domain=config_data.aws.cognito.domain,
            region=config_data.aws.region,
            username=username,
            flow=flow,
        )

        # collect tokens from login function
        tokens = login(oauth_config, verbose=verbose)
        if not tokens:
            console.print("[red]Login failed[/red]")
            return

        # Save tokens
        TokenManager().save_tokens(tokens)
        console.print("[green]Login successful![/green]")

    except Exception as e:
        console.print(
            Panel(f"Error during login: {str(e)}", title="Error", border_style="red")
        )
