"""Model workspace state management for robust recovery."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ...config.config import Config
from .git_operations import GitOperations

logger = logging.getLogger(__name__)


class ModelWorkspaceState:
    """Manage model workspace state and recovery."""

    def __init__(
        self, output_path: str, config: Optional[Config] = None, debug: bool = False
    ):
        self.output_path = Path(output_path)
        self.metadata_file = self.output_path / ".model-metadata"
        self.git_ops = (
            GitOperations(self.output_path, config, debug) if config else None
        )
        self._metadata_cache: Optional[Dict] = None
        self._metadata_cache_timestamp: Optional[float] = None

    def load_state(self) -> Dict:
        """Load existing workspace state with caching."""
        # Check if we have a valid cache
        if (
            self._metadata_cache is not None
            and self._metadata_cache_timestamp is not None
        ):
            try:
                # Check if file has been modified since cache
                if self.metadata_file.exists():
                    file_mtime = os.path.getmtime(self.metadata_file)
                    if file_mtime <= self._metadata_cache_timestamp:
                        return self._metadata_cache
            except OSError:
                # File might have been deleted, clear cache
                self._metadata_cache = None
                self._metadata_cache_timestamp = None

        # Load from file and cache
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    metadata = json.load(f)

                # Cache the result
                self._metadata_cache = metadata
                self._metadata_cache_timestamp = os.path.getmtime(self.metadata_file)

                return metadata
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load metadata file: {e}")
                return {}

        # File doesn't exist, cache empty result
        self._metadata_cache = {}
        self._metadata_cache_timestamp = 0
        return {}

    def save_state(self, metadata: Dict):
        """Save workspace state and update cache."""
        metadata["last_updated"] = datetime.utcnow().isoformat()
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # Update cache with saved data
            self._metadata_cache = metadata.copy()
            self._metadata_cache_timestamp = os.path.getmtime(self.metadata_file)

        except IOError as e:
            logger.error(f"Failed to save metadata file: {e}")
            raise

    def is_valid_workspace(self) -> bool:
        """Check if directory is valid model workspace."""
        if self.git_ops is None:
            return False
        return self.git_ops.is_valid_workspace()

    def is_same_model(self, model_name: str, model_version: str) -> bool:
        """Check if workspace is for the same model."""
        state = self.load_state()
        return (
            state.get("model_name") == model_name
            and state.get("model_version") == model_version
        )

    def clear_cache(self):
        """Clear the metadata cache."""
        self._metadata_cache = None
        self._metadata_cache_timestamp = None
        logger.debug("Metadata cache cleared")
