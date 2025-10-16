import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from ...auth.oauth import get_user_info
from ...config.config import Config
from ...utils.cache import clean_upload_state, load_upload_state, save_upload_state
from ...utils.token import TokenManager
from .utils import (
    calculate_file_checksum,
    check_large_file_considerations,
    create_artifact_id,
    get_batch_upload_urls,
    run_git_add_after_upload,
    scan_directory_structure,
    upload_files_batch_parallel,
    validate_code_quality_with_ruff,
    validate_model_data_directory,
    validate_upload_completion,
)

console = Console()


@click.command()
@click.option("--model", help="Name of the model")
@click.option("--version", help="Version of the model")
@click.option(
    "--data-path",
    type=click.Path(exists=True),
    help="Directory path containing model files",
)
@click.option(
    "--work-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the model repository work directory where model configuration is located",
)
@click.option("--config", "-c", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed debug information")
@click.option(
    "--max-retries",
    default=3,
    help="Maximum number of retry attempts per file (default: 3)",
)
@click.option(
    "--no-resume",
    is_flag=True,
    help="Start fresh without resuming from previous upload attempt",
)
@click.option(
    "--clean-state", is_flag=True, help="Clean previous upload state and start fresh"
)
@click.option(
    "--batch-upload",
    is_flag=True,
    help="[DEPRECATED] Batch upload is now the default behavior",
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Run in interactive mode to prompt for required parameters.",
)
def stage_command(
    model: Optional[str] = None,
    version: Optional[str] = None,
    data_path: Optional[str] = None,
    work_dir: Optional[str] = None,
    config: Optional[str] = None,
    verbose: bool = False,
    max_retries: int = 3,
    no_resume: bool = False,
    clean_state: bool = False,
    batch_upload: bool = False,  # Deprecated but kept for compatibility
    interactive: bool = False,
):
    """
    Stage model files for upload to the VCP Model Hub.

    \b
    This command uploads files to S3 using the new model_data path structure:
    - Files are uploaded to: s3://bucket/model/version/model_data/
    - Creates .ptr pointer files with metadata for each uploaded file
    - Deletes original files after successful upload
    - Automatically resumes from previous failed upload attempts (use --no-resume to start fresh)
    - Filters out hidden files (starting with .)

    \b
    The upload process:
    1. Scan directory and create initial pointer files
    2. Get presigned URLs for each file
    3. Upload files sequentially with immediate metadata updates
    4. Delete original files after successful upload

    \b
    Work Directory:
    - Use --work-dir to specify the location of model configuration file
    - If not provided, checks current directory first, then prompts for work directory
    - The command will look for model_data directory within the work directory structure

    \b
    Examples:
    - vcp model stage --work-dir /path/to/model/repo
    - vcp model stage --model my-model --version v1.0.0 --data-path ./model_data
    - vcp model stage --work-dir /path/to/repo --verbose
    """
    try:
        # Determine the work directory to use
        if work_dir:
            # Use provided work directory
            work_dir_path = Path(work_dir)
            if verbose:
                console.print(f"[blue]Using provided work directory: {work_dir}[/blue]")
        else:
            # Check current directory first, then prompt if needed
            current_dir = Path.cwd()
            metadata_file = current_dir / ".model-metadata"

            if metadata_file.exists():
                work_dir_path = current_dir
                if verbose:
                    console.print(
                        "[blue]Found model configuration in current directory[/blue]"
                    )
            else:
                # No metadata in current directory, ask for work directory
                console.print(
                    "[yellow]No model configuration found in current directory[/yellow]"
                )
                work_dir = click.prompt(
                    "Enter the path to your model repository work directory",
                    type=click.Path(exists=True, file_okay=False, dir_okay=True),
                )
                work_dir_path = Path(work_dir)

        # Check for .model-metadata file in the work directory
        metadata_file = work_dir_path / ".model-metadata"
        existing_metadata = None

        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    existing_metadata = json.load(f)
                console.print(
                    f"[blue]Found model configuration in {work_dir_path}[/blue]"
                )
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not read metadata file: {e}[/yellow]"
                )
                existing_metadata = None
        else:
            console.print(
                f"[yellow]No model configuration found in {work_dir_path}[/yellow]"
            )
            existing_metadata = None

        # Check if any required parameters are missing
        required_params = [model, version, data_path]
        has_any_params = any(param is not None for param in required_params)

        # If we have metadata and no explicit parameters, try to use metadata values
        if existing_metadata and not has_any_params and not interactive:
            console.print("[blue]Current values from model configuration:[/blue]")
            console.print(f"  Model name: {existing_metadata.get('model_name', 'N/A')}")
            console.print(
                f"  Model version: {existing_metadata.get('model_version', 'N/A')}"
            )
            console.print(
                f"  Output path: {existing_metadata.get('output_path', 'N/A')}"
            )

            # Ask if user wants to use metadata values
            use_metadata = click.confirm(
                "Use values from current workdir configuration?", default=True
            )

            if use_metadata:
                model = existing_metadata.get("model_name")
                version = existing_metadata.get("model_version")
                output_path = existing_metadata.get("output_path")

                if model and version and output_path:
                    # Construct data-path: output_path/*mlflow_pkg/model_data
                    # TODO: remove wildcard from mlflow_pkg. Unnecessary and only used for backwards compatibility with testing repos
                    output_path_obj = Path(output_path)

                    # Look for *mlflow_pkg directory
                    mlflow_dirs = list(output_path_obj.glob("*mlflow_pkg"))
                    if mlflow_dirs:
                        mlflow_dir = mlflow_dirs[0]  # Use first match
                        model_data_path = mlflow_dir / "model_data"

                        # Validate the model_data directory
                        if not validate_model_data_directory(str(model_data_path)):
                            return

                        data_path = str(model_data_path)
                        console.print(f"[green]Using data path: {data_path}[/green]")
                    else:
                        console.print(
                            f"[yellow]No *mlflow_pkg directory found in {output_path}[/yellow]"
                        )
                        console.print(
                            "[yellow]Please specify --data-path manually[/yellow]"
                        )
                        return
                else:
                    console.print(
                        "[red]Incomplete metadata file. Missing required fields.[/red]"
                    )
                    return
            else:
                # User chose not to use metadata, run in interactive mode
                interactive = True

        # Interactive mode - prompt for missing parameters
        if interactive:
            # Use the work directory we already determined
            if existing_metadata:
                console.print("[blue]Current values from model configuration:[/blue]")
                console.print(
                    f"  Model name: {existing_metadata.get('model_name', 'N/A')}"
                )
                console.print(
                    f"  Model version: {existing_metadata.get('model_version', 'N/A')}"
                )
                console.print(
                    f"  Output path: {existing_metadata.get('output_path', 'N/A')}"
                )

            # Prompt for model name
            if not model:
                if existing_metadata and existing_metadata.get("model_name"):
                    default_name = existing_metadata["model_name"]
                    use_existing = click.confirm(
                        f"Use existing model name '{default_name}'?", default=True
                    )
                    if use_existing:
                        model = default_name
                    else:
                        model = click.prompt("Model name")
                else:
                    model = click.prompt("Model name")

            # Prompt for model version
            if not version:
                if existing_metadata and existing_metadata.get("model_version"):
                    default_version = existing_metadata["model_version"]
                    use_existing = click.confirm(
                        f"Use existing model version '{default_version}'?", default=True
                    )
                    if use_existing:
                        version = default_version
                    else:
                        version = click.prompt("Model version")
                else:
                    version = click.prompt("Model version")

            # Prompt for data path
            if not data_path:
                if existing_metadata and existing_metadata.get("output_path"):
                    output_path = existing_metadata["output_path"]
                    # Try to construct data path from metadata
                    output_path_obj = Path(output_path)
                    mlflow_dirs = list(output_path_obj.glob("*mlflow_pkg"))
                    if mlflow_dirs:
                        mlflow_dir = mlflow_dirs[0]
                        model_data_path = mlflow_dir / "model_data"
                        if model_data_path.exists():
                            default_data_path = str(model_data_path)
                            use_existing = click.confirm(
                                f"Use data path from metadata '{default_data_path}'?",
                                default=True,
                            )
                            if use_existing:
                                # Validate the model_data directory
                                if not validate_model_data_directory(default_data_path):
                                    return
                                data_path = default_data_path
                            else:
                                data_path = click.prompt(
                                    "Data directory path", type=click.Path(exists=True)
                                )
                        else:
                            data_path = click.prompt(
                                "Data directory path", type=click.Path(exists=True)
                            )
                    else:
                        data_path = click.prompt(
                            "Data directory path", type=click.Path(exists=True)
                        )
                else:
                    data_path = click.prompt(
                        "Data directory path", type=click.Path(exists=True)
                    )

        # Validate that all required parameters are now provided
        if not all([model, version, data_path]):
            console.print("[red]Error: Missing required parameters.[/red]")
            console.print(
                "[yellow]All of model, version, and data-path are required.[/yellow]"
            )
            return

        # Validate the model_data directory
        if not validate_model_data_directory(data_path):
            return

        # Check if files are already uploaded (only .ptr files and directories should remain)
        # If not all files are uploaded, we'll proceed with the upload process
        upload_complete = validate_upload_completion(data_path, show_errors=False)
        if upload_complete:
            console.print(
                "[green]All files have already been staged successfully![/green]"
            )
            console.print(
                "[blue]Only .ptr files and directories remain in model_data.[/blue]"
            )

            # Find repository root for code quality validation
            current_path = Path(data_path)
            repo_root = None

            # Walk up the directory tree to find .git
            for parent in [current_path] + list(current_path.parents):
                if (parent / ".git").exists():
                    repo_root = parent
                    break

            if repo_root:
                # Run code quality validation with ruff before saving files
                console.print(
                    "\n[bold blue]Running code quality validation...[/bold blue]"
                )
                validation_passed = validate_code_quality_with_ruff(str(repo_root))
                if not validation_passed:
                    console.print(
                        "[yellow]Code quality validation failed. Please fix the issues before proceeding.[/yellow]"
                    )
                    # Continue with saving files even if validation fails
                    console.print(
                        "[blue]Continuing with saving files despite validation failure...[/blue]"
                    )

                # Save all files to ensure they are properly stored
                console.print("\n[bold blue]Saving all repository files...[/bold blue]")
                run_git_add_after_upload(data_path)
            else:
                console.print(
                    "[yellow]Warning: Could not find repository root for code quality validation[/yellow]"
                )
                # Still save files even if we can't find repo root
                console.print("\n[bold blue]Saving all repository files...[/bold blue]")
                run_git_add_after_upload(data_path)
            return
        # Load configuration
        config_data = Config.load(config)

        # Get user authentication
        token_manager = TokenManager()
        headers = token_manager.get_auth_headers()

        if not headers:
            console.print(
                Panel(
                    "[red]Authentication required. Please run 'vcp login' first.[/red]",
                    title="Authentication Error",
                )
            )
            return

        # Get user info from token
        user_info = get_user_info(headers["Authorization"].replace("Bearer ", ""))
        if not user_info:
            console.print(
                Panel(
                    "[red]Could not get user information from token.[/red]",
                    title="Authentication Error",
                )
            )
            return

        # Add user info to headers
        headers["X-User-Name"] = user_info["username"]

        # Use production-grade batch upload by default (single URL mode is deprecated)
        # The single URL mode doesn't work with the new model_data path structure
        return stage_files_batch_upload(
            model,
            version,
            data_path,
            config_data,
            headers,
            verbose,
            max_retries,
            not no_resume,  # Invert the logic: resume by default unless no_resume is True
            clean_state,
        )

    except Exception as e:
        if verbose:
            console.print("\n[bold red]Detailed Error Information:[/bold red]")
            console.print(traceback.format_exc())
        console.print(f"[red]Error during staging: {str(e)}[/red]")


