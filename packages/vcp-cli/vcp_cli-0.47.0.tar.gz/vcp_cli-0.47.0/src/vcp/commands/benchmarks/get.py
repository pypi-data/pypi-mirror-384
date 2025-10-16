import fnmatch
import json
import logging
from typing import Any, Dict, List, Optional

import click
from rich.console import Console

from .api import BenchmarkMetric, BenchmarkRecord
from .utils import (
    CACHE_PATH,
    CLIError,
    handle_cli_error,
    handle_unexpected_error,
)

logger = logging.getLogger(__name__)
console = Console()


def convert_cached_results_to_api_format(
    model_metrics: list, model: str, dataset: str, task: str
) -> List[BenchmarkRecord]:
    """
    Convert cached benchmark results from local JSON format to API BenchmarkRecord objects.

    Processes both model_metrics and baseline_metrics sections from cached data,
    creating separate BenchmarkRecord objects for each. Handles conversion failures
    gracefully by logging warnings and continuing with valid data.

    Args:
        cached_data: Dictionary containing cached benchmark data with 'model_metrics'
                    and/or 'baseline_metrics' lists, plus optional 'czbenchmarks_version'
                    and 'timestamp' fields
        model: Model identifier extracted from the cache file path
        dataset: Dataset identifier extracted from the cache file path
        task: Task identifier extracted from the cache file path

    Returns:
        List of BenchmarkRecord objects, potentially containing both model and baseline
        results. Returns empty list if conversion fails or no valid metrics found.
    """
    benchmark_records = []

    try:
        if model_metrics:
            api_metrics = []
            for metric_data in model_metrics:
                api_metric = convert_cached_metric_to_api_format(metric_data)
                if api_metric:
                    api_metrics.append(api_metric)

            if api_metrics:
                model_record = BenchmarkRecord(
                    benchmark_key="",
                    model_key=model,
                    model_name_display=f"{model}",
                    dataset_keys=[dataset],
                    dataset_names_display=[dataset],
                    task_key=task,
                    task_name_display=task,
                    metrics=api_metrics,
                    czbenchmarks_version=None,
                    timestamp=None,
                )
                benchmark_records.append(model_record)

        # FIXME: Cache structure does not differentiate between model and baseline metrics currently
        # baseline_metrics = cached_data.get("baseline_metrics", [])
        # if baseline_metrics:
        #     api_metrics = []
        #     for metric_data in baseline_metrics:
        #         api_metric = convert_cached_metric_to_api_format(metric_data)
        #         if api_metric:
        #             api_metrics.append(api_metric)

        #     if api_metrics:
        #         baseline_record = BenchmarkRecord(
        #             benchmark_key="",
        #             model_key="baseline",
        #             model_name_display="baseline (cached)",
        #             dataset_keys=[dataset],
        #             dataset_names_display=[dataset],
        #             task_key=task,
        #             task_name_display=task,
        #             metrics=api_metrics,
        #             czbenchmarks_version=cached_data.get("czbenchmarks_version"),
        #             timestamp=cached_data.get("timestamp"),
        #         )
        #         benchmark_records.append(baseline_record)

        return benchmark_records

    except Exception as e:
        console.print(
            f"[dim yellow]Warning: Failed to convert cached data for {model}/{dataset}/{task}: {e}[/dim yellow]"
        )
        return []


def convert_cached_metric_to_api_format(
    metric_data: Dict[str, Any],
) -> Optional[BenchmarkMetric]:
    """
    Convert a single cached metric dictionary to API BenchmarkMetric format.

    Handles legacy 'MetricType.' prefixed metric types by stripping the prefix.
    Creates a standardized BenchmarkMetric with single-value statistics and
    default values for fields not present in cached format.

    Args:
        metric_data: Dictionary containing 'metric_type', 'value', and optional 'params'
                    fields from cached benchmark results

    Returns:
        BenchmarkMetric object with normalized metric_key, converted value, and
        single-value statistics. Returns None if conversion fails due to missing
        or invalid data.
    """
    try:
        metric_type = metric_data.get("metric_type", "")
        if metric_type.startswith("MetricType."):
            metric_key = metric_type.replace("MetricType.", "").lower()
        else:
            metric_key = str(metric_type).lower()

        metric_value = float(metric_data.get("value", 0.0))
        params = metric_data.get("params", {})

        api_metric = BenchmarkMetric(
            params=params,
            n_values=1,
            value=metric_value,
            value_std_dev=0.0,
            values_raw=[metric_value],
            batch_random_seeds=None,
            metric_key=metric_key,
        )

        return api_metric

    except Exception as e:
        console.print(
            f"[dim yellow]Warning: Failed to convert metric {metric_data}: {e}[/dim yellow]"
        )
        return None


