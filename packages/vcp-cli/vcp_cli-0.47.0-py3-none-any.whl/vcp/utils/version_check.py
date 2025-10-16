"""Version checking utilities for VCP CLI."""

import json
import time
from pathlib import Path
from typing import Optional, Tuple

import requests
from packaging import version as packaging_version

from vcp import __version__

# PyPI package name - change this when the package is published
PYPI_PACKAGE_NAME = "vcp-cli"


def get_current_version() -> str:
    """Get the currently installed version of vcp-cli."""
    return __version__


def get_cache_file() -> Path:
    """Get the cache file path for version information."""
    cache_dir = Path.home() / ".vcp" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "version_check.json"


def is_cache_valid(cache_file: Path, max_age_hours: int = 24) -> bool:
    """Check if the cache file is valid and not expired."""
    if not cache_file.exists():
        return False

    try:
        cache_age = time.time() - cache_file.stat().st_mtime
        return cache_age < (max_age_hours * 3600)
    except OSError:
        return False


def get_cached_version_info(cache_file: Path) -> Optional[dict]:
    """Get cached version information."""
    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_version_info_to_cache(cache_file: Path, latest_version: str) -> None:
    """Save version information to cache."""
    try:
        data = {
            "latest_version": latest_version,
            "timestamp": time.time(),
            "current_version": get_current_version(),
        }
        with open(cache_file, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def get_latest_pypi_version(
    package_name: str = PYPI_PACKAGE_NAME, timeout: int = 5
) -> Optional[str]:
    """Get the latest version available on PyPI.

    Args:
        package_name: The package name on PyPI
        timeout: Request timeout in seconds

    Returns:
        Latest version string if successful, None if failed
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
    except Exception:
        return None


def compare_versions(current: str, latest: str) -> Tuple[bool, str]:
    """Compare current version with latest version.

    Args:
        current: Current version string
        latest: Latest version string

    Returns:
        Tuple of (is_update_available, comparison_result)
    """
    try:
        current_ver = packaging_version.parse(current)
        latest_ver = packaging_version.parse(latest)

        if current_ver < latest_ver:
            return True, f"Update available: {current} → {latest}"
        elif current_ver == latest_ver:
            return False, f"You have the latest version ({current})"
        else:
            return False, f"You have a newer version ({current}) than PyPI ({latest})"
    except Exception as e:
        return False, f"Error comparing versions: {e}"


def check_for_updates_with_cache(
    package_name: str = PYPI_PACKAGE_NAME,
) -> Optional[Tuple[bool, str]]:
    """Check for updates using cache with TTL.

    Only checks PyPI if cache is expired. Returns None if no check needed.

    Args:
        package_name: The package name on PyPI

    Returns:
        Tuple of (is_update_available, status_message) or None if no check needed
    """
    cache_file = get_cache_file()
    current = get_current_version()

    # Check if we have valid cached data
    if is_cache_valid(cache_file):
        cached_info = get_cached_version_info(cache_file)
        if cached_info and cached_info.get("current_version") == current:
            latest = cached_info.get("latest_version")
            if latest:
                is_update_available, message = compare_versions(current, latest)
                return (is_update_available, message) if is_update_available else None

    # Cache expired or invalid, check PyPI
    latest = get_latest_pypi_version(package_name)
    if latest:
        save_version_info_to_cache(cache_file, latest)
        is_update_available, message = compare_versions(current, latest)
        return (is_update_available, message) if is_update_available else None

    return None


def check_for_updates(package_name: str = PYPI_PACKAGE_NAME) -> Tuple[bool, str]:
    """Check if updates are available for the CLI (always checks PyPI).

    Args:
        package_name: The package name on PyPI

    Returns:
        Tuple of (is_update_available, status_message)
    """
    current = get_current_version()
    latest = get_latest_pypi_version(package_name)

    if latest is None:
        return False, f"Could not check for updates (current: {current})"

    return compare_versions(current, latest)
