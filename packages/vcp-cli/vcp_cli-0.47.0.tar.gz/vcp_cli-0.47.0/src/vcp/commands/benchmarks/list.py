import json
import logging
from typing import Optional

import click
from rich.console import Console

from .api import fetch_benchmarks_by_key, fetch_benchmarks_list
from .utils import (
    CLIError,
    format_as_table,
    handle_cli_error,
    handle_unexpected_error,
    validate_benchmark_filters,
)

logger = logging.getLogger(__name__)
console = Console()


@click.command(name="list", context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-b",
    "--benchmark-key",
    help="Filter by benchmark key",
)
@click.option(
    "-m",
    "--model-filter",
    help="Filter by model key (substring match with '*' wildcards, e.g. 'scvi*v1').",
)
@click.option(
    "-d",
    "--dataset-filter",
    help="Filter by dataset key (substring match with '*' wildcards, e.g. 'tsv2*liver').",
)
@click.option(
    "-t",
    "--task-filter",
    help="Filter by task key (substring match with '*' wildcards, e.g. 'label*pred').",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
# TODO: Consider --debug if this is just showing debug log output (https://czi.atlassian.net/browse/VC-4024)
@click.pass_context
def list_command(
    ctx: click.Context,
    benchmark_key: Optional[str],
    dataset_filter: Optional[str],
    model_filter: Optional[str],
    task_filter: Optional[str],
    format: str,
) -> None:
    """
    List available model, dataset and task benchmark combinations. You can filter results by dataset, model, or task using glob patterns.
    """

    try:
        validate_benchmark_filters(model_filter, dataset_filter, task_filter)

        if benchmark_key:
            benchmark_record = fetch_benchmarks_by_key(benchmark_key)
            benchmarks = [benchmark_record]
        else:
            benchmarks = fetch_benchmarks_list(
                model_filter=model_filter,
                dataset_filter=dataset_filter,
                task_filter=task_filter,
            )

        if not benchmarks:
            if format == "json":
                console.print("[]", markup=False)
            else:
                console.print("No benchmarks found matching the specified filters.")
            return

        api_rows = []
        for benchmark in benchmarks:
            benchmark_dict = benchmark.model_dump()
            api_rows.append({
                "benchmark_key": benchmark_dict["benchmark_key"],
                "model_key": benchmark_dict["model_key"],
                "model_name": benchmark_dict["model_name_display"],
                "dataset_keys": ", ".join(benchmark_dict["dataset_keys"]),
                "dataset_names": ", ".join(benchmark_dict["dataset_names_display"]),
                "task_key": benchmark_dict["task_key"],
                "task_name": benchmark_dict["task_name_display"],
            })

        if format == "json":
            console.print(json.dumps(api_rows, indent=2))
        else:
            console.print(format_as_table(api_rows, "benchmarks"))

    except CLIError as e:
        handle_cli_error(e)
    except Exception as e:
        handle_unexpected_error(e, "vcp benchmarks list")
