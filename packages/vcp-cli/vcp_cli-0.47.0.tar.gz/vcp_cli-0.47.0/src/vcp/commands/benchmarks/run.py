from __future__ import annotations

import json
import logging
import os

import click
from rich.console import Console

from .model_registry import ModelRegistry
from .run_pipeline import CellRepresentationPipeline, FullBenchmarkPipeline
from .specs import BenchmarkRunSpec
from .tasks_cli_handler import add_task_specific_cli_options
from .utils import (
    CLIError,
    DockerRunner,
    handle_cli_error,
    handle_unexpected_error,
    mutually_exclusive,
    validate_benchmark_filters,
)

logger = logging.getLogger(__name__)
console = Console()


def _validate_task_key(ctx, param, value):
    """
    Validate task key using lazy import.

    Args:
        ctx: Click context
        param: Click parameter
        value: Task key value to validate

    Returns:
        str: Validated task key

    Raises:
        click.BadParameter: If task key is invalid
    """
    if value is None:
        return value
    from czbenchmarks.tasks.task import TASK_REGISTRY  # noqa: PLC0415

    available_tasks = list(TASK_REGISTRY.list_tasks())
    if value not in available_tasks:
        raise click.BadParameter(
            f"Invalid task '{value}'. Available tasks: {', '.join(available_tasks)}"
        )
    return value


@click.command(
    name="run",
    context_settings={"help_option_names": ["-h", "--help"]},
    help="""
Run a benchmark task on a model and dataset.

Use a VCP model (--model-key) or a precomputed cell representation (--cell-representation).
Datasets can be VCP datasets (--dataset-key) or user datasets (--user-dataset).
""",
)
@click.option(
    "-b",
    "--benchmark-key",
    callback=mutually_exclusive(
        "model_key", "cell_representation", "user_dataset", "dataset_key"
    ),
    help="Shortcut for specifying model, dataset, and task together. Format: MODEL-DATASET-TASK (e.g., scvi_homo_sapiens-tsv2_blood-cell_type_annotation).",
)
@click.option(
    "-m",
    "--model-key",
    callback=mutually_exclusive("benchmark_key", "cell_representation"),
    # TODO: Could list the valid model keys here (there are a limited number currently)
    help="Model key from the registry (e.g., scvi_homo_sapiens).",
)
@click.option(
    "-d",
    "--dataset-key",
    multiple=True,
    callback=mutually_exclusive("user_dataset"),
    help="Dataset key from czbenchmarks datasets(e.g., tsv2_blood). Can be used multiple times.",
)
@click.option(
    "-u",
    "--user-dataset",
    multiple=True,
    callback=mutually_exclusive("dataset_key"),
    help='Path to a user-provided .h5ad file. Provide as a JSON string with keys: \'dataset_class\', \'organism\', and \'path\'. Example: \'{"dataset_class": "czbenchmarks.datasets.SingleCellLabeledDataset", "organism": "HUMAN", "path": "~/mydata.h5ad"}\'. Can be used multiple times.',
)
@click.option(
    "-t",
    "--task-key",
    callback=_validate_task_key,
    help="Benchmark task to run (choose from available tasks).",
)
@click.option(
    "-c",
    "--cell-representation",
    multiple=True,
    type=str,
    callback=mutually_exclusive("benchmark_key", "model_key"),
    help="Path to precomputed cell embeddings (.npy file) or AnnData reference (e.g., '@X', '@obsm:X_pca'). Can be used multiple times.",
)
@click.option(
    "-l",
    "--baseline-args",
    help="JSON string with parameters for the baseline computation.",
)
@click.option(
    "-r", "--random-seed", type=int, help="Set a random seed for reproducibility."
)
@click.option(
    "-n",
    "--no-cache",
    is_flag=True,
    help="Disable caching. Forces all steps to run from scratch.",
)
# TODO: Consider --debug if this is just showing debug log output (https://czi.atlassian.net/browse/VC-4024)
@click.pass_context
def run_command(ctx: click.Context, **kwargs) -> None:
    """
    Run a benchmark task on a model and dataset.

    You can run a full benchmark (model + dataset + task) or evaluate precomputed cell embeddings.
    Specify either a model and dataset, a benchmark key, or a user dataset file.
    """

    try:
        spec = BenchmarkRunSpec.from_cli_args(kwargs)
        validate_benchmark_filters(spec.model_key, spec.dataset_key, spec.task_key)

        if spec.cell_representations:
            pipeline = CellRepresentationPipeline()
            results = pipeline.run(
                spec,
                use_cache=not kwargs.get("no_cache", False),
                random_seed=kwargs.get("random_seed"),
            )
        else:
            registry = ModelRegistry()

            if not registry.validate(spec):
                return

            # For faster testing on local mac
            use_gpu = os.environ.get("USE_GPU", "true") in ("1", "true", "yes", "on")
            logger.debug(f"Using GPU: {use_gpu}")

            docker = DockerRunner(
                use_gpu=use_gpu  # benchmarks absolutely need a GPU for inference
            )
            pipeline = FullBenchmarkPipeline(registry, docker)
            results = pipeline.run(
                spec,
                use_cache=not kwargs.get("no_cache", False),
                random_seed=kwargs.get("random_seed"),
            )
        console.print("\n[green]Benchmark completed successfully![/green]")
        console.print("\n[bold]Results:[/bold]")
        console.print(json.dumps(results, indent=2, default=str))
    except click.UsageError:
        raise
    except CLIError as e:
        handle_cli_error(e)
    except Exception as e:
        handle_unexpected_error(e, "vcp benchmarks run")


add_task_specific_cli_options(run_command)
