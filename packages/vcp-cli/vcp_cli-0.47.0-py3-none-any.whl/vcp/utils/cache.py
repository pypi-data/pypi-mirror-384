"""XDG-compliant cache management for vcp-cli."""

import hashlib
import json
import os
import platform
import shutil
from pathlib import Path
from typing import Any, Dict, Optional


def get_xdg_cache_home() -> Path:
    """
    Get the XDG cache directory following XDG Base Directory Specification.

    Returns:
        Path to cache directory based on platform and environment
    """
    system = platform.system()

    if system == "Linux":
        # Linux: Use XDG_CACHE_HOME or default to ~/.cache
        cache_home = os.environ.get("XDG_CACHE_HOME")
        if cache_home:
            return Path(cache_home)
        return Path.home() / ".cache"

    elif system == "Darwin":  # macOS
        # macOS: Use ~/Library/Caches
        return Path.home() / "Library" / "Caches"

    elif system == "Windows":
        # Windows: Use LOCALAPPDATA
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data)
        return Path.home() / "AppData" / "Local"

    else:
        # Fallback for other systems
        return Path.home() / ".cache"


def get_vcp_cache_dir() -> Path:
    """
    Get the vcp-cli cache directory.

    Returns:
        Path to vcp-cli cache directory
    """
    cache_dir = get_xdg_cache_home() / "vcp-cli"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_upload_cache_dir() -> Path:
    """
    Get the upload cache directory for storing upload state and history.

    Returns:
        Path to upload cache directory
    """
    upload_cache = get_vcp_cache_dir() / "uploads"
    upload_cache.mkdir(parents=True, exist_ok=True)
    return upload_cache


def get_benchmark_cache_dir() -> Path:
    """
    Get the benchmark cache directory.

    Returns:
        Path to benchmark cache directory
    """
    benchmark_cache = get_vcp_cache_dir() / "benchmarks"
    benchmark_cache.mkdir(parents=True, exist_ok=True)
    return benchmark_cache


def get_version_cache_dir() -> Path:
    """
    Get the version check cache directory.

    Returns:
        Path to version cache directory
    """
    version_cache = get_vcp_cache_dir() / "version"
    version_cache.mkdir(parents=True, exist_ok=True)
    return version_cache


def migrate_legacy_cache() -> bool:
    """
    Migrate from legacy ~/.vcp/cache to XDG-compliant cache directory.

    Returns:
        True if migration was performed, False if no migration needed
    """
    legacy_cache = Path.home() / ".vcp" / "cache"
    new_cache = get_vcp_cache_dir()

    if not legacy_cache.exists():
        return False

    if new_cache.exists() and any(new_cache.iterdir()):
        # New cache already has content, don't migrate
        return False

    try:
        # Copy legacy cache to new location
        if legacy_cache.exists():
            # Copy benchmarks
            legacy_benchmarks = legacy_cache
            new_benchmarks = get_benchmark_cache_dir()

            for item in legacy_benchmarks.iterdir():
                if item.is_dir():
                    shutil.copytree(
                        item, new_benchmarks / item.name, dirs_exist_ok=True
                    )
                else:
                    shutil.copy2(item, new_benchmarks / item.name)

        # Migrate version cache if it exists
        legacy_version = Path.home() / ".vcp" / "version_check.json"
        if legacy_version.exists():
            new_version_dir = get_version_cache_dir()
            shutil.copy2(legacy_version, new_version_dir / "version_check.json")

        return True

    except Exception as e:
        # Migration failed, but don't break the CLI
        print(f"Warning: Failed to migrate legacy cache: {e}")
        return False


def get_upload_state_file(
    model: str, version: str, data_path: Optional[str] = None
) -> Path:
    """
    Get the upload state file for a specific model/version.

    This provides both local (per-directory) and global (cache) state management.

    Args:
        model: Model name
        version: Model version
        data_path: Optional data path for local state file

    Returns:
        Path to upload state file
    """
    # Create a unique identifier for this upload
    upload_id = f"{model}_{version}"
    if data_path:
        # Include data path hash for uniqueness

        path_hash = hashlib.md5(str(Path(data_path).resolve()).encode()).hexdigest()[:8]
        upload_id = f"{model}_{version}_{path_hash}"

    upload_cache = get_upload_cache_dir()
    return upload_cache / f"{upload_id}.json"


