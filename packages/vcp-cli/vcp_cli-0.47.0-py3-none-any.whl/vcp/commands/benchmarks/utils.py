import hashlib
import json
import logging
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import numpy as np
from rich.console import Console
from rich.table import Table

from vcp.config.config import Config

logger = logging.getLogger(__name__)
console = Console()


# TODO: will be replaced when implementing https://czi.atlassian.net/browse/VC-3963
CACHE_PATH = Path.home() / ".vcp" / "cache"


# TODO: Move all cache-related methods to a new cache.py module
def save_to_cache(
    model: str, dataset: str, task: Optional[str], data: Any, data_type: str = "auto"
):
    """
    Save data to the local cache directory for a given model, dataset, and task.

    This function serializes and stores data (such as embeddings, results, or datasets)
    in the appropriate subdirectory under ~/.vcp/cache/<model>/<dataset>/task_outputs/<task>/.
    The file type and name are determined by the data_type argument or inferred from the data.
    Creates cache directories automatically if they don't exist.

    Args:
        model (str): The model identifier/key.
        dataset (str): The dataset identifier/key.
        task (Optional[str]): The task identifier/key. If None, data is stored at the
            model/dataset level without task_outputs subdirectory.
        data (Any): The data to cache. Can be a numpy array, dict, or AnnData object.
        data_type (str, optional): Type of data to store. Options are:
            - "embeddings": Save as .npy file
            - "results": Save as .json file
            - "dataset": Save as .h5ad file
            - "auto": Automatically infer type from data. Defaults to "auto".

    Returns:
        None

    Raises:
        CLIError: If the data type is unsupported for caching or if data cannot be serialized.
    """

    if task:
        cache_dir = CACHE_PATH / model / dataset / "task_outputs" / task
    else:
        cache_dir = CACHE_PATH / model / dataset

    cache_dir.mkdir(parents=True, exist_ok=True)

    if data_type == "embeddings" or (
        data_type == "auto" and isinstance(data, np.ndarray)
    ):
        file_path = cache_dir / "embeddings.npy"
        np.save(file_path, data)
    elif data_type == "results" or (data_type == "auto" and isinstance(data, dict)):
        file_path = cache_dir / "results.json"
        file_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    elif data_type == "dataset" or (
        data_type == "auto" and hasattr(data, "write_h5ad")
    ):
        file_path = cache_dir / "dataset.h5ad"
        data.write_h5ad(file_path)
    else:
        raise CLIError(f"Unsupported data type for caching: {type(data)}")


def load_from_cache(
    model: str, dataset: str, task: Optional[str], data_type: str
) -> Any:
    """
    Load cached data for a given model, dataset, and task from the local cache directory.

    Retrieves and deserializes data (such as embeddings, results, or datasets) from
    ~/.vcp/cache/<model>/<dataset>/task_outputs/<task>/ or ~/.vcp/cache/<model>/<dataset>/
    based on whether a task is specified and the data_type requested.

    Args:
        model (str): The model identifier/key.
        dataset (str): The dataset identifier/key.
        task (Optional[str]): The task identifier/key. If None, loads from the
            model/dataset level directory.
        data_type (str): Type of data to load. Must be one of:
            - "embeddings": Load .npy file as numpy array
            - "results": Load .json file as dictionary
            - "dataset": Load .h5ad file as AnnData object

    Returns:
        Any: The loaded data - numpy array for embeddings, dict for results,
             or AnnData object for datasets.

    Raises:
        FileNotFoundError: If the requested cache file does not exist.
        CLIError: If the data_type is not supported.
    """

    if task:
        cache_dir = CACHE_PATH / model / dataset / "task_outputs" / task
    else:
        cache_dir = CACHE_PATH / model / dataset

    if data_type == "embeddings":
        file_path = cache_dir / "embeddings.npy"

        if not file_path.exists():
            raise FileNotFoundError(f"Embeddings not found: {file_path}")

        return np.load(file_path)
    elif data_type == "results":
        file_path = cache_dir / "results.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Results not found: {file_path}")
        return json.loads(file_path.read_text(encoding="utf-8"))
    elif data_type == "dataset":
        file_path = cache_dir / "dataset.h5ad"

        if not file_path.exists():
            raise FileNotFoundError(f"Dataset not found: {file_path}")
        from anndata import read_h5ad  # noqa: PLC0415

        return read_h5ad(file_path)
    else:
        raise CLIError(f"Unsupported data type: {data_type}")


