import json
import os
import re
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import requests
import yaml
from pydantic import BaseModel, Field, HttpUrl, field_validator
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...auth.github import GitHubAuth

# from ...auth.oauth import get_user_info  # Function doesn't exist
from ...config.config import Config
from ...utils.token import TokenManager
from .git_operations import GitOperations
from .utils import (
    check_merge_conflicts,
    get_git_status,
    validate_init_command_ran,
    validate_no_large_files,
    validate_stage_command_ran,
)

console = Console()


# Authentication functions removed - now using centralized GitHubAuth class


def push_model_branch(
    repo_path: str,
    branch_name: str,
    commit_message: str,
    config: Config,
    repository_url: Optional[str] = None,
) -> bool:
    """
    Push the model branch to the remote repository.

    Args:
        repo_path: Path to the git repository
        branch_name: Name of the branch to push
        commit_message: Commit message for the changes
        github_token: GitHub token for authentication
        repository_url: Repository URL from model card metadata

    Returns:
        True if push was successful, False otherwise
    """
    try:
        # First, commit any staged changes
        if commit_message:
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0 and "nothing to commit" not in result.stdout:
                console.print(
                    f"[yellow]Warning: Commit failed: {result.stderr}[/yellow]"
                )
                return False

        # Use the same proven authentication logic as the init command
        # Create GitOperations instance (same as init command)
        git_ops = GitOperations(repo_path, config, debug=False)

        # Use the proven _run_git_command_with_auth method
        result = git_ops._run_git_command_with_auth(
            ["git", "push", "--set-upstream", "origin", branch_name], timeout=60
        )

        if result.returncode == 0:
            console.print(
                f"[green]Successfully pushed branch '{branch_name}' to remote[/green]"
            )
            return True
        else:
            console.print(f"[red]Failed to push branch: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print("[red]Error: Git push timed out after 60 seconds[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error pushing branch: {e}[/red]")
        return False


def create_pr_via_api(
    owner: str,
    repo: str,
    branch_name: str,
    model_name: str,
    model_version: str,
    is_first_push: bool,
    github_token: Optional[str] = None,
    config_data: Optional[Config] = None,
    repository_link: Optional[str] = None,
) -> bool:
    """
    Create a PR using GitHub API instead of GitHub CLI.

    Args:
        owner: Repository owner
        repo: Repository name
        branch_name: Name of the branch
        model_name: Name of the model
        model_version: Version of the model
        is_first_push: Whether this is the first push (new PR)
        github_token: GitHub token (optional, will be retrieved if not provided)
        config_data: Configuration data for GitHubAuth
        repository_link: Repository link from model card metadata

    Returns:
        True if PR creation was successful, False otherwise
    """
    try:
        # Get GitHub token from Model Hub API
        if not github_token and config_data:
            try:
                github_auth = GitHubAuth(config_data)
                github_token = github_auth.get_contributions_token()
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not get GitHub token from API: {e}[/yellow]"
                )

        if not github_token:
            console.print(
                "[yellow]Warning: No GitHub token available for PR creation[/yellow]"
            )
            return False

        # Prepare PR data
        if is_first_push:
            pr_title = f"feat: Add model {model_name} {model_version}"
            pr_body = f"""
## Model Submission

**Model Name:** {model_name}
**Version:** {model_version}
**Repository:** {repository_link or "Not specified"}

### Description
This PR adds a new model to the VCP Model Hub.

### Changes
- Added model files and metadata
- Updated model documentation
- Configured model staging

### Validation
- ✅ Init command completed
- ✅ Stage command completed
- ✅ All files staged successfully
- ✅ No large files detected
- ✅ Only .ptr files remain in model_data
"""
        else:
            pr_title = f"chore: Update model {model_name} {model_version}"
            pr_body = f"""
## Model Update

**Model Name:** {model_name}
**Version:** {model_version}
**Repository:** {repository_link or "Not specified"}

### Description
This PR updates the existing model with new changes.

### Changes
- Updated model files and metadata
- Refreshed model documentation
- Updated model staging

### Validation
- ✅ Init command completed
- ✅ Stage command completed
- ✅ All files staged successfully
- ✅ No large files detected
- ✅ Only .ptr files remain in model_data
"""

        # Make API request to create PR
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "vcp-cli",
        }

        data = {"title": pr_title, "head": branch_name, "base": "main", "body": pr_body}

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            return True
        elif response.status_code == 422:
            # PR might already exist
            error_data = response.json()
            if "already exists" in str(error_data):
                return True
            else:
                console.print(
                    f"[yellow]Warning: Could not create PR: {error_data}[/yellow]"
                )
                return False
        else:
            # Suppress 404 warnings as they're often expected (repo not found, no access, etc.)
            if response.status_code != 404:
                console.print(
                    f"[yellow]Warning: GitHub API error ({response.status_code}): {response.text}[/yellow]"
                )
            return False

    except Exception as e:
        console.print(f"[yellow]Warning: Could not create PR via API: {e}[/yellow]")
        return False