def save_upload_state(
    model: str, version: str, state: Dict[str, Any], data_path: Optional[str] = None
) -> None:
    """
    Save upload state to cache.

    Args:
        model: Model name
        version: Model version
        state: State dictionary to save
        data_path: Optional data path for context
    """
    state_file = get_upload_state_file(model, version, data_path)

    # Add metadata
    state.update({
        "model": model,
        "version": version,
        "data_path": str(Path(data_path).resolve()) if data_path else None,
        "last_updated": __import__("datetime").datetime.now().isoformat(),
    })

    try:
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save upload state: {e}")


def load_upload_state(
    model: str, version: str, data_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load upload state from cache.

    Args:
        model: Model name
        version: Model version
        data_path: Optional data path for context

    Returns:
        Upload state dictionary
    """
    state_file = get_upload_state_file(model, version, data_path)

    if not state_file.exists():
        return {
            "completed_files": [],
            "failed_files": [],
            "started_at": None,
            "last_upload": None,
        }

    try:
        with open(state_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load upload state: {e}")
        return {
            "completed_files": [],
            "failed_files": [],
            "started_at": None,
            "last_upload": None,
        }


def clean_upload_state(
    model: str, version: str, data_path: Optional[str] = None
) -> bool:
    """
    Clean upload state for a specific model/version.

    Args:
        model: Model name
        version: Model version
        data_path: Optional data path for context

    Returns:
        True if state was cleaned, False if no state existed
    """
    state_file = get_upload_state_file(model, version, data_path)

    if state_file.exists():
        try:
            state_file.unlink()
            return True
        except Exception as e:
            print(f"Warning: Failed to clean upload state: {e}")

    return False


def list_upload_history(limit: int = 10) -> list[Dict[str, Any]]:
    """
    List recent upload history from cache.

    Args:
        limit: Maximum number of entries to return

    Returns:
        List of upload state dictionaries, sorted by last_updated
    """
    upload_cache = get_upload_cache_dir()
    history = []

    try:
        for state_file in upload_cache.glob("*.json"):
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    if "last_updated" in state:
                        history.append(state)
            except Exception:
                continue

        # Sort by last_updated, most recent first
        history.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return history[:limit]

    except Exception as e:
        print(f"Warning: Failed to load upload history: {e}")
        return []


def get_cache_size() -> Dict[str, int]:
    """
    Get cache size information.

    Returns:
        Dictionary with cache sizes in bytes
    """
    cache_dir = get_vcp_cache_dir()
    sizes = {}

    try:
        for subdir in ["uploads", "benchmarks", "version"]:
            subdir_path = cache_dir / subdir
            if subdir_path.exists():
                size = sum(
                    f.stat().st_size for f in subdir_path.rglob("*") if f.is_file()
                )
                sizes[subdir] = size
            else:
                sizes[subdir] = 0

        sizes["total"] = sum(sizes.values())
        return sizes

    except Exception as e:
        print(f"Warning: Failed to calculate cache size: {e}")
        return {"total": 0, "uploads": 0, "benchmarks": 0, "version": 0}


def clear_cache(cache_type: Optional[str] = None) -> bool:
    """
    Clear cache data.

    Args:
        cache_type: Type of cache to clear ("uploads", "benchmarks", "version", or None for all)

    Returns:
        True if cache was cleared successfully
    """
    cache_dir = get_vcp_cache_dir()

    try:
        if cache_type is None:
            # Clear all cache
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Clear specific cache type
            subdir = cache_dir / cache_type
            if subdir.exists():
                shutil.rmtree(subdir)
                subdir.mkdir(parents=True, exist_ok=True)

        return True

    except Exception as e:
        print(f"Warning: Failed to clear cache: {e}")
        return False


# Initialize cache and perform migration on import
try:
    migrate_legacy_cache()
except Exception:
    # Don't break CLI if migration fails
    pass
