import json
import logging
import re
import shutil
import traceback
from datetime import datetime
from pathlib import Path

import click
import requests
from copier import run_copy
from rich.console import Console
from rich.panel import Panel

from ...auth.github import GitHubAuth
from ...config.config import Config
from ...utils.token import TokenManager
from .git_operations import GitOperations
from .models import SubmissionResponse
from .utils import validate_version_format
from .workspace import ModelWorkspaceState

logger = logging.getLogger(__name__)
console = Console()


def _verbose_print(message: str, verbose: bool = False) -> None:
    """Print message only if verbose mode is enabled."""
    if verbose:
        console.print(f"[dim]VERBOSE: {message}[/dim]")


def _debug_print(message: str, debug: bool = False) -> None:
    """Print debug message only if debug mode is enabled (includes sensitive info)."""
    if debug:
        console.print(f"[yellow]DEBUG: {message}[/yellow]")


def _verbose_log(message: str, verbose: bool = False) -> None:
    """Log message only if verbose mode is enabled."""
    if verbose:
        logger.info(message)


def _debug_log(message: str, debug: bool = False) -> None:
    """Log debug message only if debug mode is enabled (includes sensitive info)."""
    if debug:
        logger.debug(message)


def _mask_token(token: str, show_chars: int = 4) -> str:
    """Mask sensitive token information for safe logging."""
    if not token or len(token) <= show_chars * 2:
        return "***"
    return f"{token[:show_chars]}...{token[-show_chars:]}"


def _mask_sensitive_data(text: str) -> str:
    """Mask all sensitive information in text for safe sharing in tickets."""

    # Mask GitHub tokens (ghs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
    text = re.sub(r"ghs_[A-Za-z0-9]{36}", "ghs_***MASKED***", text)

    # Mask any token-like strings (40+ character alphanumeric)
    text = re.sub(r"\b[A-Za-z0-9]{40,}\b", "***TOKEN_MASKED***", text)

    # Mask URLs with embedded tokens
    text = re.sub(
        r"https://[^@]+@github\.com/", "https://***TOKEN***@github.com/", text
    )

    # Mask email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "***EMAIL_MASKED***",
        text,
    )

    # Mask API keys and secrets (common patterns)
    text = re.sub(r"\b[A-Za-z0-9]{32,}\b", "***SECRET_MASKED***", text)

    return text


def _debug_print_safe(
    message: str, debug: bool = False, debug_file: str | None = None
) -> None:
    """Print debug message with sensitive data masked for safe sharing."""
    if debug:
        masked_message = _mask_sensitive_data(message)
        console.print(f"[yellow]DEBUG: {masked_message}[/yellow]")

        # Also write to debug file if specified
        if debug_file:
            try:
                with open(debug_file, "a", encoding="utf-8") as f:
                    f.write(f"DEBUG: {masked_message}\n")
            except Exception as e:
                console.print(
                    f"[red]Warning: Could not write to debug file {debug_file}: {e}[/red]"
                )


def _setup_debug_file(debug_file: str | None) -> None:
    """Initialize debug file with header information."""
    if debug_file:
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write("=== VCP CLI Debug Output ===\n")
                f.write(
                    "This file contains debug information with sensitive data masked.\n"
                )
                f.write("Safe to share in support tickets.\n")
                f.write("=" * 50 + "\n\n")
        except Exception as e:
            console.print(
                f"[red]Warning: Could not create debug file {debug_file}: {e}[/red]"
            )


