import dataclasses
import json
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ..config.config import Config

console = Console()


def mask_secrets(d):
    if isinstance(d, dict):
        return {
            k: (
                "****"
                if any(s in k.lower() for s in ["password", "username", "secret"])
                else mask_secrets(v)
            )
            for k, v in d.items()
        }
    elif isinstance(d, list):
        return [mask_secrets(i) for i in d]
    else:
        return d


@click.command()
@click.option("--config", "-c", help="Path to config file")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@click.option(
    "--show-secrets/--hide-secrets", default=False, help="Show sensitive information"
)
@click.option(
    "--init",
    "-i",
    is_flag=True,
    help="Initialize a configuration if one does not exist",
)
def config_command(
    config: Optional[str] = None,
    format: str = "yaml",
    show_secrets: bool = False,
    init: bool = False,
):
    """Print the current configuration."""
    try:
        # Load configuration
        config_dict = dataclasses.asdict(Config.load(config))

        if not show_secrets:
            config_dict = mask_secrets(config_dict)

        # Print configuration
        if format == "json":
            output = json.dumps(config_dict, indent=2)
            syntax = Syntax(output, "json", theme="monokai")
        else:
            output = yaml.dump(config_dict, default_flow_style=False)
            syntax = Syntax(output, "yaml", theme="monokai")

        console.print(
            Panel(
                syntax,
                title="Current Configuration",
                subtitle=f"Format: {format.upper()}"
                + (" (with secrets)" if show_secrets else ""),
            )
        )

        # Print config file location
        config_path = Path(config) if config else Path.home() / ".vcp" / "config.yaml"
        if not config_path.exists():
            if init:
                # write formatted config to config path
                config_path.parent.mkdir(parents=True, exist_ok=True)
                if format == "json":
                    json.dump(config_dict, open(config_path, "w+"), indent=2)
                elif format == "yaml":
                    yaml.dump(config_dict, open(config_path, "w+"), indent=2)

                console.print(f"\n[dim]Configuration initialized: {config_path}[/dim]")

            config_path = Path("config.yaml")

        console.print(f"\n[dim]Configuration loaded from: {config_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error loading configuration: {str(e)}[/red]")
