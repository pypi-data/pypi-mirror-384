import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator

from .api import fetch_benchmarks_by_key
from .tasks_cli_handler import process_all_task_inputs
from .utils import CLIError, handle_cli_error

logger = logging.getLogger(__name__)


def _user_dataset_key(path: Path) -> str:
    """
    Generate a robust, unique key for user datasets.

    Uses file metadata (path, size, modification time) to create a content-aware
    hash that avoids cache collisions while being fast to compute.

    Args:
        path: Path to the user dataset file

    Returns:
        str: A unique dataset key in format 'user_dataset_{sanitized_name}_{hash}'
    """
    try:
        resolved_path = path.resolve()
        stat_info = resolved_path.stat()

        payload = (
            f"{resolved_path}|{stat_info.st_size}|{int(stat_info.st_mtime)}".encode()
        )
        content_hash = hashlib.sha256(payload).hexdigest()[:12]

    except Exception:
        content_hash = hashlib.sha256(str(path).encode()).hexdigest()[:12]

    sanitized_name = "".join(c if c.isalnum() else "_" for c in path.stem)

    return f"user_dataset_{sanitized_name}_{content_hash}"


class UserDatasetSpec(BaseModel):
    """
    Pydantic model for user-provided dataset configuration.

    Validates and manages user dataset specifications including the dataset
    class, organism type, and file path. Automatically expands user paths
    and validates file existence.

    Attributes:
        dataset_class (str): Fully qualified class name for the dataset.
        organism (str): Organism type (e.g., "HUMAN", "MOUSE").
        path (Path): Resolved path to the dataset file.
    """

    dataset_class: str
    organism: str
    path: Path

    @field_validator("path", mode="before")
    @classmethod
    def validate_path_exists_and_expand(cls, v):
        p = Path(v).expanduser()
        if not p.exists():
            handle_cli_error(CLIError(f"User dataset file not found: {p}"))
        return p

    model_config = {"extra": "forbid", "protected_namespaces": ()}