def stage_files_batch_upload(
    model: str,
    version: str,
    data_path: str,
    config_data,
    headers: dict,
    verbose: bool = False,
    max_retries: int = 3,
    resume: bool = True,  # Resume by default
    clean_state: bool = False,
) -> None:
    """
    Production-grade batch upload using individual presigned URLs per file.

    This function implements the new upload approach:
    1. Scan directory structure
    2. Get individual presigned URLs for each file
    3. Upload files sequentially with immediate metadata updates
    4. Handle individual file retries
    """
    try:
        console.print("\n[bold blue]Starting batch staging...[/bold blue]")
        console.print(f"Model: {model}, Version: {version}")
        console.print(f"Data path: {data_path}")

        # Scan directory structure
        console.print("\n[bold blue]Scanning directory structure...[/bold blue]")
        files_info = scan_directory_structure(data_path)

        if not files_info:
            console.print("[yellow]No files found to stage.[/yellow]")
            return

        # Check for large files and provide S3 presigned URL considerations
        check_large_file_considerations(files_info)

        # Create pointer files BEFORE upload
        console.print(
            f"\n[bold blue]Creating pointer files (.ptr) for {len(files_info)} files...[/bold blue]"
        )
        create_pointer_files_before_upload(
            files_info, Path(data_path), model, version, verbose
        )

        console.print(f"Found {len(files_info)} files to stage:")

        # Show first 10 files with their sizes
        for file_info in files_info[:10]:  # Show first 10 files
            size_mb = file_info["file_size"] / (1024 * 1024)
            console.print(f"  - {file_info['relative_path']} ({size_mb:.2f} MB)")

        # Show count of remaining files if more than 10
        if len(files_info) > 10:
            remaining = len(files_info) - 10
            console.print(f"  ... and {remaining} more files.")

        # Initialize upload state management with XDG cache

        if clean_state:
            clean_upload_state(model, version, data_path)
            if verbose:
                console.print("[blue]Cleaned previous upload state from cache[/blue]")

        upload_state = load_upload_state(model, version, data_path)

        # Update state with current session info
        if not upload_state.get("started_at"):
            upload_state["started_at"] = datetime.now().isoformat()

        # Always check for already completed files and resume automatically
        completed_files = set(upload_state.get("completed_files", []))
        original_count = len(files_info)
        files_info = [
            f for f in files_info if f["relative_path"] not in completed_files
        ]
        if completed_files:
            skipped = original_count - len(files_info)
            console.print(
                f"[blue]Resuming staging: {skipped} files already completed[/blue]"
            )

        if not files_info:
            console.print("[green]All files already completed![/green]")
            return

        # Get batch presigned URLs
        console.print(
            f"\n[bold blue]Preparing {len(files_info)} files for staging...[/bold blue]"
        )
        batch_response = get_batch_upload_urls(
            config_data, headers, model, version, files_info, verbose
        )

        if not batch_response:
            console.print("[red]Failed to get batch staging URLs[/red]")
            return

        # Extract file upload mappings
        api_files = batch_response.get("files", [])
        if len(api_files) != len(files_info):
            console.print(
                f"[yellow]Warning: Got URLs for {len(api_files)} files, expected {len(files_info)}[/yellow]"
            )

        # Create upload mapping
        files_upload_mapping = []
        api_files_by_path = {f["relative_path"]: f for f in api_files}

        for file_info in files_info:
            api_file = api_files_by_path.get(file_info["relative_path"])
            if not api_file:
                console.print(
                    f"[red]No presigned URL for file: {file_info['relative_path']}[/red]"
                )
                continue

            if not api_file.get("presigned_url"):
                console.print(
                    f"[red]Invalid presigned URL for file: {file_info['relative_path']}[/red]"
                )
                continue

            files_upload_mapping.append({
                "file_info": file_info,
                "presigned_url": api_file["presigned_url"],
                "storage_key": api_file["s3_key"],
            })

        if not files_upload_mapping:
            console.print("[red]No valid staging URLs available[/red]")
            return

        console.print(
            f"\n[bold blue]Staging {len(files_upload_mapping)} files sequentially...[/bold blue]"
        )

        # Upload files sequentially with immediate pointer updates and file deletion
        upload_results = upload_files_batch_parallel(
            files_upload_mapping, model, version, verbose, max_retries
        )

        # Update upload state with completed files
        successful_files = [
            r["file_info"]["relative_path"] for r in upload_results["successful"]
        ]
        upload_state.setdefault("completed_files", []).extend(successful_files)
        upload_state["last_upload"] = datetime.now().isoformat()
        save_upload_state(model, version, upload_state, data_path)

        # Show results
        total = upload_results["total"]
        successful = len(upload_results["successful"])
        failed = len(upload_results["failed"])

        console.print("\n[bold]Upload Results:[/bold]")
        console.print(f"Successful: {successful}/{total}")
        console.print(f"Failed: {failed}/{total}")

        if failed > 0:
            console.print("\n[red]Failed files:[/red]")
            for result in upload_results["failed"][:5]:  # Show first 5 failed files
                file_info = result.get("file_info", {})
                console.print(f"  - {file_info.get('relative_path', 'unknown')}")
            if failed > 5:
                console.print(f"  ... and {failed - 5} more")

            # Check if we should attempt automatic retry
            if failed <= 5:  # Only auto-retry if few failures
                console.print(
                    f"\n[bold blue]Attempting automatic retry for {failed} failed files with extended timeout...[/bold blue]"
                )

                # Create retry mapping for failed files only
                retry_mapping = []
                for result in upload_results["failed"]:
                    file_info = result.get("file_info")
                    if file_info:
                        # Find the original mapping for this file
                        for mapping in files_upload_mapping:
                            if (
                                mapping["file_info"]["relative_path"]
                                == file_info["relative_path"]
                            ):
                                retry_mapping.append(mapping)
                                break

                if retry_mapping:
                    retry_results = upload_files_batch_parallel(
                        retry_mapping,
                        model,
                        version,
                        verbose,
                        max_retries + 2,  # Extra retries
                    )

                    retry_successful = len(retry_results["successful"])
                    if retry_successful > 0:
                        # Update state with newly successful files
                        retry_successful_files = [
                            r["file_info"]["relative_path"]
                            for r in retry_results["successful"]
                        ]
                        upload_state.setdefault("completed_files", []).extend(
                            retry_successful_files
                        )
                        save_upload_state(model, version, upload_state, data_path)

                        # Update totals
                        upload_results["successful"].extend(retry_results["successful"])
                        upload_results["failed"] = []
                        successful += retry_successful
                        failed = 0
                        console.print(
                            "[green]All failed files successfully staged on retry![/green]"
                        )

            if failed > 0:
                console.print(
                    "\n[yellow]You can manually retry remaining failed staging by running the same command again:[/yellow]"
                )
                console.print(
                    f"[blue]vcp model stage --model {model} --version {version} --data-path {data_path}[/blue]"
                )

        if successful == total:
            console.print("\n[green]All files staged successfully![/green]")
            # Clean up state on complete success
            clean_upload_state(model, version, data_path)

            # Find repository root for code quality validation
            current_path = Path(data_path)
            repo_root = None

            # Walk up the directory tree to find .git
            for parent in [current_path] + list(current_path.parents):
                if (parent / ".git").exists():
                    repo_root = parent
                    break

            if repo_root:
                # Run code quality validation with ruff before saving files
                console.print(
                    "\n[bold blue]Running code quality validation...[/bold blue]"
                )
                validation_passed = validate_code_quality_with_ruff(str(repo_root))
                if not validation_passed:
                    console.print(
                        "[yellow]Code quality validation failed. Please fix the issues before proceeding.[/yellow]"
                    )
                    # Continue with saving files even if validation fails
                    console.print(
                        "[blue]Continuing with saving files despite validation failure...[/blue]"
                    )

                # Save all files in the repository
                console.print("\n[bold blue]Saving all repository files...[/bold blue]")
                run_git_add_after_upload(data_path)
            else:
                console.print(
                    "[yellow]Warning: Could not find repository root for code quality validation[/yellow]"
                )
                # Still save files even if we can't find repo root
                console.print("\n[bold blue]Saving all repository files...[/bold blue]")
                run_git_add_after_upload(data_path)

        # Pointer files are now updated immediately after each successful upload
        # No need for batch pointer file updates

    except Exception as e:
        console.print(f"[red]Error in batch staging: {str(e)}[/red]")
        if verbose:
            console.print(f"[red]{traceback.format_exc()}[/red]")