def get_cache_dir(model: str, dataset: str, task: Optional[str] = None) -> Path:
    """
    Get (and create if necessary) the cache directory for a given model, dataset, and task.

    Constructs the path ~/.vcp/cache/<model>/<dataset>/<task>/ and ensures it exists.

    Args:
        model (str): The model key.
        dataset (str): The dataset key.
        task (Optional[str]): The task key. If None, returns the model/dataset directory.

    Returns:
        Path: The Path object for the cache directory.
    """
    if task:
        cache_dir = CACHE_PATH / model / dataset / "task_outputs" / task
    else:
        cache_dir = CACHE_PATH / model / dataset
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def generate_benchmark_key(
    model_key: str, dataset_keys: List[str], task_key: str
) -> str:
    """
    Generate a short hash-based benchmark key from model, dataset, and task information.

    Creates a deterministic 16-character hexadecimal hash from the descriptive
    benchmark key format: {model_key}-[{dataset_keys_joined}]-{task_key}

    Args:
        model_key (str): The model identifier.
        dataset_keys (List[str]): List of dataset identifiers.
        task_key (str): The task identifier.

    Returns:
        str: 16-character hexadecimal hash representing the benchmark.

    Examples:
        >>> generate_benchmark_key("AIDO-cell_3m", ["tsv2_blood"], "clustering")
        'ee79e260a24cdc63'
        >>> generate_benchmark_key("SCVI-multi_species", ["mouse_brain", "mouse_liver"], "clustering")
        'a3ba18c4b6a3ec1f'
    """
    descriptive_key = f"{model_key}-{sorted(dataset_keys)!r}-{task_key}"
    return hashlib.sha256(descriptive_key.encode("utf-8")).hexdigest()[:16]


def format_as_table(
    rows: List[Dict], table_type: str = "auto", depth: int = 2
) -> Table:
    """
    Format a list of dictionaries as a Rich table for console display.

    Infers columns from the data, supports nested dicts up to a specified depth,
    and allows explicit column ordering. Handles missing values and formats
    floats, dicts, and lists for display.

    Args:
        rows (List[Dict]): List of records to display as table rows.
        table_type (str or List[str], optional): Controls column ordering:
            - "auto": Automatically sort columns alphabetically
            - List[str]: Explicit column order; unlisted columns appear after listed ones
            Defaults to "auto".
        depth (int, optional): Maximum depth for flattening nested dictionaries.
            Nested keys become "parent.child" column names. Defaults to 2.

    Returns:
        Table: A Rich Table object ready for console display with proper formatting.
    """

    if not rows:
        return Table()

    def extract_columns(row: Dict, parent: str = "", level: int = 1) -> List[str]:
        cols = []
        for k, v in row.items():
            col_name = f"{parent}.{k}" if parent else k
            if isinstance(v, dict) and level < depth:
                cols.extend(extract_columns(v, col_name, level + 1))
            else:
                cols.append(col_name)
        return cols

    columns_set = set()
    for row in rows:
        columns_set.update(extract_columns(row))
    all_columns = sorted(columns_set)

    if isinstance(table_type, list):
        columns = table_type + [col for col in all_columns if col not in table_type]
    else:
        columns = sorted(all_columns)

    tbl = Table(
        show_header=True, header_style="bold magenta", title="Benchmarks", expand=True
    )
    for col in columns:
        header_text = str(col).replace("_", " ").title()
        min_width = max(12, len(header_text))
        tbl.add_column(header_text, overflow="fold", no_wrap=False, min_width=min_width)

    def get_value(row: Dict, col: str):
        keys = col.split(".")
        val = row
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return ""
        if isinstance(val, float):
            return f"{val:.4f}"
        elif isinstance(val, dict):
            return json.dumps(val)
        elif isinstance(val, list):
            return ", ".join(map(str, val))
        else:
            return str(val)

    for r in rows:
        row_values = [get_value(r, col) for col in columns]
        tbl.add_row(*row_values)
    return tbl


class CLIError(click.ClickException):
    """
    Custom exception class for CLI-related errors.

    Inherits from click.ClickException to provide proper error handling
    and formatting within the Click command-line interface framework.

    Args:
        message (str): The error message to display to the user.
    """

    def __init__(self, message: str):
        super().__init__(message)