def _should_run_copier(
    work_dir: str, model_name: str, model_version: str, license_type: str
) -> bool:
    """
    Determine if copier should run based on existing files and metadata.

    Args:
        work_dir: Path to the model directory
        model_name: Current model name
        model_version: Current model version
        license_type: Current license type

    Returns:
        True if copier should run, False if files are already up-to-date
    """
    work_dir_obj = Path(work_dir)

    # Check if this is a fresh directory (no template files)
    if not work_dir_obj.exists() or not any(work_dir_obj.iterdir()):
        return True

    # Check for .copier-answers.yml file (indicates copier has run)
    copier_answers_file = work_dir_obj / ".copier-answers.yml"
    if not copier_answers_file.exists():
        return True

    # Check if .model-metadata exists and matches current parameters
    metadata_file = work_dir_obj / ".model-metadata"
    if metadata_file.exists():
        try:
            with open(metadata_file, "r") as f:
                existing_metadata = json.load(f)

            # Compare current parameters with existing metadata
            if (
                existing_metadata.get("model_name") == model_name
                and existing_metadata.get("model_version") == model_version
                and existing_metadata.get("license_type") == license_type
            ):
                # Check if template files exist (basic check for key template files)
                key_template_files = [
                    "model_card_docs/model_card_metadata.yaml",
                    "copier.yml",
                    ".copier-answers.yml",
                ]

                all_template_files_exist = all(
                    (work_dir_obj / file_path).exists()
                    for file_path in key_template_files
                )

                if all_template_files_exist:
                    console.print(
                        "[blue]Template files already exist and match current parameters.[/blue]"
                    )
                    return False
                else:
                    console.print(
                        "[yellow]Template files missing, will regenerate.[/yellow]"
                    )
                    return True
            else:
                console.print(
                    "[yellow]Model parameters changed, will regenerate template files.[/yellow]"
                )
                return True

        except Exception as e:
            console.print(
                f"[yellow]Could not read metadata file: {e}. Will regenerate template files.[/yellow]"
            )
            return True

    # If no metadata file exists, check for basic template structure
    key_template_files = [
        "model_card_docs/model_card_metadata.yaml",
        "copier.yml",
        ".copier-answers.yml",
    ]

    all_template_files_exist = all(
        (work_dir_obj / file_path).exists() for file_path in key_template_files
    )

    if all_template_files_exist:
        console.print(
            "[blue]Template files already exist. Skipping copier execution.[/blue]"
        )
        return False
    else:
        console.print("[yellow]Template files incomplete, will regenerate.[/yellow]")
        return True


