import traceback

import click
from rich.console import Console
from rich.panel import Panel

from ..auth.config import LogoutConfig
from ..auth.oauth import logout
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
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def logout_command(config: str, verbose: bool):
    """Logout from the Virtual Cells Platform"""
    try:
        # Load configuration to get Cognito settings
        config_data = Config.load(config)
        if verbose:
            console.print("\n[bold blue]Configuration loaded:[/bold blue]")
            console.print(f"  Domain: {config_data.aws.cognito.domain}")
            console.print(f"  Client ID: {config_data.aws.cognito.client_id}")
            console.print(f"  Region: {config_data.aws.region}")

        # Create logout configuration - only need region for Cognito client
        logout_config = LogoutConfig(region=config_data.aws.region)

        # Perform logout with Cognito token invalidation
        success = logout(logout_config, verbose=verbose)

        if success:
            console.print("[green]Successfully logged out![/green]")
            if verbose:
                console.print(
                    "[green]All tokens have been invalidated with AWS Cognito and cleared locally.[/green]"
                )
        else:
            console.print(
                "[yellow]Logout completed with some issues. Check verbose output for details.[/yellow]"
            )

    except FileNotFoundError:
        # Fallback: just clear local tokens if no config found
        console.print(
            "[yellow]No configuration found. Clearing local tokens only...[/yellow]"
        )
        try:
            TokenManager().clear_tokens()
            console.print("[green]Local tokens cleared.[/green]")
            console.print(
                "[yellow]Note: Remote tokens were not invalidated. Use --config to specify configuration for full logout.[/yellow]"
            )
        except Exception as e:
            console.print(f"[red]Error clearing local tokens: {str(e)}[/red]")

    except Exception as e:
        console.print(
            Panel(
                f"Error during logout: {str(e)}",
                title="Logout Error",
                border_style="red",
            )
        )
        if verbose:
            console.print("\n[bold red]Full error traceback:[/bold red]")
            console.print(traceback.format_exc())

        # Attempt to clear local tokens as fallback
        try:
            TokenManager().clear_tokens()
            console.print("[yellow]Cleared local tokens despite error.[/yellow]")
        except Exception as local_error:
            console.print(
                f"[red]Failed to clear local tokens: {str(local_error)}[/red]"
            )
