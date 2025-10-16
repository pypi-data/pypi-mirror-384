import hashlib
import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import click
import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from ...auth.github import GitHubAuth
from ...config.config import Config
from ...utils.cache import get_vcp_cache_dir
from .models import ModelResponse

console = Console()


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

    # Pattern 4: 1.0.0 (semantic versioning without v prefix)
    if re.match(r"^\d+\.\d+\.\d+$", version):
        return True

    # Pattern 5: 1 (simple version without v prefix)
    if re.match(r"^\d+$", version):
        return True

    return False


def download_single_file(
    download_url: str,
    output_path: str,
    filename: Optional[str] = None,
    model: str = "",
    version: str = "",
    api_url: str = "",
    headers: dict = None,
    timeout: int = 1800,
    verbose: bool = False,
    show_progress: bool = True,
) -> bool:
    """
    Download a single file using a presigned S3 URL.

    Args:
        download_url: The presigned S3 URL
        output_path: Directory path to save the downloaded file
        filename: Optional filename to use
        model: Model name (unused in current implementation)
        version: Model version (unused in current implementation)
        api_url: API URL (unused in current implementation)
        headers: Auth headers (unused in current implementation)
        timeout: Download timeout
        verbose: Whether to show verbose output
        show_progress: Whether to show progress bar

    Returns:
        True if download successful, False otherwise
    """
    try:
        if verbose:
            console.print(f"[blue]Downloading from {download_url}[/blue]")

        response = requests.get(download_url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Determine filename
        if not filename:
            parsed = urlparse(download_url)
            filename = os.path.basename(parsed.path) or "downloaded_file"

        output_file = os.path.join(output_path, filename)
        os.makedirs(output_path, exist_ok=True)

        # Simple download without progress for now
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if verbose:
            console.print(f"[green]Downloaded: {output_file}[/green]")

        return True

    except Exception as e:
        if verbose:
            console.print(f"[red]Download failed: {str(e)}[/red]")
        return False


def download_multiple_files(
    all_files: List[Dict[str, Any]],
    output_path: str,
    model: str,
    version: str,
    timeout: int = 1800,
    verbose: bool = False,
) -> bool:
    """
    Download multiple files.

    Args:
        all_files: List of file info dictionaries
        output_path: Directory to save files
        model: Model name
        version: Model version
        timeout: Download timeout
        verbose: Whether to show verbose output

    Returns:
        True if all downloads successful, False otherwise
    """
    success_count = 0

    for file_info in all_files:
        download_url = file_info.get("download_url")
        filename = file_info.get("filename")

        if not download_url:
            if verbose:
                console.print(f"[yellow]No download URL for {filename}[/yellow]")
            continue

        success = download_single_file(
            download_url,
            output_path,
            filename,
            model,
            version,
            "",
            {},
            timeout,
            verbose,
            True,
        )

        if success:
            success_count += 1
        elif verbose:
            console.print(f"[red]Failed to download {filename}[/red]")

    return success_count == len(all_files)


# Production-grade file upload constants
MAX_PARALLEL_UPLOADS = 5  # Number of concurrent uploads
UPLOAD_TIMEOUT = 600  # 10 minutes base timeout per file (increased by 2x)
MAX_UPLOAD_TIMEOUT = (
    3600  # 60 minutes maximum timeout for very large files (increased by 2x)
)

# Chunk size for downloads (16MB)
CHUNK_SIZE = 16 * 1024 * 1024


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        SHA256 checksum as hex string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_artifact_id(model_name: str, version: str, relative_path: str) -> str:
    """Create artifact ID for a file.

    Args:
        model_name: Name of the model
        version: Version of the model
        relative_path: Relative path of the file

    Returns:
        Unique artifact ID
    """
    combined = f"{model_name}:{version}:{relative_path}"
    return hashlib.sha256(combined.encode()).hexdigest()


def is_presigned_url_expired(presigned_url: str, verbose: bool = False) -> bool:
    """Check if a presigned URL has expired.

    Args:
        presigned_url: The presigned URL to check
        verbose: Whether to show verbose output

    Returns:
        True if expired, False otherwise
    """
    try:
        parsed_url = urlparse(presigned_url)
        query_params = parse_qs(parsed_url.query)

        # Check for 'Expires' parameter
        expires_param = query_params.get("Expires")
        if expires_param:
            expires_timestamp = int(expires_param[0])
            current_timestamp = int(time.time())

            if verbose:
                expires_time = datetime.fromtimestamp(expires_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                current_time = datetime.fromtimestamp(current_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                console.print(f"[blue]URL expires at: {expires_time}[/blue]")
                console.print(f"[blue]Current time: {current_time}[/blue]")
                console.print(
                    f"[blue]URL expired: {current_timestamp >= expires_timestamp}[/blue]"
                )

            return current_timestamp >= expires_timestamp
        else:
            if verbose:
                console.print("[yellow]No expiration parameter found in URL[/yellow]")
            return False
    except Exception as e:
        if verbose:
            console.print(f"[yellow]Could not check URL expiration: {str(e)}[/yellow]")
        return False


def create_upload_state_file(directory: Path, name: str, version: str) -> Path:
    """Create a state file to track upload progress.

    Args:
        directory: Directory being staged
        name: Model name
        version: Model version

    Returns:
        Path to state file
    """
    cache_dir = get_vcp_cache_dir()
    state_filename = f"{name}_{version}_{directory.name}_upload_state.json"
    return cache_dir / state_filename


def load_upload_state(state_file: Path) -> Dict[str, Any]:
    """Load upload state from file.

    Args:
        state_file: Path to state file

    Returns:
        Upload state dictionary
    """
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"completed_files": [], "failed_files": []}
    return {"completed_files": [], "failed_files": []}


def scan_directory_structure(data_path: str) -> List[Dict[str, Any]]:
    """
    Scan directory and build file list with relative paths and metadata.

    Args:
        data_path: Root directory to scan

    Returns:
        List of file info dictionaries
    """
    files_info = []
    base_path = Path(data_path)

    for root, _dirs, files in os.walk(data_path):
        for file in files:
            file_path = Path(root) / file

            # Skip pointer files we create, state files, and hidden files (starting with .)
            if (
                file_path.suffix == ".ptr"
                or file_path.name.startswith(".vcp_upload_state")
                or file_path.name.startswith(".")
            ):
                continue

            relative_path = file_path.relative_to(base_path)
            file_stats = file_path.stat()

            files_info.append({
                "relative_path": str(relative_path),
                "absolute_path": str(file_path),
                "file_size": file_stats.st_size,
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                + "Z",
            })

    return files_info


def get_batch_upload_urls(
    config_data,
    headers: Dict[str, str],
    model: str,
    version: str,
    files_info: List[Dict[str, Any]],
    verbose: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Get batch presigned upload URLs for multiple files.

    Args:
        config_data: Configuration object with API base URL
        headers: Authentication headers
        model: Model name
        version: Model version
        files_info: List of file info dicts
        verbose: Whether to show verbose output

    Returns:
        API response with batch URLs or None if failed
    """
    try:
        # Use hardcoded batch upload endpoint
        batch_endpoint = "/api/models/stage-contributions"
        batch_url = f"{config_data.models.base_url}{batch_endpoint}"

        if verbose:
            console.print("[bold blue]Requesting batch upload URLs...[/bold blue]")
            console.print(f"Files: {len(files_info)}")

        # Prepare request payload
        files_request = []
        for file_info in files_info:
            files_request.append({
                "relative_path": file_info["relative_path"],
                "file_size": file_info["file_size"],
            })

        payload = {"model_name": model, "version": version, "files": files_request}

        response = requests.post(batch_url, json=payload, headers=headers, timeout=60)

        if verbose:
            console.print(f"Batch URL Response Status: {response.status_code}")
            console.print(f"Response Headers: {dict(response.headers)}")
            console.print(f"Response Content: {repr(response.text)}")

        if response.status_code == 200:
            # Check if response has content before parsing JSON
            if not response.text.strip():
                if verbose:
                    console.print("[red]API returned empty response body[/red]")
                return None

            try:
                return response.json()
            except json.JSONDecodeError as e:
                if verbose:
                    console.print(f"[red]Failed to parse JSON response: {e}[/red]")
                    console.print(f"[red]Response content: {repr(response.text)}[/red]")
                return None
        else:
            if verbose:
                console.print(
                    f"[red]Failed to get batch URLs: {response.status_code} - {response.text}[/red]"
                )
            return None

    except Exception as e:
        if verbose:
            console.print(f"[red]Error getting batch upload URLs: {str(e)}[/red]")
        return None


def upload_single_file_to_presigned_url(
    file_info: Dict[str, Any],
    presigned_url: str,
    storage_key: str,
    verbose: bool = False,
    max_retries: int = 3,
) -> bool:
    """
    Upload a single file to S3 using a presigned URL.

    Args:
        file_info: Dictionary containing file information including size_mb
        presigned_url: Presigned S3 URL for upload
        storage_key: Storage key (path) for the file
        verbose: Whether to show verbose output
        max_retries: Maximum number of retry attempts

    Returns:
        True if upload successful, False otherwise
    """
    file_path = Path(file_info["absolute_path"])
    file_size_mb = file_info.get("size_mb", 0)

    # Calculate adaptive timeout based on file size
    base_timeout = UPLOAD_TIMEOUT
    adaptive_timeout = min(base_timeout + (file_size_mb * 2), MAX_UPLOAD_TIMEOUT)

    for attempt in range(max_retries + 1):
        try:
            if verbose and attempt > 0:
                console.print(
                    f"[yellow]Upload attempt {attempt + 1}/{max_retries + 1} for {file_path.name}[/yellow]"
                )

            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()

            console.print(
                f"[blue]Read {len(file_content)} bytes from {file_path.name}[/blue]"
            )
            console.print(f"[blue]Staging with timeout {adaptive_timeout}s...[/blue]")

            # Set proper headers for S3 uploads
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(file_content)),
            }

            response = requests.put(
                presigned_url,
                data=file_content,
                headers=headers,
                timeout=adaptive_timeout,
            )

            console.print(
                f"[blue]Upload response for {file_path.name}: {response.status_code}[/blue]"
            )

            if response.status_code == 200:
                return True
            else:
                console.print(
                    f"Access denied ({response.status_code}) but URL not expired: {response.text}"
                )
                if response.status_code in [400, 403, 404]:
                    # Permanent failures - don't retry
                    console.print(
                        f"Upload failed for {file_path.name} with status {response.status_code}: {response.text}"
                    )
                    return False

        except requests.exceptions.Timeout:
            console.print(
                f"Upload timeout for {file_path.name} on attempt {attempt + 1}"
            )
            if attempt < max_retries:
                time.sleep(2**attempt)  # Exponential backoff
                continue
            else:
                break

        except Exception as e:
            console.print(f"Exception uploading {file_path.name}: {str(e)}")
            if attempt < max_retries:
                time.sleep(2**attempt)
                continue
            else:
                break

    return False


def upload_files_batch_parallel(
    files_upload_mapping: List[Dict[str, Any]],
    model: str = "",
    version: str = "",
    verbose: bool = False,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Upload files sequentially with immediate metadata updates and file deletion.

    Args:
        files_upload_mapping: List of file upload mappings
        model: Model name
        version: Model version
        verbose: Whether to show verbose output
        max_retries: Maximum number of retry attempts per file

    Returns:
        Dictionary with upload results
    """
    successful_uploads = []
    failed_uploads = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        upload_task = progress.add_task(
            f"[cyan]Staging {len(files_upload_mapping)} files...",
            total=len(files_upload_mapping),
        )

        for i, mapping in enumerate(files_upload_mapping, 1):
            file_info = mapping["file_info"]
            presigned_url = mapping["presigned_url"]
            storage_key = mapping["storage_key"]

            console.print(
                f"\n[bold cyan]Processing file {i}/{len(files_upload_mapping)}: {file_info['relative_path']}[/bold cyan]"
            )

            # Calculate file stats before upload
            file_path = Path(file_info["absolute_path"])
            if not file_path.exists():
                console.print(f"[red]File not found: {file_path}[/red]")
                failed_uploads.append({
                    "file_info": file_info,
                    "storage_key": storage_key,
                    "success": False,
                })
                progress.update(upload_task, advance=1)
                continue

            # Calculate file stats
            file_stats = file_path.stat()
            file_size_mb = file_stats.st_size / (1024 * 1024)

            # Add size_mb to file_info for the upload function
            file_info_with_size = file_info.copy()
            file_info_with_size["size_mb"] = file_size_mb

            console.print(
                f"[blue]Staging {file_info['relative_path']} ({file_size_mb:.2f} MB)...[/blue]"
            )

            # Upload the file
            success = upload_single_file_to_presigned_url(
                file_info_with_size,
                presigned_url,
                storage_key,
                verbose=False,
                max_retries=max_retries,
            )

            if success:
                console.print(
                    f"[green]Upload successful: {file_info['relative_path']}[/green]"
                )

                # Immediately update pointer file and delete original
                try:
                    console.print(
                        f"[blue]Updating metadata for: {file_info['relative_path']}[/blue]"
                    )

                    # Load and update pointer file
                    pointer_file = (
                        file_path.parent / f"{file_path.stem}{file_path.suffix}.ptr"
                    )
                    if pointer_file.exists():
                        with open(pointer_file, "r") as f:
                            metadata = json.load(f)

                        # Update metadata with upload completion
                        metadata.update({
                            "upload_status": "completed",
                            "upload_timestamp": datetime.now().isoformat(),
                            "upload_successful": True,
                        })

                        # Save updated metadata
                        with open(pointer_file, "w") as f:
                            json.dump(metadata, f, indent=2)

                        pointer_filename = pointer_file.name
                        console.print(
                            f"[green]Metadata updated: {pointer_filename}[/green]"
                        )

                        # Delete original file
                        file_path.unlink()
                        console.print(
                            f"[green]Original file deleted: {file_info['relative_path']}[/green]"
                        )

                    successful_uploads.append({
                        "file_info": file_info,
                        "storage_key": storage_key,
                        "success": True,
                    })

                except Exception as e:
                    console.print(
                        f"[red]Error updating metadata for {file_info['relative_path']}: {str(e)}[/red]"
                    )
            else:
                console.print(f"[red]Upload failed: {file_info['relative_path']}[/red]")
                failed_uploads.append({
                    "file_info": file_info,
                    "storage_key": storage_key,
                    "success": False,
                })

            progress.update(upload_task, advance=1)

    return {
        "successful": successful_uploads,
        "failed": failed_uploads,
        "total": len(files_upload_mapping),
    }


def save_upload_state(state_file: Path, state: Dict[str, Any]) -> None:
    """Save upload state to file.

    Args:
        state_file: Path to state file
        state: State dictionary to save
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def validate_local_file(
    file_path: Path, pointer_file: Path, verbose: bool = False
) -> bool:
    """Validate if a local file matches its pointer file (checksum and last modified).

    Args:
        file_path: Path to the local file
        pointer_file: Path to the corresponding pointer file
        verbose: Whether to show verbose output

    Returns:
        True if file is valid (matches pointer), False otherwise
    """
    try:
        if not pointer_file.exists():
            if verbose:
                console.print(
                    f"[yellow]No pointer file found for {file_path.name}[/yellow]"
                )
            return False

        # Load pointer metadata
        with open(pointer_file, "r") as f:
            metadata = json.load(f)

        # Check if upload was successful
        if not metadata.get("upload_successful", False):
            if verbose:
                console.print(
                    f"[yellow]Pointer indicates failed upload for {file_path.name}[/yellow]"
                )
            return False

        # Calculate current file checksum
        current_checksum = calculate_file_checksum(file_path)
        stored_checksum = metadata.get("checksum", "").replace("sha256:", "")

        # Get current file modification time
        current_mtime = (
            datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() + "Z"
        )
        stored_mtime = metadata.get("last_modified", "")

        # Check if checksums match
        checksums_match = current_checksum == stored_checksum
        times_match = current_mtime == stored_mtime

        if verbose:
            console.print(f"[blue]Checksums match: {checksums_match}[/blue]")
            console.print(f"[blue]Modification times match: {times_match}[/blue]")

        return checksums_match and times_match

    except Exception as e:
        if verbose:
            console.print(f"[red]Error validating {file_path.name}: {str(e)}[/red]")
        return False


# =============================================================================
# Model Validation Functions
# =============================================================================


def validate_init_command_ran(
    work_dir: str = None, verbose: bool = True
) -> Tuple[bool, str, dict]:
    """
    Validate that the init command was run by checking for model configuration file.

    Args:
        work_dir: Optional work directory path to check
        verbose: Whether to print error messages (default: True)

    Returns:
        Tuple of (is_valid, metadata_path, metadata_content)
    """
    if work_dir:
        # Check in provided work directory
        work_dir_path = Path(work_dir)
        metadata_file = work_dir_path / ".model-metadata"

        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                return True, str(metadata_file), metadata
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not read metadata file: {e}[/yellow]"
                )
                return False, "", {}
        else:
            if verbose:
                console.print("[red]Error: No model workspace found.[/red]")
                console.print()
                console.print("To initialize a model workspace:")
                console.print("  [blue]vcp model init[/blue]")
                console.print()
                console.print("Or specify all parameters:")
                console.print(
                    "  [blue]vcp model init --model-name <name> --model-version <version> --license-type <license> --work-dir <path>[/blue]"
                )
                console.print()
                console.print("Example:")
                console.print(
                    "  [blue]vcp model init --model-name my-model --model-version v1 --license-type MIT --work-dir /tmp/my-model[/blue]"
                )
            return False, "", {}
    else:
        # Check in current directory
        current_dir = Path.cwd()
        metadata_file = current_dir / ".model-metadata"

        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                return True, str(metadata_file), metadata
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not read metadata file: {e}[/yellow]"
                )
                return False, "", {}
        else:
            if verbose:
                console.print("[red]Error: No model workspace found.[/red]")
                console.print()
                console.print("To initialize a model workspace:")
                console.print("  [blue]vcp model init[/blue]")
                console.print()
                console.print("Or specify all parameters:")
                console.print(
                    "  [blue]vcp model init --model-name <name> --model-version <version> --license-type <license> --work-dir <path>[/blue]"
                )
                console.print()
                console.print("Example:")
                console.print(
                    "  [blue]vcp model init --model-name my-model --model-version v1 --license-type MIT --work-dir /tmp/my-model[/blue]"
                )
            return False, "", {}


def validate_model_data_directory(data_path: str) -> bool:
    """
    Validate that the model_data directory exists and is not empty.

    Args:
        data_path: Path to the model_data directory

    Returns:
        True if valid, False otherwise
    """
    data_path_obj = Path(data_path)

    if not data_path_obj.exists():
        console.print(
            f"[red]Error: Model data directory does not exist: {data_path}[/red]"
        )
        console.print(
            "[yellow]The model_data directory needs to be generated first.[/yellow]"
        )
        console.print(
            "[blue]Please run the model training/packaging process to generate model_data.[/blue]"
        )
        return False

    if not data_path_obj.is_dir():
        console.print(f"[red]Error: Path is not a directory: {data_path}[/red]")
        return False

    # Check if directory is empty (ignoring .gitkeep files)
    try:
        files = list(data_path_obj.iterdir())
        # Filter out .gitkeep files
        non_gitkeep_files = [file for file in files if file.name != ".gitkeep"]
        if not non_gitkeep_files:
            console.print(
                f"[red]Error: Model data directory is empty: {data_path}[/red]"
            )
            console.print(
                "[yellow]The model_data directory needs to contain model files.[/yellow]"
            )
            console.print(
                "[blue]Please run the model training/packaging process to generate model files.[/blue]"
            )
            return False
    except PermissionError:
        console.print(
            f"[red]Error: Permission denied accessing directory: {data_path}[/red]"
        )
        return False

    return True


def validate_upload_completion(data_path: str, show_errors: bool = True) -> bool:
    """
    Validate that all files in model_data were uploaded successfully.
    After upload, model_data should only contain *.ptr files and directories.

    Args:
        data_path: Path to the model_data directory
        show_errors: Whether to show error messages (default: True)

    Returns:
        True if all files were uploaded (only .ptr files and directories remain), False otherwise
    """
    data_path_obj = Path(data_path)

    if not data_path_obj.exists():
        return False

    # Files that are allowed to remain (not uploaded to S3)
    allowed_files = {
        ".gitignore",
        ".gitkeep",
    }

    try:
        for item in data_path_obj.rglob("*"):
            if item.is_file():
                # Check if it's a .ptr file or an allowed file
                if not (item.suffix == ".ptr" or item.name in allowed_files):
                    # Found a non-.ptr file that's not in the allowed list, upload is incomplete
                    if show_errors:
                        console.print(
                            f"[red]Error: Found non-uploaded file: {item.relative_to(data_path_obj)}[/red]"
                        )
                        console.print(
                            "[yellow]Not all files have been uploaded successfully.[/yellow]"
                        )
                        console.print(
                            "[blue]The stage command needs to run and update all files before proceeding.[/blue]"
                        )
                        console.print(
                            "[blue]Only .ptr files and directories should remain after successful upload.[/blue]"
                        )
                    return False
    except Exception as e:
        if show_errors:
            console.print(
                f"[yellow]Warning: Could not validate upload completion: {e}[/yellow]"
            )
        return False

    return True


def validate_stage_command_ran(data_path: str) -> bool:
    """
    Validate that the stage command was run successfully.
    After staging, model_data should only contain *.ptr files and directories.

    Args:
        data_path: Path to the model_data directory

    Returns:
        True if staging was successful (only .ptr files and directories remain), False otherwise
    """
    return validate_upload_completion(data_path, show_errors=True)


def validate_no_large_files(data_path: str) -> bool:
    """
    Validate that there are no large files (>5GB) in the model_data directory.
    Large files should have been handled during staging.

    Args:
        data_path: Path to the model_data directory

    Returns:
        True if no large files found, False otherwise
    """
    data_path_obj = Path(data_path)
    large_file_threshold = 5 * 1024 * 1024 * 1024  # 5GB in bytes
    large_files = []

    if not data_path_obj.exists():
        return True  # No directory means no large files

    try:
        for item in data_path_obj.rglob("*"):
            if item.is_file() and item.suffix == ".ptr":
                # Check the original file size from the .ptr file
                try:
                    with open(item, "r") as f:
                        ptr_data = json.load(f)
                    file_size = ptr_data.get("file_size", 0)
                    if file_size > large_file_threshold:
                        large_files.append({
                            "path": item.relative_to(data_path_obj),
                            "size": file_size,
                        })
                except Exception:
                    # If we can't read the .ptr file, skip it
                    continue
    except Exception as e:
        console.print(f"[yellow]Warning: Could not check for large files: {e}[/yellow]")
        return True  # Assume OK if we can't check

    if large_files:
        console.print(
            f"[yellow]Warning: Found {len(large_files)} large files (>5GB) in model_data[/yellow]"
        )
        for file_info in large_files[:3]:  # Show first 3
            size_gb = file_info["size"] / (1024 * 1024 * 1024)
            console.print(f"  - {file_info['path']} ({size_gb:.2f} GB)")
        if len(large_files) > 3:
            console.print(f"  ... and {len(large_files) - 3} more large files")
        console.print(
            "[blue]Large files should have been handled during staging.[/blue]"
        )
        return False

    return True


def check_large_file_considerations(files_info: List[Dict]) -> Dict:
    """
    Check for large files (>5GB) and provide S3 presigned URL considerations.

    Args:
        files_info: List of file information dictionaries

    Returns:
        Dictionary with large file information and recommendations
    """
    large_files = []
    total_large_size = 0
    large_file_threshold = 5 * 1024 * 1024 * 1024  # 5GB in bytes

    for file_info in files_info:
        if file_info.get("file_size", 0) > large_file_threshold:
            large_files.append(file_info)
            total_large_size += file_info.get("file_size", 0)

    if large_files:
        console.print(
            f"[yellow]Warning: Found {len(large_files)} files larger than 5GB[/yellow]"
        )
        console.print("[blue]S3 Presigned URL Considerations for Large Files:[/blue]")
        console.print(
            "  • Presigned URLs have a maximum expiration time (typically 1 hour)"
        )
        console.print(
            "  • Large files may take longer than URL expiration time to upload"
        )
        console.print("  • Consider using multipart upload for files >5GB")
        console.print("  • Monitor upload progress and retry if URL expires")

        for file_info in large_files[:3]:  # Show first 3 large files
            size_gb = file_info.get("file_size", 0) / (1024 * 1024 * 1024)
            console.print(
                f"  - {file_info.get('relative_path', 'unknown')} ({size_gb:.2f} GB)"
            )

        if len(large_files) > 3:
            console.print(f"  ... and {len(large_files) - 3} more large files")

        console.print(
            f"[blue]Total size of large files: {total_large_size / (1024 * 1024 * 1024):.2f} GB[/blue]"
        )

    return {
        "large_files": large_files,
        "total_large_size": total_large_size,
        "has_large_files": len(large_files) > 0,
    }


def get_git_status(repo_path: str) -> Dict:
    """
    Get git status information for the repository.

    Args:
        repo_path: Path to the git repository

    Returns:
        Dictionary with git status information
    """
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return {"is_git_repo": False, "error": result.stderr}

        # Parse git status
        status_lines = (
            result.stdout.strip().split("\n") if result.stdout.strip() else []
        )
        staged_files = []
        unstaged_files = []
        untracked_files = []

        for line in status_lines:
            if line.startswith("??"):
                untracked_files.append(line[3:])
            elif line.startswith("A") or line.startswith("M"):
                staged_files.append(line[3:])
            else:
                unstaged_files.append(line[3:])

        return {
            "is_git_repo": True,
            "staged_files": staged_files,
            "unstaged_files": unstaged_files,
            "untracked_files": untracked_files,
            "has_changes": len(status_lines) > 0,
        }
    except Exception as e:
        return {"is_git_repo": False, "error": str(e)}


def check_merge_conflicts(repo_path: str, branch_name: str) -> Dict:
    """
    Check for potential merge conflicts before pushing.

    Args:
        repo_path: Path to the git repository
        branch_name: Name of the branch to push

    Returns:
        Dictionary with merge conflict information
    """
    try:
        console.print("[blue]Checking for updates...[/blue]")

        # Fetch latest changes from remote with timeout
        result = subprocess.run(
            ["git", "fetch", "origin", "--quiet"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        if result.returncode != 0:
            console.print(
                "[yellow]Warning: Could not check for updates, proceeding with local check[/yellow]"
            )
            return {
                "branch_exists_remote": False,
                "ahead_count": 0,
                "behind_count": 0,
                "needs_merge": False,
            }

        console.print("[blue]Checking submission status...[/blue]")

        # Check if branch exists on remote
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,  # 10 second timeout
        )

        branch_exists_remote = bool(result.stdout.strip())

        if branch_exists_remote:
            # Check if local branch is behind remote
            result = subprocess.run(
                ["git", "rev-list", "--count", f"origin/{branch_name}..{branch_name}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            ahead_count = int(result.stdout.strip()) if result.stdout.strip() else 0

            result = subprocess.run(
                ["git", "rev-list", "--count", f"{branch_name}..origin/{branch_name}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            behind_count = int(result.stdout.strip()) if result.stdout.strip() else 0

            return {
                "branch_exists_remote": True,
                "ahead_count": ahead_count,
                "behind_count": behind_count,
                "needs_merge": behind_count > 0,
            }
        else:
            return {
                "branch_exists_remote": False,
                "ahead_count": 0,
                "behind_count": 0,
                "needs_merge": False,
            }
    except Exception as e:
        return {"error": str(e)}


def validate_code_quality_with_ruff(repo_path: str) -> bool:
    """
    Validate code quality using ruff for linting and formatting on model_card_docs directory.

    Args:
        repo_path: Path to the git repository

    Returns:
        True if code quality validation passes, False otherwise
    """
    try:
        console.print(
            "[blue]Running ruff lint and format validation on model_card_docs...[/blue]"
        )

        # Check if model_card_docs directory exists
        model_card_docs_path = Path(repo_path) / "model_card_docs"
        if not model_card_docs_path.exists():
            console.print(
                "[yellow]Warning: model_card_docs directory not found, skipping ruff validation[/yellow]"
            )
            return True

        # First, run ruff check (linting) on model_card_docs directory
        console.print("[blue]Running ruff check (linting) on model_card_docs...[/blue]")
        result = subprocess.run(
            ["ruff", "check", "model_card_docs"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print("[yellow]Ruff linting found issues:[/yellow]")
            console.print(result.stdout)
            if result.stderr:
                console.print(f"[red]Ruff errors: {result.stderr}[/red]")

            # Ask user if they want to auto-fix
            auto_fix = click.confirm(
                "Would you like to auto-fix the linting issues?", default=True
            )
            if auto_fix:
                console.print(
                    "[blue]Running ruff check --fix on model_card_docs...[/blue]"
                )
                fix_result = subprocess.run(
                    ["ruff", "check", "--fix", "model_card_docs"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                )

                if fix_result.returncode == 0:
                    console.print("[green]✅ Ruff linting issues auto-fixed[/green]")
                else:
                    console.print(
                        "[yellow]Some linting issues could not be auto-fixed[/yellow]"
                    )
                    console.print(fix_result.stdout)
                    if fix_result.stderr:
                        console.print(
                            f"[red]Ruff fix errors: {fix_result.stderr}[/red]"
                        )
            else:
                console.print(
                    "[yellow]Please fix the linting issues manually before proceeding[/yellow]"
                )
                console.print(
                    "[blue]You can run: ruff check --fix model_card_docs[/blue]"
                )
                return False
        else:
            console.print("[green]✅ Ruff linting passed[/green]")

        # Then, run ruff format check
        console.print("[blue]Running ruff format check on model_card_docs...[/blue]")
        format_result = subprocess.run(
            ["ruff", "format", "--check", "model_card_docs"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        if format_result.returncode != 0:
            console.print("[yellow]Ruff formatting found issues:[/yellow]")
            console.print(format_result.stdout)
            if format_result.stderr:
                console.print(f"[red]Ruff format errors: {format_result.stderr}[/red]")

            # Ask user if they want to auto-format
            auto_format = click.confirm(
                "Would you like to auto-format the code?", default=True
            )
            if auto_format:
                console.print("[blue]Running ruff format on model_card_docs...[/blue]")
                format_fix_result = subprocess.run(
                    ["ruff", "format", "model_card_docs"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                )

                if format_fix_result.returncode == 0:
                    console.print("[green]✅ Code auto-formatted with ruff[/green]")
                else:
                    console.print(
                        "[yellow]Some formatting issues could not be auto-fixed[/yellow]"
                    )
                    console.print(format_fix_result.stdout)
                    if format_fix_result.stderr:
                        console.print(
                            f"[red]Ruff format errors: {format_fix_result.stderr}[/red]"
                        )
            else:
                console.print(
                    "[yellow]Please format the code manually before proceeding[/yellow]"
                )
                console.print("[blue]You can run: ruff format model_card_docs[/blue]")
                return False
        else:
            console.print("[green]✅ Ruff formatting passed[/green]")

        console.print(
            "[green]✅ Code quality validation completed successfully[/green]"
        )
        return True

    except FileNotFoundError:
        console.print(
            "[yellow]Warning: ruff not found. Skipping code quality validation.[/yellow]"
        )
        console.print(
            "[blue]To enable code quality validation, install ruff: pip install ruff[/blue]"
        )
        return True  # Don't fail if ruff is not installed
    except Exception as e:
        console.print(f"[yellow]Warning: Error running ruff validation: {e}[/yellow]")
        console.print("[blue]Skipping code quality validation[/blue]")
        return True  # Don't fail the entire process


def run_git_add_after_upload(data_path: str) -> bool:
    """
    Run git add for all files in the repository after successful upload.

    Args:
        data_path: Path to the model_data directory (used to find repo root)

    Returns:
        True if git add was successful, False otherwise
    """
    try:
        # Find the repository root by looking for .git directory
        current_path = Path(data_path)
        repo_root = None

        # Walk up the directory tree to find .git
        for parent in [current_path] + list(current_path.parents):
            if (parent / ".git").exists():
                repo_root = parent
                break

        if not repo_root:
            console.print(
                "[yellow]Warning: Could not find work directory root[/yellow]"
            )
            return False

        # Run git add for all files in the repository
        result = subprocess.run(
            ["git", "add", "."], cwd=repo_root, capture_output=True, text=True
        )

        if result.returncode == 0:
            console.print("[green]Successfully staged all files[/green]")
            return True
        else:
            console.print(
                f"[yellow]Warning: Failed to save files: {result.stderr}[/yellow]"
            )
            return False

    except Exception as e:
        console.print(f"[yellow]Warning: Could not save files: {e}[/yellow]")
        return False


# =============================================================================
# GitHub PR Feedback Functions
# =============================================================================

logger = logging.getLogger(__name__)


class GitHubPRFeedback:
    """Handles GitHub PR feedback retrieval for model reviews."""

    def __init__(self, config: Config):
        """Initialize GitHub PR feedback handler."""
        self.config = config
        self.github_auth = GitHubAuth(config)

    def clean_pr_url(self, pr_url: str) -> str:
        """Clean PR URL by removing any embedded authentication tokens.

        Args:
            pr_url: PR URL that may contain embedded tokens

        Returns:
            Clean PR URL without embedded tokens
        """
        if not pr_url:
            return pr_url

        # Remove token from URL if present (format: https://token@github.com/...)
        if "@" in pr_url:
            # Split on @ and take everything after the first @
            parts = pr_url.split("@", 1)
            if len(parts) > 1:
                clean_url = parts[1]
                # Ensure it starts with https://
                if not clean_url.startswith("https://"):
                    clean_url = f"https://{clean_url}"
                return clean_url

        return pr_url

    def extract_pr_info(self, pr_url: str) -> Tuple[str, str, int]:
        """Extract owner, repo, and PR number from GitHub PR URL.

        Args:
            pr_url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)

        Returns:
            Tuple of (owner, repo_name, pr_number)

        Raises:
            ValueError: If URL format is invalid
        """
        try:
            # Clean the URL first to remove any embedded tokens
            clean_url = self.clean_pr_url(pr_url)

            parsed = urlparse(clean_url)
            if parsed.netloc != "github.com":
                raise ValueError(f"Invalid GitHub URL: {clean_url}")

            path_parts = parsed.path.strip("/").split("/")

            # Handle PR URL format: /owner/repo/pull/123
            if len(path_parts) >= 4 and path_parts[2] == "pull":
                owner = path_parts[0]
                repo_name = path_parts[1]
                pr_number = int(path_parts[3])
                return owner, repo_name, pr_number

            # Handle repository URL format: /owner/repo or /owner/repo.git
            elif len(path_parts) >= 2:
                owner = path_parts[0]
                repo_name = path_parts[1].replace(".git", "")

                # For repository URLs, we need to find the PR number
                # This is a fallback - we'll try to find the most recent PR
                pr_number = self._find_pr_number_for_repo(owner, repo_name)
                if pr_number:
                    return owner, repo_name, pr_number
                else:
                    raise ValueError(f"No PR found for repository: {clean_url}")
            else:
                raise ValueError(f"Invalid URL format: {clean_url}")

        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse PR URL '{pr_url}': {e}") from e

    def _find_pr_number_for_repo(self, owner: str, repo_name: str) -> Optional[int]:
        """Find the most recent PR number for a repository.

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            PR number if found, None otherwise
        """
        try:
            token = self.github_auth.get_contributions_token()
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get the most recent PRs for the repository
            prs_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
            response = requests.get(
                prs_url, headers=headers, params={"state": "open", "per_page": 1}
            )

            if response.status_code == 200:
                prs = response.json()
                if prs:
                    return prs[0]["number"]

            return None

        except Exception as e:
            logger.error(f"Failed to find PR for {owner}/{repo_name}: {e}")
            return None

    def get_pr_comments(self, pr_url: str) -> List[Dict]:
        """Get all comments from a GitHub PR.

        Args:
            pr_url: GitHub PR URL

        Returns:
            List of comment dictionaries
        """
        try:
            owner, repo_name, pr_number = self.extract_pr_info(pr_url)
            token = self.github_auth.get_contributions_token()

            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get PR comments
            comments_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
            response = requests.get(comments_url, headers=headers)
            response.raise_for_status()

            comments = response.json()
            logger.info(f"Retrieved {len(comments)} comments from PR {pr_number}")

            return comments

        except Exception as e:
            logger.error(f"Failed to get PR comments for {pr_url}: {e}")
            return []

    def get_pr_review_comments(self, pr_url: str) -> List[Dict]:
        """Get all review comments from a GitHub PR.

        Args:
            pr_url: GitHub PR URL

        Returns:
            List of review comment dictionaries
        """
        try:
            owner, repo_name, pr_number = self.extract_pr_info(pr_url)
            token = self.github_auth.get_contributions_token()

            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get PR review comments
            review_comments_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/comments"
            response = requests.get(review_comments_url, headers=headers)
            response.raise_for_status()

            review_comments = response.json()
            logger.info(
                f"Retrieved {len(review_comments)} review comments from PR {pr_number}"
            )

            return review_comments

        except Exception as e:
            logger.error(f"Failed to get PR review comments for {pr_url}: {e}")
            return []

    def get_pr_reviews(self, pr_url: str) -> List[Dict]:
        """Get all reviews from a GitHub PR.

        Args:
            pr_url: GitHub PR URL

        Returns:
            List of review dictionaries
        """
        try:
            owner, repo_name, pr_number = self.extract_pr_info(pr_url)
            token = self.github_auth.get_contributions_token()

            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get PR reviews
            reviews_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/reviews"
            response = requests.get(reviews_url, headers=headers)
            response.raise_for_status()

            reviews = response.json()
            logger.info(f"Retrieved {len(reviews)} reviews from PR {pr_number}")

            return reviews

        except Exception as e:
            logger.error(f"Failed to get PR reviews for {pr_url}: {e}")
            return []

    def get_unresolved_feedback(self, pr_url: str) -> Dict:
        """Get all unresolved feedback from a GitHub PR.

        Args:
            pr_url: GitHub PR URL

        Returns:
            Dictionary containing unresolved comments, review comments, and reviews
        """
        try:
            # Get all types of feedback
            comments = self.get_pr_comments(pr_url)
            review_comments = self.get_pr_review_comments(pr_url)
            reviews = self.get_pr_reviews(pr_url)

            # Filter for unresolved items
            unresolved_comments = []
            unresolved_review_comments = []
            unresolved_reviews = []

            # Comments are generally considered unresolved if they're not from the PR author
            # and don't have a resolved status
            for comment in comments:
                # Skip comments from bots or if they appear to be resolved
                if comment.get("user", {}).get("type") == "Bot":
                    continue

                # Check if comment indicates resolution
                body = comment.get("body", "").lower()
                if any(
                    resolved_indicator in body
                    for resolved_indicator in [
                        "resolved",
                        "fixed",
                        "addressed",
                        "done",
                        "completed",
                    ]
                ):
                    continue

                unresolved_comments.append(comment)

            # Review comments are unresolved if they don't have a resolved state
            for review_comment in review_comments:
                if not review_comment.get("resolved", False):
                    unresolved_review_comments.append(review_comment)

            # Reviews are unresolved if they're not approved and have comments
            for review in reviews:
                state = review.get("state", "").lower()
                if state in ["changes_requested", "commented"]:
                    unresolved_reviews.append(review)

            return {
                "unresolved_comments": unresolved_comments,
                "unresolved_review_comments": unresolved_review_comments,
                "unresolved_reviews": unresolved_reviews,
                "total_unresolved": len(unresolved_comments)
                + len(unresolved_review_comments)
                + len(unresolved_reviews),
            }

        except Exception as e:
            logger.error(f"Failed to get unresolved feedback for {pr_url}: {e}")
            return {
                "unresolved_comments": [],
                "unresolved_review_comments": [],
                "unresolved_reviews": [],
                "total_unresolved": 0,
                "error": str(e),
            }

    def format_feedback_summary(self, feedback: Dict, pr_url: str) -> str:
        """Format unresolved feedback into a readable summary.

        Args:
            feedback: Dictionary containing unresolved feedback
            pr_url: GitHub PR URL

        Returns:
            Formatted feedback summary string
        """
        if feedback.get("error"):
            return f"[red]Error fetching PR feedback: {feedback['error']}[/red]"

        total_unresolved = feedback.get("total_unresolved", 0)
        if total_unresolved == 0:
            return "[green]No unresolved feedback found in PR.[/green]"

        summary_parts = [
            f"[yellow]Found {total_unresolved} unresolved feedback items:[/yellow]"
        ]

        # Add comments summary
        comments = feedback.get("unresolved_comments", [])
        if comments:
            summary_parts.append(f"  • {len(comments)} unresolved comments")
            for comment in comments[:3]:  # Show first 3 comments
                author = comment.get("user", {}).get("login", "Unknown")
                body = (
                    comment.get("body", "")[:100] + "..."
                    if len(comment.get("body", "")) > 100
                    else comment.get("body", "")
                )
                summary_parts.append(f"    - {author}: {body}")
            if len(comments) > 3:
                summary_parts.append(f"    ... and {len(comments) - 3} more comments")

        # Add review comments summary
        review_comments = feedback.get("unresolved_review_comments", [])
        if review_comments:
            summary_parts.append(
                f"  • {len(review_comments)} unresolved review comments"
            )
            for comment in review_comments[:2]:  # Show first 2 review comments
                author = comment.get("user", {}).get("login", "Unknown")
                body = (
                    comment.get("body", "")[:100] + "..."
                    if len(comment.get("body", "")) > 100
                    else comment.get("body", "")
                )
                summary_parts.append(f"    - {author}: {body}")
            if len(review_comments) > 2:
                summary_parts.append(
                    f"    ... and {len(review_comments) - 2} more review comments"
                )

        # Add reviews summary
        reviews = feedback.get("unresolved_reviews", [])
        if reviews:
            summary_parts.append(f"  • {len(reviews)} unresolved reviews")
            for review in reviews:
                author = review.get("user", {}).get("login", "Unknown")
                state = review.get("state", "unknown")
                body = (
                    review.get("body", "")[:100] + "..."
                    if len(review.get("body", "")) > 100
                    else review.get("body", "")
                )
                if body:
                    summary_parts.append(f"    - {author} ({state}): {body}")
                else:
                    summary_parts.append(f"    - {author} ({state})")

        return "\n".join(summary_parts)


def format_models_table(models: list[ModelResponse]) -> Table:
    """
    Format models list as a Rich table.

    Args:
        models: List of ModelResponse objects

    Returns:
        Rich Table ready for console.print()
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Model Name")
    table.add_column("Version")
    table.add_column("Description")

    for model in models:
        if model.versions:
            # Add first version with model name
            first_version = model.versions[0]
            table.add_row(
                model.name,
                first_version.version,
                first_version.description or "N/A",
            )

            # Add remaining versions with empty model name
            for version in model.versions[1:]:
                table.add_row(
                    "",
                    version.version,
                    version.description or "N/A",
                )
        else:
            # Model with no versions
            table.add_row(model.name, "No versions", "N/A")

    return table