class DockerRunner:
    """
    Utility class for running Docker containers with GPU support and custom configurations.

    Provides a simplified interface for executing commands in Docker containers,
    with support for GPU acceleration, volume mounts, and environment variables.

    Attributes:
        Mount: Type alias for mount specification (host_path, container_path, mode).

    Args:
        use_gpu (bool, optional): Whether to enable GPU support with --gpus all. Defaults to True.
        custom_args (Optional[List[str]], optional): Additional Docker arguments. Defaults to None.
    """

    Mount = Tuple[str, str, str]

    def __init__(self, use_gpu: bool = True, custom_args: Optional[List[str]] = None):
        self.use_gpu = use_gpu
        self.custom_args = custom_args or []

    def run(
        self,
        image: str,
        mounts: List[Mount],
        cmd_args: List[str],
        description: str,
        env_vars: Optional[Dict[str, str]] = None,
    ):
        """
        Execute a command in a Docker container with specified configuration.

        Args:
            image (str): Docker image name/tag to run.
            mounts (List[Mount]): List of volume mounts as (host_path, container_path, mode) tuples.
            cmd_args (List[str]): Command and arguments to execute in the container.
            description (str): Human-readable description for logging purposes.
            env_vars (Optional[Dict[str, str]], optional): Environment variables to set. Defaults to None.

        Returns:
            None

        Raises:
            CLIError: If Docker is not found or if the container execution fails.
        """

        cmd = ["docker", "run", "--rm"]
        if self.use_gpu:
            cmd += ["--gpus", "all"]
        cmd.extend(self.custom_args)
        if env_vars:
            for k, v in env_vars.items():
                cmd += ["-e", f"{k}={v}"]
        for host, container, mode in mounts:
            cmd += ["-v", f"{host}:{container}:{mode}"]
        cmd += [image] + cmd_args
        logger.info(f"{description} command: {' '.join(cmd)}")
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, check=True, shell=False
            )
            logger.debug(f"{description} stdout:\n{proc.stdout}")
        except FileNotFoundError as e:
            raise CLIError(
                "Docker not found. Please ensure Docker is installed and accessible in PATH."
            ) from e
        except subprocess.CalledProcessError as e:
            stderr_msg = e.stderr.strip() if e.stderr else "No error output"
            raise CLIError(
                f"{description} failed (exit code {e.returncode}). Docker error: {stderr_msg}"
            ) from e


def mutually_exclusive(*other_names: str):
    """
    Create a Click callback to enforce mutual exclusivity between CLI options.

    Ensures that only one of the mutually exclusive options is provided by the user.
    Raises a Click.BadParameter error if more than one is specified.

    Args:
        *other_names (str): Names of other mutually exclusive options.

    Returns:
        Callable: A Click callback function for use in option definitions.
    """

    def callback(ctx: click.Context, param: click.Parameter, value: Any):
        current_has_value = False
        if isinstance(value, tuple):
            current_has_value = len(value) > 0
        else:
            current_has_value = value is not None

        if current_has_value:
            for other in other_names:
                other_value = ctx.params.get(other)
                other_has_value = False

                if isinstance(other_value, tuple):
                    other_has_value = len(other_value) > 0
                else:
                    other_has_value = other_value is not None

                if other_has_value:
                    param_name_kebab = param.name.replace("_", "-")
                    other_name_kebab = other.replace("_", "-")
                    raise click.BadParameter(
                        f"--{param_name_kebab} and --{other_name_kebab} are mutually exclusive."
                    )
        return value

    return callback


@lru_cache(maxsize=1)
def get_config() -> Config:
    """
    Load and cache the application configuration.

    Uses LRU cache to ensure the configuration is loaded only once per session.
    Handles configuration loading errors gracefully by calling handle_cli_error.

    Returns:
        Config: The loaded configuration object, or None if loading fails.

    Raises:
        CLIError: Via handle_cli_error if configuration cannot be loaded.
    """

    try:
        return Config.load()
    except Exception as e:
        handle_cli_error(CLIError(f"Configuration error: {e}"))
        return None


def validate_benchmark_filters(
    model_filter: Optional[str] = None,
    dataset_filter: Optional[str] = None,
    task_filter: Optional[str] = None,
) -> None:
    """
    Validate benchmark filter parameters for length and content safety.

    Ensures filter strings are within acceptable length limits and don't contain
    potentially dangerous characters that could be used for injection attacks.

    Args:
        model_filter (Optional[str], optional): Model name filter. Defaults to None.
        dataset_filter (Optional[str], optional): Dataset name filter. Defaults to None.
        task_filter (Optional[str], optional): Task name filter. Defaults to None.

    Returns:
        None

    Raises:
        CLIError: If any filter exceeds 100 characters or contains invalid characters (<, >, ", ').
    """

    filters = {
        "model_filter": model_filter,
        "dataset_filter": dataset_filter,
        "task_filter": task_filter,
    }

    for name, value in filters.items():
        if value and len(value) > 100:
            handle_cli_error(CLIError(f"{name} too long (max 100 characters)"))
        if value and any(char in value for char in ["<", ">", '"', "'"]):
            handle_cli_error(CLIError(f"{name} contains invalid characters"))


# TODO: This should just report and non re-raise error to avoid double logging
def handle_cli_error(error: CLIError) -> None:
    console.print(f"[red]Error:[/red] {error}")
    raise error


# TODO: This should just report and non re-raise error to avoid double logging
def handle_unexpected_error(error: Exception, command_name: str) -> None:
    console.print(f"[red]Unexpected error:[/red] {error}")
    console.print("[dim]Check logs for details or contact support.[/dim]")
    raise error