@click.command(name="init")
@click.option(
    "--model-name",
    type=str,
    help="Name of the model to initialize.",
)
@click.option(
    "--model-version",
    type=str,
    help="Version of the model to initialize.",
)
@click.option(
    "--license-type",
    type=str,
    help="License type for the model (e.g., MIT, Apache-2.0).",
)
@click.option(
    "--work-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
    help="Path to the model repository work directory where the model will be initialized.",
)
@click.option(
    "--data-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="JSON file containing template data to prefill answers.",
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Run in interactive mode to prompt for required parameters (default when no parameters provided).",
)
@click.option(
    "--workflow-help",
    is_flag=True,
    help="Show workflow guidance and next steps after initialization.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output for debugging and detailed information.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug output (includes sensitive information - use with caution).",
)
@click.option(
    "--debug-file",
    type=click.Path(),
    help="Write debug output to file (automatically masks sensitive data for safe sharing).",
)
@click.option(
    "--iteration",
    is_flag=True,
    help="Indicate this is an iteration on a previously submitted model.",
)
@click.option(
    "--skip-git",
    is_flag=True,
    help="Skip git operations (clone, pull, branch creation) for faster initialization.",
)
def init_command(
    model_name: str | None,
    model_version: str | None,
    license_type: str | None,
    work_dir: str | None,
    data_file: str | None,
    interactive: bool,
    workflow_help: bool,
    verbose: bool,
    debug: bool,
    debug_file: str | None,
    iteration: bool,
    skip_git: bool,
    config: str | None = None,
):
    """Initialize a new model in the VCP Model Hub API.

    Runs in interactive mode by default when no parameters are provided.
    Use --work-dir to specify where to initialize the model repository

    """
    # Setup debug file if specified
    if debug_file:
        _setup_debug_file(debug_file)
        _debug_print_safe("Debug file initialized", debug, debug_file)

    _verbose_print("Starting model initialization", verbose)
    _verbose_log(
        f"Command parameters: model_name={model_name}, model_version={model_version}, license_type={license_type}, work_dir={work_dir}, interactive={interactive}, verbose={verbose}",
        verbose,
    )

    # Check if any required parameters are missing
    required_params = [model_name, model_version, license_type, work_dir]
    has_any_params = any(param is not None for param in required_params)
    _verbose_print(f"Has any parameters: {has_any_params}", verbose)

    # If no parameters provided, automatically run in interactive mode
    if not has_any_params:
        interactive = True
        console.print(
            "[blue]No parameters provided. Running in interactive mode...[/blue]"
        )

    # Interactive mode - prompt for missing parameters
    if interactive:
        # Check for existing .model-metadata in current directory
        current_dir = Path.cwd()
        metadata_file = current_dir / ".model-metadata"
        existing_metadata = None

        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    existing_metadata = json.load(f)
                console.print(
                    "[blue]Found existing model configuration in current directory[/blue]"
                )
                console.print("[blue]Current values:[/blue]")
                console.print(
                    f"  Model name: {existing_metadata.get('model_name', 'N/A')}"
                )
                console.print(
                    f"  Model version: {existing_metadata.get('model_version', 'N/A')}"
                )
                console.print(
                    f"  License type: {existing_metadata.get('license_type', 'N/A')}"
                )
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not read existing metadata: {e}[/yellow]"
                )
                existing_metadata = None

        # Prompt for model name
        if not model_name:
            if existing_metadata and existing_metadata.get("model_name"):
                default_name = existing_metadata["model_name"]
                use_existing = click.confirm(
                    f"Use existing model name '{default_name}'?", default=True
                )
                if use_existing:
                    model_name = default_name
                else:
                    model_name = click.prompt("Model name")
            else:
                model_name = click.prompt("Model name")

        # Prompt for model version
        if not model_version:
            if existing_metadata and existing_metadata.get("model_version"):
                default_version = existing_metadata["model_version"]
                use_existing = click.confirm(
                    f"Use existing model version '{default_version}'?", default=True
                )
                if use_existing:
                    model_version = default_version
                else:
                    model_version = click.prompt("Model version")
            else:
                model_version = click.prompt("Model version")

        # Prompt for license type
        if not license_type:
            if existing_metadata and existing_metadata.get("license_type"):
                default_license = existing_metadata["license_type"]
                use_existing = click.confirm(
                    f"Use existing license type '{default_license}'?", default=True
                )
                if use_existing:
                    license_type = default_license
                else:
                    license_type = click.prompt("License type (e.g., MIT, Apache-2.0)")
            else:
                license_type = click.prompt("License type (e.g., MIT, Apache-2.0)")

        # Prompt for work directory
        if not work_dir:
            if existing_metadata and existing_metadata.get("output_path"):
                default_path = existing_metadata["output_path"]
                use_existing = click.confirm(
                    f"Use existing work directory '{default_path}'?", default=True
                )
                if use_existing:
                    work_dir = default_path
                else:
                    work_dir = click.prompt("Work directory path")
            else:
                work_dir = click.prompt("Work directory path")

    # Check if work directory exists, if not ask user if they want to create it
    work_dir_path = Path(work_dir)
    if not work_dir_path.exists():
        console.print(f"[yellow]Work directory '{work_dir}' does not exist.[/yellow]")

        if interactive:
            # Interactive mode: ask user for confirmation
            create_dir = click.confirm(
                "Do you want to create this directory?", default=True
            )
            if not create_dir:
                console.print(
                    "[red]Cannot proceed without a valid work directory.[/red]"
                )
                return
        else:
            # Non-interactive mode: automatically create the directory
            console.print(
                "[blue]Non-interactive mode: automatically creating directory...[/blue]"
            )

        # Create the directory
        try:
            work_dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]Created work directory: {work_dir}[/green]")
        except Exception as e:
            console.print(f"[red]Error creating directory '{work_dir}': {e}[/red]")
            return

    # Validate that all required parameters are now provided
    if not all([model_name, model_version, license_type, work_dir]):
        console.print("[red]Error: Missing required parameters.[/red]")
        console.print(
            "[yellow]All of model-name, model-version, license-type, and work-dir are required.[/yellow]"
        )
        return

    # Validate version format
    if not validate_version_format(model_version):
        console.print(
            f"[red]Error: Version '{model_version}' does not comply with supported formats.[/red]"
        )
        console.print("[yellow]Supported formats are:[/yellow]")
        console.print("  [cyan]• v1[/cyan] (simple version)")
        console.print("  [cyan]• v1.0.0[/cyan] (semantic versioning)")
        console.print("  [cyan]• YYYY-MM-DD[/cyan] (date format, e.g., 2024-01-15)")
        return

    # Load configuration
    _verbose_print("Loading configuration", verbose)
    config_data = Config.load(config)
    model_hub_url = config_data.models.base_url
    _verbose_print(f"Model Hub URL: {model_hub_url}", verbose)
    _verbose_print(f"Template: {config_data.models.github.template_repo}", verbose)

    # Initialize GitHub authentication
    _verbose_print("Initializing authentication", verbose)
    github_auth = GitHubAuth(config_data)

    # Get GitHub token for git operations
    try:
        github_auth.get_contributions_token()
        _verbose_print("GitHub token obtained successfully", verbose)
    except Exception as e:
        _verbose_print(f"Warning: Could not get GitHub token: {e}", verbose)

    # Initialize workspace state management
    _verbose_print("Initializing workspace state management", verbose)
    workspace = ModelWorkspaceState(work_dir, config_data, debug)

    console.print(f"[blue]Initializing model: {model_name} {model_version}[/blue]")
    console.print(f"[blue]License: {license_type}[/blue]")
    console.print(f"[blue]Work directory: {work_dir}[/blue]")

    # Check for existing workspace and handle smart recovery
    _verbose_print("Checking for existing workspace", verbose)
    if workspace.is_valid_workspace():
        _verbose_print("Valid workspace detected", verbose)
        existing_state = workspace.load_state()
        _verbose_print(f"Existing state: {existing_state}", verbose)

        if workspace.is_same_model(model_name, model_version):
            console.print("[green]Valid workspace detected for this model.[/green]")

            # Set resubmit flag since this model already exists
            existing_metadata = workspace.load_state()
            if not existing_metadata.get("resubmit", False):
                existing_metadata["resubmit"] = True
                workspace.save_state(existing_metadata)
                console.print("[blue]Marked as resubmission workflow.[/blue]")

            # Check if user has made changes
            if workspace.git_ops.has_user_changes():
                console.print(
                    "[yellow]Existing work detected. Preserving user changes.[/yellow]"
                )
                console.print(
                    "[blue]Skipping template generation to avoid overwriting your work.[/blue]"
                )

                console.print("[green]Workspace ready for development.[/green]")

                # Show iteration message if --iteration flag was used
                if iteration:
                    console.print("\n[bold blue]🔄 Iteration Mode[/bold blue]")
                    console.print(
                        "You're working on addressing review feedback for a previously submitted model."
                    )
                    console.print(
                        f"Run 'vcp model assist --work-dir {work_dir}' to see what needs to be addressed."
                    )

                return
            else:
                console.print(
                    "[yellow]Empty workspace detected. Proceeding with initialization.[/yellow]"
                )
        else:
            console.print("[red]Directory contains different model.[/red]")
            console.print(f"[yellow]Expected: {model_name} {model_version}[/yellow]")
            console.print(
                f"[yellow]Found: {existing_state.get('model_name', 'unknown')} {existing_state.get('model_version', 'unknown')}[/yellow]"
            )
            console.print("[red]Please use a different output directory.[/red]")
            return

    try:
        # Step 1: Check if model exists in model hub
        console.print("[yellow]Checking if model exists...[/yellow]")
        check_url = f"{model_hub_url}/api/models/check"
        check_params = {"model_name": model_name}
        _verbose_print(f"API check URL: {check_url}", verbose)
        _verbose_print(f"Check parameters: {check_params}", verbose)

        # Get authentication headers for API calls
        _verbose_print("Getting authentication headers", verbose)
        token_manager = TokenManager()
        headers = token_manager.get_auth_headers()

        if not headers:
            console.print("[red]Not logged in. Please run 'vcp login' first.[/red]")
            return

        _verbose_print(f"Request headers: {list(headers.keys())}", verbose)

        _verbose_print("Making API request to check model existence", verbose)
        check_response = requests.get(check_url, params=check_params, headers=headers)
        _verbose_print(f"Response status: {check_response.status_code}", verbose)
        _verbose_print(f"Response headers: {dict(check_response.headers)}", verbose)
        _verbose_print(
            f"Response content type: {check_response.headers.get('content-type', 'unknown')}",
            verbose,
        )
        _verbose_print(
            f"Response text (first 500 chars): {check_response.text[:500]}", verbose
        )
        check_response.raise_for_status()
        check_data = check_response.json()
        _verbose_print(f"Response data: {check_data}", verbose)

        repo_path = check_data.get("repo_path")

        if repo_path:
            # Model exists - handle existing repository with branch management
            console.print("[green]Model exists![/green]")

            # Generate branch name (standardized format)
            branch_name = f"{model_name}_{model_version}"

            # Check if work directory exists and has content
            work_dir_obj = Path(work_dir)
            dir_exists = work_dir_obj.exists()
            has_content = dir_exists and any(work_dir_obj.iterdir())

            if dir_exists:
                # Check what type of directory this is
                git_ops = GitOperations(work_dir, config_data, debug)
                is_git_repo = git_ops.is_git_repository()
                is_valid_workspace = git_ops.is_valid_workspace()

                if is_valid_workspace:
                    console.print(
                        "[green]Valid model workspace found. Checking status...[/green]"
                    )
                elif is_git_repo:
                    console.print(
                        "[yellow]Git repository found but not a valid model workspace. Checking status...[/yellow]"
                    )
                elif has_content:
                    console.print(
                        "[yellow]Directory exists with files but is not a git repository. Checking status...[/yellow]"
                    )
                else:
                    console.print(
                        "[blue]Empty directory found. Will set up model workspace...[/blue]"
                    )

                # Only proceed with git operations if it's a valid git repository
                if is_git_repo:
                    # Update main branch first
                    git_ops.update_main_branch()

                    # Check if model branch exists
                    branch_exists, _ = git_ops.branch_exists(branch_name)
                    if branch_exists:
                        # Check if there's an open PR for this branch
                        try:
                            repo_owner, repo_name = github_auth.get_repo_info(repo_path)
                            github_auth.check_pr_exists(
                                repo_owner, repo_name, branch_name
                            )
                        except Exception:
                            pass

                        if not git_ops.checkout_branch(branch_name):
                            return

                        # Update the model branch with latest changes from main
                        git_ops.update_model_branch(branch_name)
                    else:
                        if not git_ops.create_branch(branch_name):
                            return
                else:
                    # Not a git repository, need to clone it
                    console.print("[yellow]Setting up existing model...[/yellow]")

                    # Remove existing directory if it has content but isn't a git repo
                    if has_content:
                        console.print(
                            "[yellow]Removing existing non-git directory...[/yellow]"
                        )
                        shutil.rmtree(work_dir)
                        work_dir_obj.mkdir(parents=True, exist_ok=True)

                    # Clone the repository using GitHub authentication
                    github_auth.clone_repository(repo_path, work_dir)
                    console.print(
                        f"[green]Model setup successfully in: {work_dir}[/green]"
                    )

                    # Create feature branch from main
                    git_ops = GitOperations(work_dir, config_data, debug)
                    if not git_ops.create_branch(branch_name):
                        return
            else:
                # Fresh clone - clone repository and create feature branch
                console.print("[yellow]Setting up existing model...[/yellow]")

                # Ensure work directory exists
                work_dir_obj.mkdir(parents=True, exist_ok=True)

                # Clone the repository using GitHub authentication
                github_auth.clone_repository(repo_path, work_dir)
                console.print(f"[green]Model setup successfully in: {work_dir}[/green]")

                # Create feature branch from main
                logger.debug(
                    f"About to call create_branch with work_dir={work_dir}, branch_name={branch_name}"
                )
                if not github_auth.create_branch(work_dir, branch_name):
                    logger.error("create_branch returned False")
                    return
                logger.debug("create_branch completed successfully")

            # Create .model-metadata file with branch information
            metadata = {
                "model_name": model_name,
                "model_version": model_version,
                "license_type": license_type,
                "branch_name": branch_name,
                "output_path": work_dir,  # Keep output_path for backward compatibility
                "template_version": "v1.0.0",  # TODO: Get from template repo
                "template_repo": config_data.models.github.template_repo,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
            }
            workspace.save_state(metadata)
            console.print("[blue]Created model configuration[/blue]")

        else:
            # Model doesn't exist - create new repository via API
            console.print("[yellow]Model doesn't exist. Creating new model...[/yellow]")

            # Call model hub API to create new submission
            create_url = f"{model_hub_url}/api/sub"
            create_data = {
                "model_name": model_name,
                "model_version": model_version,
                "license_type": license_type,
            }
            _verbose_print(f"Create submission URL: {create_url}", verbose)
            _verbose_print(f"Create data: {create_data}", verbose)

            # Get authentication headers for API calls
            _verbose_print(
                "Getting authentication headers for submission creation", verbose
            )
            token_manager = TokenManager()
            headers = token_manager.get_auth_headers()

            if not headers:
                console.print("[red]Not logged in. Please run 'vcp login' first.[/red]")
                return

            _verbose_print("Making API request to create submission", verbose)
            create_response = requests.post(
                create_url, json=create_data, headers=headers
            )
            _verbose_print(
                f"Create response status: {create_response.status_code}", verbose
            )
            create_response.raise_for_status()

            # Parse response using Pydantic model
            submission_response = SubmissionResponse.model_validate(
                create_response.json()
            )
            _verbose_print(
                f"Create result: {submission_response.model_dump()}", verbose
            )

            # Extract submission data from validated response
            repo_url = submission_response.submission.repo_url
            submission_id = submission_response.submission.submission_id
            console.print("[green]New model created[/green]")

            # Clone the newly created repository
            console.print("[yellow]Setting up new model...[/yellow]")

            # Ensure work directory exists
            work_dir_obj = Path(work_dir)
            work_dir_obj.mkdir(parents=True, exist_ok=True)

            # Clone the repository using GitHub authentication
            github_auth.clone_repository(repo_url, work_dir)
            console.print(f"[green]Model setup successfully in: {work_dir}[/green]")

            # Create feature branch from main (standardized format)
            branch_name = f"{model_name}_{model_version}"
            _verbose_print(f"About to create branch {branch_name}", verbose)
            try:
                _verbose_print(
                    f"Creating GitOperations with work_dir={work_dir}",
                    verbose,
                )
                git_ops = GitOperations(work_dir, config_data, debug)
                _verbose_print(
                    f"About to call git_ops.create_branch({branch_name})", verbose
                )
                if not git_ops.create_branch(branch_name):
                    _verbose_print("git_ops.create_branch returned False", verbose)
                    return
                _verbose_print("git_ops.create_branch completed successfully", verbose)
            except Exception as e:
                _verbose_print(
                    f"Exception in GitOperations.create_branch: {e}", verbose
                )
                _verbose_print(f"Exception type: {type(e)}", verbose)
                _verbose_print(f"Traceback: {traceback.format_exc()}", verbose)
                return

            # Create .model-metadata file with branch information and submission_id
            metadata = {
                "model_name": model_name,
                "model_version": model_version,
                "license_type": license_type,
                "branch_name": branch_name,
                "output_path": work_dir,  # Keep output_path for backward compatibility
                "template_version": "v1.0.0",  # TODO: Get from template repo
                "template_repo": config_data.models.github.template_repo,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "submission_id": submission_id,  # Save submission_id from API response
            }
            workspace.save_state(metadata)
            console.print("[blue]Created model configuration[/blue]")

        # Step 2: Check if copier should run or skip
        _verbose_print("Checking if copier should run", verbose)
        should_run_copier = _should_run_copier(
            work_dir, model_name, model_version, license_type
        )
        _verbose_print(f"Should run copier: {should_run_copier}", verbose)

        if should_run_copier:
            console.print("[yellow]Running copier with template data...[/yellow]")

            # Load data from file if provided
            data = {
                "model_name": model_name,
                "model_version": model_version,
                "license_type": license_type,
                "model_display_name": model_name,  # Use model_name as display name
            }
            _verbose_print(f"Initial copier data: {data}", verbose)

            if data_file:
                _verbose_print(f"Loading data from file: {data_file}", verbose)
                try:
                    file_path = Path(data_file)
                    content = file_path.read_text()
                    # Parse as JSON and merge with existing data
                    file_data = json.loads(content)
                    data.update(file_data)
                    _verbose_print(f"Updated data with file content: {data}", verbose)
                except Exception as e:
                    console.print(f"[red]Error loading data file: {e}[/red]")
                    return

            # Get template URL
            template_repo = config_data.models.github.template_repo
            _verbose_print(f"Template: {template_repo}", verbose)

            # Always run in non-interactive mode since we have all required data
            data["interactive_mode"] = False
            _verbose_print(f"Final copier data: {data}", verbose)
            _verbose_print(
                f"Running copier with template={template_repo}, destination={work_dir}",
                verbose,
            )
            run_copy(
                src_path=template_repo,
                dst_path=work_dir,
                data=data,
                overwrite=True,
                defaults=True,  # Use defaults for unspecified fields
                vcs_ref="main",
            )

            console.print("[green]Template files generated successfully![/green]")
        else:
            console.print(
                "[blue]Template files are already up-to-date. Skipping copier execution.[/blue]"
            )

        console.print("[green]Model initialization completed successfully![/green]")
        console.print(f"[green]Model files are available in: {work_dir}[/green]")

        # Show workflow guidance if requested
        if workflow_help:
            console.print("\n[bold blue]🤖 Workflow Assistant[/bold blue]")
            console.print(
                Panel(
                    "[bold green]✅ Step 1 Complete: Model Initialized[/bold green]\n\n"
                    "[bold blue]Next Steps:[/bold blue]\n"
                    "1. Review files and edit the necessary files, all model_card_files required to be updated\n"
                    "2. Add your model files to the model_data directory\n"
                    "3. Run: [cyan]vcp model stage --interactive[/cyan]\n"
                    "4. Then run: [cyan]vcp model submit --work-dir {work_dir}[/cyan]\n\n"
                    "[bold yellow]💡 Tip:[/bold yellow] Use [cyan]vcp model assist[/cyan] for step-by-step guidance!",
                    title="Workflow Guidance",
                )
            )

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error communicating with Model Hub API: {e}[/red]")
        _verbose_log(f"Request exception details: {e}", verbose)
        if hasattr(e, "response") and e.response is not None:
            console.print(f"[red]Response: {e.response.text}[/red]")
            _verbose_log(f"Response status: {e.response.status_code}", verbose)
            _verbose_log(f"Response headers: {dict(e.response.headers)}", verbose)
        console.print("[yellow]Recovery suggestions:[/yellow]")
        console.print("  • Check your internet connection")
        console.print("  • Verify you're logged in: vcp login")
        console.print("  • Try again in a few moments")
    except Exception as e:
        console.print(f"[red]Error during model initialization: {e}[/red]")
        _verbose_log(f"Exception details: {e}", verbose)
        logger.error(f"Error during model initialization: {e}", exc_info=True)

        # Provide recovery guidance based on error type
        if "authentication" in str(e).lower() or "token" in str(e).lower():
            console.print(
                "[yellow]Authentication error detected. Recovery suggestions:[/yellow]"
            )
            console.print("  • Re-authenticate: vcp logout && vcp login")
            console.print("  • Check permissions")
        else:
            console.print("[yellow]General recovery suggestions:[/yellow]")
            console.print("  • Try running the command again")
            console.print("  • Use a different output directory")
            console.print("  • Check the logs for more details")