def create_pointer_files_before_upload(
    files_info: list, base_path: Path, model: str, version: str, verbose: bool = False
):
    """Create pointer files (.ptr) BEFORE upload for tracking purposes."""
    for file_info in files_info:
        try:
            file_path = Path(file_info["absolute_path"])

            # Get file stats
            file_stats = file_path.stat()
            file_size_mb = file_stats.st_size / (1024 * 1024)  # Size in MB
            checksum = calculate_file_checksum(file_path)
            last_modified = (
                datetime.fromtimestamp(file_stats.st_mtime).isoformat() + "Z"
            )
            artifact_id = create_artifact_id(model, version, file_info["relative_path"])

            # Create pointer file path
            pointer_file = file_path.parent / f"{file_path.stem}{file_path.suffix}.ptr"

            # Create initial metadata (will be updated after successful upload)
            metadata = {
                "artifact_id": artifact_id,
                "model_name": model,
                "version": version,
                "relative_path": file_info["relative_path"],
                "storage_key": f"{model}/{version}/model_data/{file_info['relative_path']}",
                "size": f"{round(file_size_mb, 2)} MB",
                "checksum": f"sha256:{checksum}",
                "last_modified": last_modified,
                "created_timestamp": datetime.now().isoformat(),
                "upload_status": "pending",
                "upload_successful": False,
                "content_type": "application/octet-stream",
            }

            # If pointer file already exists, preserve creation timestamp
            if pointer_file.exists():
                try:
                    with open(pointer_file, "r") as f:
                        existing_data = json.load(f)
                    metadata["created_timestamp"] = existing_data.get(
                        "created_timestamp", datetime.now().isoformat()
                    )
                    if verbose:
                        console.print(
                            f"[blue]Updating existing pointer file for {file_info['relative_path']}[/blue]"
                        )
                except Exception:
                    pass  # Use new timestamp if can't read existing

            # Save pointer file
            with open(pointer_file, "w") as f:
                json.dump(metadata, f, indent=2)

            if verbose:
                console.print(
                    f"[green]Created pointer file: {pointer_file.name}[/green]"
                )

        except Exception as e:
            console.print(
                f"[red]Error creating pointer file for {file_info['relative_path']}: {str(e)}[/red]"
            )