def create_or_update_pr(
    repo_path: str,
    branch_name: str,
    model_name: str,
    model_version: str,
    is_first_push: bool,
    github_token: Optional[str] = None,
    config_data: Optional[Config] = None,
    repository_link: Optional[str] = None,
) -> bool:
    """
    Create a new PR or update an existing one.

    Args:
        repo_path: Path to the git repository
        branch_name: Name of the branch
        model_name: Name of the model
        model_version: Version of the model
        is_first_push: Whether this is the first push (new PR)

    Returns:
        True if PR operation was successful, False otherwise
    """
    try:
        # Use repository URL from API if provided, otherwise get from git remote
        if repository_link and "github.com" in repository_link:
            remote_url = repository_link
        else:
            # Get repository owner and name from remote URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                console.print("[red]Could not get remote repository URL[/red]")
                return False

            remote_url = result.stdout.strip()

        # Extract owner/repo from URL (handle both https and ssh formats)
        if "github.com" in remote_url:
            if remote_url.startswith("https://"):
                parts = (
                    remote_url.replace("https://github.com/", "")
                    .replace(".git", "")
                    .split("/")
                )
            else:
                parts = (
                    remote_url.replace("git@github.com:", "")
                    .replace(".git", "")
                    .split("/")
                )

            if len(parts) >= 2:
                owner = parts[0]
                repo = parts[1]
            else:
                console.print("[red]Could not parse repository owner/name[/red]")
                return False
        else:
            console.print("[red]Repository is not hosted on GitHub[/red]")
            return False

        # Use GitHub API to create PR (no CLI dependency)
        return create_pr_via_api(
            owner,
            repo,
            branch_name,
            model_name,
            model_version,
            is_first_push,
            github_token,
            config_data,
            repository_link,
        )

    except Exception as e:
        console.print(f"[yellow]Warning: Could not create/update PR: {e}[/yellow]")
        console.print("[blue]You may need to create the PR manually on GitHub[/blue]")
        return True  # Don't fail the entire process