def load_cached_benchmark_results(
    model_filter: Optional[str] = None,
    dataset_filter: Optional[str] = None,
    task_filter: Optional[str] = None,
) -> List[BenchmarkRecord]:
    """
    Load and filter cached benchmark results from local filesystem cache.

    Scans the cache directory structure for results.json files and applies
    case-insensitive substring filtering using fnmatch patterns. Handles
    malformed JSON files and invalid cache structures gracefully by logging
    warnings and continuing processing.

    Cache structure: ~/.vcp/cache/<model>/<dataset>/task_outputs/<task>/results.json

    Args:
        model_filter: Optional case-insensitive substring pattern to match against
                     model names. Uses fnmatch for pattern matching
        dataset_filter: Optional case-insensitive substring pattern to match against
                       dataset names. Uses fnmatch for pattern matching
        task_filter: Optional case-insensitive substring pattern to match against
                    task names. Uses fnmatch for pattern matching

    Returns:
        List of BenchmarkRecord objects matching all specified filters. Includes
        both model and baseline results from each matching cache file. Returns
        empty list if cache directory doesn't exist or no matches found.
    """
    cached_benchmarks = []

    if not CACHE_PATH.exists():
        return cached_benchmarks

    for results_file in CACHE_PATH.glob("*/*/task_outputs/*/results.json"):
        try:
            parts = results_file.parts
            model = parts[-5]
            dataset = parts[-4]
            task = parts[-2]

            if model_filter and not fnmatch.fnmatch(
                model.lower(), f"*{model_filter.lower()}*"
            ):
                continue
            if dataset_filter and not fnmatch.fnmatch(
                dataset.lower(), f"*{dataset_filter.lower()}*"
            ):
                continue
            if task_filter and not fnmatch.fnmatch(
                task.lower(), f"*{task_filter.lower()}*"
            ):
                continue

            try:
                cached_data = json.loads(results_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                console.print(
                    f"[dim yellow]Warning: Skipping malformed file {results_file}: {e}[/dim yellow]"
                )
                continue

            benchmark_records = convert_cached_results_to_api_format(
                cached_data, model, dataset, task
            )
            cached_benchmarks.extend(benchmark_records)

        except (IndexError, ValueError) as e:
            console.print(
                f"[dim yellow]Warning: Invalid cache path structure {results_file}: {e}[/dim yellow]"
            )
            continue

    return cached_benchmarks


@click.command(name="get", context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-b",
    "--benchmark-key",
    help="Filter by benchmark key (substring match with '*' wildcards, e.g. 'scvi*v1-tsv2*liver-label*pred')",
)
@click.option(
    "-m",
    "--model-filter",
    help="Filter by model key (substring match with '*' wildcards, e.g. 'scvi*v1')",
)
@click.option(
    "-d",
    "--dataset-filter",
    help="Filter by dataset key (substring match with '*' wildcards, e.g 'tsv2*liver')",
)
@click.option(
    "-t",
    "--task-filter",
    help="Filter by task key (substring match with '*' wildcards, e.g. 'label*pred')",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def get_command(
    ctx: click.Context,
    benchmark_key: Optional[str],
    model_filter: Optional[str],
    dataset_filter: Optional[str],
    task_filter: Optional[str],
    format: str,
) -> None:
    """
    Fetch and display benchmark results from the API.

    Use filters to select by model, dataset, or task. Choose to show model, baseline, or both metrics.
    """

    try:
        from .utils import validate_benchmark_filters  # noqa: PLC0415

        validate_benchmark_filters(model_filter, dataset_filter, task_filter)

        if benchmark_key and (model_filter or dataset_filter or task_filter):
            handle_cli_error(
                CLIError(
                    "Cannot use both --benchmark-key and filter options (--model-filter, --dataset-filter, --task-filter) at the same time. "
                    "Use either --benchmark-key for a specific benchmark or filter options to search."
                )
            )

        if benchmark_key:
            from .api import fetch_benchmarks_by_key  # noqa: PLC0415

            benchmark_record = fetch_benchmarks_by_key(benchmark_key)
            api_benchmarks = [benchmark_record]
        else:
            from .api import fetch_benchmarks_list  # noqa: PLC0415

            api_benchmarks = fetch_benchmarks_list(
                model_filter=model_filter,
                dataset_filter=dataset_filter,
                task_filter=task_filter,
            )

        cached_benchmarks = load_cached_benchmark_results(
            model_filter=model_filter,
            dataset_filter=dataset_filter,
            task_filter=task_filter,
        )

        all_benchmarks = api_benchmarks + cached_benchmarks

        # Always output valid JSON or table (even if empty)
        if not all_benchmarks:
            if format == "json":
                console.print("[]", markup=False)
            else:
                console.print("No benchmarks found matching the specified filters.")
            return

        all_rows = []
        for benchmark in all_benchmarks:
            benchmark_dict = benchmark.model_dump()

            base_row = {
                "benchmark_key": benchmark_dict["benchmark_key"],
                "model_key": benchmark_dict["model_key"],
                "model_name": benchmark_dict["model_name_display"],
                "dataset_keys": ", ".join(benchmark_dict["dataset_keys"]),
                "dataset_names": ", ".join(benchmark_dict["dataset_names_display"]),
                "task_key": benchmark_dict["task_key"],
                "task_name": benchmark_dict["task_name_display"],
            }

            for metric in benchmark_dict.get("metrics", []):
                metric_row = {
                    **base_row,
                    "metric": metric.get("metric_key"),
                    "value": metric.get("value"),
                    "params": metric.get("params", {}),
                }
                all_rows.append(metric_row)

        if format == "json":
            console.print(json.dumps(all_rows, indent=2, default=str))
        else:
            ordered_columns = [
                "benchmark_key",
                "model_key",
                "model_name",
                "dataset_keys",
                "dataset_names",
                "task_key",
                "task_name",
                "metric",
                "value",
            ]
            from .utils import format_as_table  # noqa: PLC0415

            console.print(format_as_table(all_rows, table_type=ordered_columns))

    except CLIError as e:
        handle_cli_error(e)
    except Exception as e:
        handle_unexpected_error(e, "vcp benchmarks get")
