import os
import traceback
from typing import Optional

import click
import requests
from rich.console import Console
from rich.panel import Panel

from ...config.config import Config
from ...utils.token import TokenManager
from .utils import download_multiple_files, download_single_file

console = Console()


@click.command()
@click.option("--model", required=True, help="Name of the model to download")
@click.option("--version", required=True, help="Version of the model to download")
@click.option("--output", required=True, help="Directory to save the downloaded model")
@click.option("--config", "-c", help="Path to config file")
@click.option(
    "--timeout", default=1800, help="Timeout in seconds for download (default: 1800)"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed debug information")
@click.option(
    "--max-workers",
    default=4,
    help="Maximum number of concurrent downloads (default: 4)",
)
def download_command(
    model: str,
    version: str,
    output: str,
    config: Optional[str] = None,
    timeout: int = 1800,
    verbose: bool = False,
    max_workers: int = 4,
):
    """Download a specific version of a model using presigned S3 URLs."""
    try:
        # Load configuration
        config_data = Config.load(config)

        # Check for valid tokens and get auth headers
        token_manager = TokenManager()
        headers = token_manager.get_auth_headers()

        if not headers:
            console.print("[red]Not logged in. Please run 'vcp login' first.[/red]")
            return

        # Call the download endpoint to get the model URI
        url = f"{config_data.models.base_url}/api/models/download/{model}/{version}"

        response = requests.get(url, headers=headers)

        if verbose:
            console.print(
                f"[bold blue]API Status Code:[/bold blue] {response.status_code}"
            )

        if response.status_code != 200:
            console.print(
                Panel(
                    f"[red]Failed to get download URI: {response.text}[/red]",
                    title="API Error",
                )
            )
            return

        data = response.json()

        # Handle the new API response structure with all_files array
        all_files = data.get("all_files", [])

        # For backward compatibility, also handle single download_url
        if not all_files and "download_url" in data:
            # Create a single file entry for backward compatibility
            all_files = [
                {
                    "name": "model.tar.gz",
                    "download_url": data["download_url"],
                    "relative_path": "model.tar.gz",
                    "size": data.get("object_size"),
                }
            ]

        if not all_files:
            console.print(
                Panel(
                    "[red]No files found in the API response.[/red]",
                    title="Download Error",
                )
            )
            return

        # Extract model information from response
        expires_in = data.get("presigned_url_expires_in", 3600)
        total_files = data.get("total_files", len(all_files))
        total_size = data.get("total_size") or 0

        # Create directory with model name and version
        model_dir = os.path.join(output, f"{model}-{version}")
        os.makedirs(model_dir, exist_ok=True)

        if verbose:
            console.print(
                f"\n[bold blue]Files to download:[/bold blue] {len(all_files)} files"
            )
            console.print(f"[bold blue]Total size:[/bold blue] {total_size:,} bytes")
            console.print(f"[bold blue]Download directory:[/bold blue] {model_dir}")
            console.print(
                f"[bold blue]URL expires in:[/bold blue] {expires_in} seconds"
            )
            if len(all_files) <= 5:  # Show file details if not too many
                for i, file_info in enumerate(all_files, 1):
                    console.print(
                        f"[bold blue]File {i}:[/bold blue] {file_info['name']} ({(file_info.get('size') or 0):,} bytes)"
                    )
                    console.print(
                        f"[bold blue]  Path:[/bold blue] {file_info['relative_path']}"
                    )
            else:
                console.print(
                    f"[bold blue]Files:[/bold blue] {', '.join([f['name'] for f in all_files[:3]])}... (and {len(all_files) - 3} more)"
                )

        # Download the model using presigned S3 URLs
        try:
            if len(all_files) == 1:
                # Single file download with retry support
                file_info = all_files[0]
                file_path = os.path.join(model_dir, file_info["relative_path"])

                # Create directory for the file if needed
                file_dir = os.path.dirname(file_path)
                if file_dir and file_dir != model_dir:
                    os.makedirs(file_dir, exist_ok=True)

                success = download_single_file(
                    download_url=file_info["download_url"],
                    output_path=file_dir if file_dir != model_dir else model_dir,
                    filename=os.path.basename(file_info["relative_path"]),
                    model=model,
                    version=version,
                    api_url=url,
                    headers=headers,
                    timeout=timeout,
                    verbose=verbose,
                    show_progress=True,  # Show progress for single file download
                )

                if success:
                    console.print(
                        Panel(
                            f"[green]✅ Model downloaded successfully to: {model_dir}[/green]",
                            title="Success",
                        )
                    )
                else:
                    console.print(
                        Panel(
                            "[red]❌ Download failed after multiple retry attempts[/red]",
                            title="Download Error",
                        )
                    )
                    return
            else:
                # Multiple files download with parallel processing
                results = download_multiple_files(
                    all_files=all_files,
                    output_path=model_dir,
                    model=model,
                    version=version,
                    timeout=timeout,
                    verbose=verbose,
                    max_workers=max_workers,
                )

                successful_downloads = sum(1 for success in results.values() if success)
                total_files = len(all_files)

                if successful_downloads == total_files:
                    console.print(
                        Panel(
                            f"[green]✅ All {total_files} model files downloaded successfully to: {model_dir}[/green]",
                            title="Success",
                        )
                    )
                elif successful_downloads > 0:
                    console.print(
                        Panel(
                            f"[yellow]⚠️ Partial success: {successful_downloads}/{total_files} files downloaded to: {model_dir}[/yellow]\n"
                            f"Some files may have failed. Check the output directory.",
                            title="Partial Success",
                        )
                    )
                    return
                else:
                    console.print(
                        Panel(
                            "[red]❌ All downloads failed. No files were downloaded.[/red]",
                            title="Download Error",
                        )
                    )
                    return

        except Exception as e:
            console.print(
                Panel(
                    f"[red]❌ Download failed: {str(e)}[/red]", title="Download Error"
                )
            )
            return

    except Exception as e:
        if verbose:
            console.print("\n[bold red]Detailed Error Information:[/bold red]")
            console.print(traceback.format_exc())
        console.print(f"[red]Error during download: {str(e)}[/red]")