def validate_version_format(version: str) -> bool:
    """Validate version format against supported patterns."""
    # Pattern 1: v1 (simple version)
    if re.match(r"^v\d+$", version):
        return True

    # Pattern 2: v1.0.0 (semantic versioning)
    if re.match(r"^v\d+\.\d+\.\d+$", version):
        return True

    # Pattern 3: YYYY-MM-DD (date format)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", version):
        try:
            datetime.strptime(version, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    return False


class ModelSubmission(BaseModel):
    """Schema for model submission data to the VCP Model Hub API."""

    model_name: str = Field(..., min_length=1, description="Name of the model")
    version: str = Field(..., description="Version in supported format")
    license_type: str = Field(..., description="License type (e.g., MIT, Apache-2.0)")
    model_repo: HttpUrl = Field(..., description="URL to the model's repository")
    developed_by: List[str] = Field(
        ...,
        min_length=1,
        description="List of organizations or developers who created the model",
    )
    description: str = Field(
        ..., min_length=10, description="Detailed description of the model"
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        if not validate_version_format(v):
            raise ValueError(
                f"Version '{v}' does not comply with supported formats. "
                "Supported formats are:\n"
                "  - v1 (simple version)\n"
                "  - v1.0.0 (semantic versioning)\n"
                "  - YYYY-MM-DD (date format, e.g., 2024-01-15)"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "example-model",
                "version": "v1.0.0",
                "license_type": "MIT",
                "model_repo": "https://github.com/org/example-model",
                "developed_by": ["Organization A", "Developer B"],
                "description": "This is a detailed description of the example model...",
            }
        }


def validate_submission_data(data: Dict[str, Any]) -> Optional[str]:
    """Validate submission data against the schema."""
    try:
        # Check if data is wrapped in a "data" key
        if "data" not in data:
            return "Missing 'data' key in submission"

        # Validate the data against the schema
        ModelSubmission(**data["data"])
        return None
    except Exception as e:
        return str(e)


@click.command()
@click.option("--config", "-c", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed debug information")
@click.option(
    "--work-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the model repository work directory where model configuration is located",
)
@click.option("--skip-git", is_flag=True, help="Skip submission operations")
def submit_command(
    config: Optional[str] = None,
    verbose: bool = False,
    work_dir: Optional[str] = None,
    skip_git: bool = False,
):
    """Submit model for review with comprehensive validation.

    \b
    This command performs the following operations:
    1. Validates that init command was run (model configuration file exists)
    2. Validates that stage command was run (only .ptr files in model_data)
    3. Validates that no large files (>5GB) remain
    4. Submits model data to VCP Model Hub API
    5. Creates submission for model review

    \b
    The command reads submission data from:
    - model_card_docs/model_card_metadata.yaml file in the repository

    \b
    Expected model card metadata structure:
    - model_display_name: Model name for submission
    - model_version: Version (vX.X.X or YYYY-MM-DD format)
    - licenses.name: License type
    - repository_link: Model repository URL
    - authors: List of authors with name field
    - model_description: Detailed model description

    \b
    Work Directory:
    - Use --work-dir to specify the location of model configuration file
    - If not provided, checks current directory first, then prompts for work directory
    - The command will look for model_data directory within the work directory structure

    \b
    Examples:
    - vcp model submit --work-dir /path/to/model/repo
    - vcp model submit --work-dir /path/to/repo --skip-git
    - vcp model submit --work-dir /path/to/repo --verbose
    """
    try:
        console.print(
            "\n[bold blue]Starting model submission with comprehensive validation...[/bold blue]"
        )

        # Step 1: Validate that init command was run
        console.print(
            "\n[bold blue]Step 1: Validating init command was run...[/bold blue]"
        )
        init_valid, metadata_path, metadata = validate_init_command_ran(work_dir)
        if not init_valid:
            return

        console.print("[green]✅ Init command validation passed[/green]")
        console.print(f"[blue]Configuration file: {metadata_path}[/blue]")

        # Extract model information from metadata
        model_name = metadata.get("model_name")
        model_version = metadata.get("model_version")
        output_path = metadata.get("output_path")
        branch_name = metadata.get("branch_name")

        if not all([model_name, model_version, output_path, branch_name]):
            console.print(
                "[red]Error: Incomplete metadata file. Missing required fields.[/red]"
            )
            return

        # Find work directory root early (needed for both repository operations and metadata-only mode)
        output_path_obj = Path(output_path)
        repo_root = None
        for parent in [output_path_obj] + list(output_path_obj.parents):
            if (parent / ".git").exists():
                repo_root = parent
                break

        # Step 2: Validate that stage command was run
        console.print(
            "\n[bold blue]Step 2: Validating stage command was run...[/bold blue]"
        )

        # Construct data path: output_path/*mlflow_pkg/model_data
        # TODO: remove wildcard from mlflow_pkg. Unnecessary and only used for backwards compatibility with testing repos
        mlflow_dirs = list(output_path_obj.glob("*mlflow_pkg"))
        if not mlflow_dirs:
            console.print(
                f"[red]Error: No *mlflow_pkg directory found in {output_path}[/red]"
            )
            return

        mlflow_dir = mlflow_dirs[0]  # Use first match
        model_data_path = mlflow_dir / "model_data"

        if not validate_stage_command_ran(str(model_data_path)):
            return

        console.print("[green]✅ Stage command validation passed[/green]")
        console.print(f"[blue]Model data path: {model_data_path}[/blue]")

        # Step 3: Validate no large files
        console.print(
            "\n[bold blue]Step 3: Validating no large files remain...[/bold blue]"
        )
        if not validate_no_large_files(str(model_data_path)):
            console.print(
                "[yellow]Warning: Large files detected, but proceeding with submission[/yellow]"
            )
        else:
            console.print("[green]✅ No large files validation passed[/green]")

        # Load configuration early (needed for submission operations)
        config_data = Config.load(config)

        # Get GitHub token early (needed for git operations)
        github_token = None
        if not skip_git:
            try:
                github_auth = GitHubAuth(config_data)
                github_token = github_auth.get_contributions_token()
            except Exception as e:
                console.print(
                    f"[red]Error: Could not get GitHub token from API: {e}[/red]"
                )
                console.print(
                    "[yellow]GitHub authentication is required for model submission.[/yellow]"
                )
                return

            # Ensure we have a valid GitHub token
            if not github_token:
                console.print(
                    "[red]Error: No GitHub token available for authentication.[/red]"
                )
                console.print(
                    "[yellow]GitHub authentication is required for model submission.[/yellow]"
                )
                return

        # Step 4: Create submission for review (if not skipped)
        if not skip_git:
            if not repo_root:
                console.print("[red]Error: Could not find work directory root[/red]")
                return

            console.print(f"[blue]Work directory: {repo_root}[/blue]")

            # Check git status
            git_status = get_git_status(str(repo_root))
            if not git_status.get("is_git_repo"):
                console.print(
                    f"[red]Error: Invalid work directory: {git_status.get('error', 'Unknown error')}[/red]"
                )
                return

            # Initialize variables for branch status check
            branch_exists_remote = False
            is_first_push = True

            # Only run full merge conflicts check if there's an existing PR
            if not is_first_push:
                console.print(
                    "[blue]Previous submission found, checking for conflicts...[/blue]"
                )
                merge_info = check_merge_conflicts(str(repo_root), branch_name)

                if merge_info.get("needs_merge"):
                    console.print(
                        f"[yellow]Warning: Submission is {merge_info['behind_count']} commits behind remote[/yellow]"
                    )
                    console.print(
                        "[blue]Consider updating your work directory with latest changes[/blue]"
                    )
                    proceed = click.confirm(
                        "Proceed with submission despite being behind?", default=False
                    )
                    if not proceed:
                        return
            else:
                console.print(
                    "[blue]First submission detected, skipping conflicts check[/blue]"
                )

            # Create appropriate commit message
            if is_first_push:
                commit_message = f"feat: Add model {model_name} {model_version}"
            else:
                commit_message = f"chore: Update model {model_name} {model_version}"

            # Get repository URL from model check API
            model_check_url = f"{config_data.models.base_url}/api/models/check"
            model_check_params = {"model_name": model_name}

            # Get authentication headers for Model Hub API calls
            token_manager = TokenManager()
            headers = token_manager.get_auth_headers()

            if not headers:
                console.print("[red]Not logged in. Please run 'vcp login' first.[/red]")
                return

            try:
                check_response = requests.get(
                    model_check_url, params=model_check_params, headers=headers
                )
                check_response.raise_for_status()
                check_data = check_response.json()

                # Try different possible field names for repository URL
                raw_repository_url = (
                    check_data.get("repo_path")
                    or check_data.get("repository_url")
                    or check_data.get("model_repo")
                    or check_data.get("repo_url")
                    or check_data.get("repository")
                    or ""
                )

                # Use the raw repository URL directly
                repository_url = raw_repository_url
            except Exception as e:
                console.print(
                    f"[red]Error: Could not get repository URL from API: {e}[/red]"
                )
                return

            # Validate repository URL is a GitHub repository
            if not repository_url:
                console.print("[red]Error: No repository URL available.[/red]")
                console.print(
                    "[yellow]Please ensure the repository URL is properly configured.[/yellow]"
                )
                return

            # Check if branch exists on remote (now that we have repository_url)
            console.print("[blue]Checking submission status...[/blue]")
            try:
                # Use centralized GitHubAuth for git ls-remote operation
                github_auth = GitHubAuth(config_data)
                fresh_token = github_auth.get_contributions_token()

                # Set up environment for git operations
                env = os.environ.copy()
                env["GIT_TERMINAL_PROMPT"] = "0"
                env["GIT_CONFIG_GLOBAL"] = "/dev/null"

                # Use embedded token URL for authentication
                auth_url = f"https://{fresh_token}@github.com/"

                result = subprocess.run(
                    [
                        "git",
                        "ls-remote",
                        "--heads",
                        auth_url + repository_url.split("github.com/")[1],
                        branch_name,
                    ],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5,  # Shorter timeout for quick check
                    env=env,
                )

                branch_exists_remote = bool(result.stdout.strip())
                is_first_push = not branch_exists_remote

            except subprocess.TimeoutExpired:
                console.print(
                    "[yellow]Warning: Could not check submission status (timeout), assuming first submission[/yellow]"
                )
                branch_exists_remote = False
                is_first_push = True
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not check submission status: {e}, assuming first submission[/yellow]"
                )
                branch_exists_remote = False
                is_first_push = True

            # Clean the repository URL to remove any authentication tokens for validation
            clean_url = repository_url
            if "@github.com/" in repository_url:
                # Extract the clean GitHub URL from token-authenticated URL
                clean_url = (
                    "https://github.com/" + repository_url.split("@github.com/")[1]
                )

            if not clean_url.startswith("https://github.com/"):
                console.print(
                    "[red]Error: Only GitHub repositories are supported.[/red]"
                )
                console.print(
                    f"[yellow]Repository URL '{repository_url}' is not a GitHub repository.[/yellow]"
                )
                console.print(
                    "[yellow]Please use a GitHub repository URL (https://github.com/owner/repo).[/yellow]"
                )
                return

            # Submit changes and create/update PR
            console.print(f"[blue]Submitting changes for '{branch_name}'...[/blue]")
            if push_model_branch(
                str(repo_root),
                branch_name,
                commit_message,
                config_data,
                repository_url,
            ):
                console.print("[green]✅ Changes submitted successfully[/green]")

                # Create or update PR
                create_or_update_pr(
                    str(repo_root),
                    branch_name,
                    model_name,
                    model_version,
                    is_first_push,
                    github_token,
                    config_data,
                    repository_url,
                )
            else:
                console.print("[red]Error: Failed to submit changes[/red]")
                return
        else:
            console.print("[blue]Skipping submission operations as requested[/blue]")

        # Submit to VCP Model Hub API
        console.print("\n[bold blue]Submitting to VCP Model Hub API...[/bold blue]")

        if verbose:
            console.print("\n[bold blue]Configuration Details:[/bold blue]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Setting", style="dim")
            table.add_column("Value")

            table.add_row(
                "Config File",
                str(Path(config) if config else Path.home() / ".vcp" / "config.yaml"),
            )
            table.add_row("API Base URL", config_data.models.base_url)
            table.add_row("Model Hub Submit Endpoint", "/api/sub/submit")

            console.print(table)

        # Check for valid tokens and get auth headers
        token_manager = TokenManager()
        headers = token_manager.get_auth_headers()

        if not headers:
            console.print("[red]Not logged in. Please run 'vcp login' first.[/red]")
            return

        # User info will be extracted from the token when needed
        user_info = {"name": "Unknown"}

        # Prepare submission data from model_card_metadata.yaml
        console.print("[blue]Reading model card metadata for submission data...[/blue]")

        # Construct path to model_card_metadata.yaml
        model_card_metadata_path = None
        if repo_root:
            model_card_metadata_path = (
                repo_root / "model_card_docs" / "model_card_metadata.yaml"
            )
        else:
            # Fallback to work_dir if repo_root not found
            work_dir_path = Path(work_dir) if work_dir else Path.cwd()
            model_card_metadata_path = (
                work_dir_path / "model_card_docs" / "model_card_metadata.yaml"
            )

        if not model_card_metadata_path.exists():
            console.print(
                f"[red]Error: Model card metadata file not found at {model_card_metadata_path}[/red]"
            )
            console.print(
                "[yellow]Please ensure the model_card_docs/model_card_metadata.yaml file exists in your repository.[/yellow]"
            )
            return

        # Read and parse model_card_metadata.yaml
        try:
            with open(model_card_metadata_path, "r") as f:
                model_card_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            console.print(
                f"[red]Error parsing model card metadata file: {str(e)}[/red]"
            )
            return
        except Exception as e:
            console.print(
                f"[red]Error reading model card metadata file: {str(e)}[/red]"
            )
            return

        if verbose:
            console.print(
                f"[blue]Model card metadata file: {model_card_metadata_path}[/blue]"
            )
            console.print("[blue]Model card metadata loaded successfully[/blue]")

        # Extract submission data from model card metadata
        # Map model card fields to submission data structure
        submission_data = {
            "model_name": model_card_data.get("model_display_name", model_name),
            "version": model_card_data.get("model_version", model_version),
            "license_type": (
                model_card_data.get("licenses", [{}])[0].get("type", "MIT")
                if model_card_data.get("licenses")
                and len(model_card_data.get("licenses", [])) > 0
                else "MIT"
            ),
            "model_repo": model_card_data.get("repository_link", ""),
            "developed_by": [
                author.get("name", "Unknown")
                for author in model_card_data.get("authors", [])
                if author.get("name")
            ]
            or [user_info.get("name", "Unknown")],
            "description": model_card_data.get("model_description")
            or f"Model {model_name} version {model_version}",
        }

        # Auto-detect model_repo from git remote if not provided in model card
        if not submission_data["model_repo"] and repo_root:
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Use the raw URL directly
                raw_url = result.stdout.strip()
                submission_data["model_repo"] = raw_url
            except subprocess.CalledProcessError:
                console.print("[yellow]Warning: Could not get git remote URL[/yellow]")
                submission_data["model_repo"] = "https://github.com/unknown/repo"

        if not submission_data["model_repo"]:
            submission_data["model_repo"] = "https://github.com/unknown/repo"

        # Prepare final submission data
        # Ensure version has "v" prefix and proper format
        version = submission_data["version"]
        if not version.startswith("v"):
            version = f"v{version}"

        # Convert two-part versions (v1.0) to three-part versions (v1.0.0)
        # API only accepts v1 (simple) or v1.0.0 (semantic) formats
        if version.count(".") == 1:  # Two-part version like v1.0
            version = f"{version}.0"  # Convert to v1.0.0

        data = {
            "model_name": submission_data["model_name"],
            "version": version,
            "license_type": submission_data["license_type"],
            "model_repo": submission_data["model_repo"],
            "developed_by": submission_data["developed_by"],
            "description": submission_data["description"],
            "branch_name": branch_name,
            "output_path": str(output_path),
        }

        if verbose:
            console.print("[blue]Submission data prepared successfully[/blue]")
            # Show submission data for debugging (with sensitive info masked)
            safe_data = data.copy()
            if "model_repo" in safe_data and "@github.com/" in str(
                safe_data["model_repo"]
            ):
                # Mask token in model_repo URL
                repo_url = str(safe_data["model_repo"])
                if "@github.com/" in repo_url:
                    safe_data["model_repo"] = (
                        repo_url.split("@github.com/")[0].split("//")[0]
                        + "//***TOKEN***@github.com/"
                        + repo_url.split("@github.com/")[1]
                    )
            console.print("\n[bold blue]Submission Data:[/bold blue]")
            console.print(json.dumps(safe_data, indent=2))

        # Submit to VCP Model Hub API
        url = f"{config_data.models.base_url}/api/sub/submit"

        # Build request body - Always send model_name + model_version (API uses these to generate/validate ID)
        # Optionally include submission_id if available for validation
        request_body = {
            "model_name": metadata["model_name"],
            "model_version": metadata["model_version"],
            "skip_packaging": False,  # Model needs packaging by default
        }

        submission_id = metadata.get("submission_id")
        if submission_id:
            # Include submission_id for validation (API will verify it matches model_name+version)
            request_body["submission_id"] = submission_id

        if verbose:
            console.print(
                "\n[bold blue]Making API request to VCP Model Hub...[/bold blue]"
            )
            console.print(f"URL: {url}")
            # Mask sensitive information in headers
            safe_headers = headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "Bearer ***MASKED***"
            console.print("Headers:", json.dumps(safe_headers, indent=2))
            console.print(
                f"Submitting: {metadata['model_name']} v{metadata['model_version']}"
            )
            if submission_id:
                console.print(f"  (with submission_id: {submission_id})")

        # Make API request to VCP Model Hub
        response = requests.post(url, json=request_body, headers=headers)

        if verbose:
            console.print("\n[bold blue]VCP Model Hub API Response:[/bold blue]")
            console.print(f"Status Code: {response.status_code}")
            console.print("Response:", json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            console.print(
                Panel(
                    "[green]Model data submitted successfully to VCP Model Hub![/green]\n\n"
                    f"Model: {model_name} {model_version}\n"
                    f"Work directory: {output_path}",
                    title="Success",
                )
            )

            # Update last_updated timestamp for resubmissions
            if metadata.get("resubmit", False):
                try:
                    metadata["last_updated"] = datetime.utcnow().isoformat()

                    with open(metadata_path, "w") as f:
                        json.dump(metadata, f, indent=2)

                    console.print("[blue]Resubmission workflow completed.[/blue]")
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not update metadata file: {e}[/yellow]"
                    )
        else:
            console.print(
                Panel(
                    f"[red]Failed to submit model data to VCP Model Hub: {response.text}[/red]",
                    title="Error",
                )
            )

    except Exception as e:
        if verbose:
            console.print("\n[bold red]Detailed Error Information:[/bold red]")
            console.print(traceback.format_exc())
        console.print(f"[red]Error during model submission: {str(e)}[/red]")