class BenchmarkRunSpec(BaseModel):
    """
    Complete specification for running a benchmark evaluation.

    Defines all parameters needed to execute a benchmark including model
    selection, dataset configuration, task specification, and baseline
    options. Supports both VCP models and precomputed cell representations,
    as well as both czbenchmarks datasets and user-provided datasets.

    Attributes:
        model_key (Optional[str]): VCP model identifier.
        czb_dataset_key (Optional[str]): czbenchmarks dataset identifier.
        user_dataset (Optional[UserDatasetSpec]): User-provided dataset config.
        task_key (Optional[str]): Benchmark task identifier.
        cell_representation (Optional[Path]): Path to precomputed embeddings.
        run_baseline (bool): Whether to compute baseline metrics.
        baseline_args (Optional[Dict[str, Any]]): Baseline computation parameters.
    """

    model_key: Optional[str] = None
    czb_dataset_keys: List[str] = []
    user_datasets: List[UserDatasetSpec] = []
    task_key: str
    # str support both paths or AnnData refs from dataset
    cell_representations: List[str] = []
    run_baseline: bool = False
    baseline_args: Optional[Dict[str, Any]] = None
    task_inputs: Optional[Dict[str, Any]] = None

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "protected_namespaces": (),
    }

    @classmethod
    def from_cli_args(cls, args: Dict) -> "BenchmarkRunSpec":
        """
        Create a BenchmarkRunSpec from CLI arguments.

        Parses and validates CLI arguments to create a complete benchmark
        specification. Handles JSON parsing for user datasets and baseline
        arguments, and resolves benchmark keys to individual components.

        Args:
            args (Dict): Dictionary of CLI arguments from click.

        Returns:
            BenchmarkRunSpec: Validated benchmark specification.

        Raises:
            CLIError: If required arguments are missing, JSON parsing fails,
                    or benchmark key resolution fails.
        """
        model_key = args.get("model_key")
        cell_reps = list(args.get("cell_representation", ()) or [])
        czb_dataset_keys = list(args.get("dataset_key", ()) or [])
        user_dataset_specs = list(args.get("user_dataset", ()) or [])
        task_key = args.get("task_key")

        benchmark_key = args.get("benchmark_key")
        if benchmark_key:
            try:
                record = fetch_benchmarks_by_key(benchmark_key)
                model_key = record.model_key
                czb_dataset_keys = record.dataset_keys or []
                task_key = record.task_key
                if not czb_dataset_keys:
                    handle_cli_error(
                        CLIError(
                            f"No datasets found for benchmark key '{benchmark_key}'"
                        )
                    )
            except Exception as e:
                handle_cli_error(
                    CLIError(f"Failed to resolve benchmark key '{benchmark_key}': {e}")
                )

        spec_data: Dict[str, Any] = {
            "model_key": model_key,
            "czb_dataset_keys": czb_dataset_keys,
            "cell_representations": cell_reps,
            "task_key": task_key,
            "run_baseline": args.get("run_baseline", False),
        }

        if user_dataset_specs:
            try:
                parsed: List[UserDatasetSpec] = []
                for item in user_dataset_specs:
                    parsed.append(UserDatasetSpec(**json.loads(item)))
                spec_data["user_datasets"] = parsed
            except Exception as e:
                handle_cli_error(CLIError(f"Invalid user dataset: {e}"))

        if args.get("baseline_args"):
            try:
                spec_data["baseline_args"] = json.loads(args["baseline_args"])
                spec_data["run_baseline"] = True
            except Exception as e:
                handle_cli_error(CLIError(f"Invalid baseline args: {e}"))

        if args.get("task_inputs"):
            try:
                spec_data["task_inputs"] = json.loads(args["task_inputs"])
            except Exception as e:
                handle_cli_error(CLIError(f"Invalid task inputs: {e}"))

        spec = cls(**spec_data)

        dyn_task = spec._normalize_cli_param_values(args.get("task_params"))
        dyn_base = spec._normalize_cli_param_values(args.get("baseline_params"))
        if dyn_task:
            spec_data["task_inputs"] = {
                **(spec_data.get("task_inputs") or {}),
                **dyn_task,
            }
        if dyn_base:
            spec_data["baseline_args"] = {
                **(spec_data.get("baseline_args") or {}),
                **dyn_base,
            }
            spec_data["run_baseline"] = True

        spec = cls(**spec_data)

        task_inputs = process_all_task_inputs(spec.task_key, args, [])
        if task_inputs:
            spec.task_inputs = {**(spec.task_inputs or {}), **task_inputs}

        if not (
            (spec.model_key or spec.cell_representations)
            and (spec.czb_dataset_keys or spec.user_datasets)
            and spec.task_key
        ):
            handle_cli_error(
                CLIError(
                    "Missing required arguments: model/cell_representation, dataset/user-dataset, or task. Use --help for details."
                )
            )

        logger.info(
            f"Selected benchmark run - "
            f"Model: {spec.model_key}, "
            f"Dataset: {spec.dataset_key}, "
            f"Task: {spec.task_key}"
        )

        return spec

    def _parse_dynamic_params(self, value: Any) -> Any:
        """
        Parse dynamic CLI parameter values for task/baseline params.

        Handles AnnData references, JSON strings, and passthrough values.
        """
        if isinstance(value, str) and value.startswith("@"):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value

    def _normalize_cli_param_values(
        self, raw: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Normalize CLI parameter values for task/baseline params.

        Converts stringified JSON and AnnData references to usable Python objects.
        """
        if not raw:
            return {}
        out: Dict[str, Any] = {}
        for k, v in raw.items():
            if isinstance(v, tuple):
                continue
            else:
                out[k] = self._parse_dynamic_params(v)
        return out

    @property
    def key(self) -> str:
        """
        Generate a unique key for this benchmark run.

        Creates a composite key from model, dataset, and task for caching
        and identification purposes.

        Returns:
            str: Formatted key as "model-dataset-task".
        """

        return f"{self.model_key}-{self.dataset_key}-{self.task_key}"

    @property
    def dataset_keys(self) -> List[str]:
        """
        Get the dataset key for this benchmark run.

        Returns either the czbenchmarks dataset key or a generated key
        for user datasets based on the filename.

        Returns:
            str: Dataset key for caching and identification.

        Note:
            For user datasets, generates a sanitized key from the filename.
            This may cause cache collisions for files with identical names.
        """

        keys: List[str] = []
        keys.extend(self.czb_dataset_keys)
        for ud in self.user_datasets:
            keys.append(_user_dataset_key(Path(ud.path)))
        return keys

    @property
    def dataset_key(self) -> str:
        """
        Get the dataset key for this benchmark run.

        Returns either the czbenchmarks dataset key or a generated key
        for user datasets based on the filename.

        Returns:
            str: Dataset key for caching and identification.

        Note:
            For user datasets, generates a sanitized key from the filename.
            This may cause cache collisions for files with identical names.
        """

        assert self.user_dataset or self.czb_dataset_key
        if self.user_dataset:
            return _user_dataset_key(Path(self.user_dataset.path))
        return self.czb_dataset_key

    @property
    def czb_dataset_key(self) -> Optional[str]:
        """Return the first czb dataset key if available."""
        return self.czb_dataset_keys[0] if self.czb_dataset_keys else None

    @property
    def cell_representation(self) -> Optional[str]:
        """Return the first cell representation if available."""
        return self.cell_representations[0] if self.cell_representations else None

    @property
    def user_dataset(self) -> Optional[UserDatasetSpec]:
        return self.user_datasets[0] if self.user_datasets else None
