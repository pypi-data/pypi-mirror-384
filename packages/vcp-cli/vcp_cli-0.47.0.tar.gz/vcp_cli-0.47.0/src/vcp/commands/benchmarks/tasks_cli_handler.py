import logging
from typing import Any, Dict, List

import click

from .utils import CLIError

logger = logging.getLogger(__name__)


# Common CLI option helpers
def add_common_labels_option(options: List[click.Option]) -> None:
    """Add the common --labels option used by multiple tasks."""
    options.append(
        click.Option(
            ["--labels"],
            type=str,
            default="cell_type",
            help="The .obs column with cell type labels. Supports both column name ('cell_type') and reference ('@obs:cell_type') formats (default: 'cell_type').",
        )
    )


def process_labels_arg(cli_args: Dict[str, Any], default: str = "cell_type") -> str:
    """Process labels argument to handle both direct column names and references."""
    labels_col = cli_args.get("labels", default)
    # If user provided a reference like @obs:cell_type, use as-is
    # If user provided just column name like cell_type, convert to reference
    if labels_col.startswith("@"):
        return labels_col
    else:
        return f"@obs:{labels_col}"


def process_batch_column_arg(cli_args: Dict[str, Any], default: str = "batch") -> str:
    """Process batch column argument to handle both direct column names and references."""
    # Support both --batch-column and --batch-labels for backward compatibility
    batch_col = cli_args.get("batch_column") or cli_args.get("batch_labels", default)
    # Handle reference format
    if batch_col.startswith("@"):
        return batch_col
    else:
        return f"@obs:{batch_col}"


class TaskCliHandler:
    """
    Abstract base class for defining special CLI handling for a task.
    """

    @staticmethod
    def add_cli_options(options: List[click.Option]) -> None:
        """Adds task-specific click.Option objects to the provided list."""
        raise NotImplementedError

    @staticmethod
    def process_and_validate(
        cli_args: Dict[str, Any], datasets: List[Any]
    ) -> Dict[str, Any]:
        """Processes CLI arguments into a dictionary of task inputs."""
        raise NotImplementedError


class EmbeddingTaskHandler(TaskCliHandler):
    """Handler for the 'embedding' task."""

    @staticmethod
    def add_cli_options(options: List[click.Option]) -> None:
        """Adds embedding task options."""
        add_common_labels_option(options)

    @staticmethod
    def process_and_validate(
        cli_args: Dict[str, Any], datasets: List[Any]
    ) -> Dict[str, Any]:
        """Processes CLI args into embedding task inputs."""
        return {
            "input_labels": process_labels_arg(cli_args),
        }


class ClusteringTaskHandler(TaskCliHandler):
    """Handler for the 'clustering' task."""

    @staticmethod
    def add_cli_options(options: List[click.Option]) -> None:
        """Adds clustering task options."""
        add_common_labels_option(options)
        options.append(
            click.Option(
                ["--use-rep"],
                type=str,
                default="X",
                help="[Clustering Task] Representation to use for clustering (default: 'X').",
            )
        )
        options.append(
            click.Option(
                ["--n-iterations"],
                type=int,
                default=2,
                help="[Clustering Task] Number of Leiden algorithm iterations (default: 2).",
            )
        )
        options.append(
            click.Option(
                ["--flavor"],
                type=click.Choice(["leidenalg", "igraph"]),
                default="igraph",
                help="[Clustering Task] Flavor of Leiden algorithm (default: 'igraph').",
            )
        )
        options.append(
            click.Option(
                ["--key-added"],
                type=str,
                default="leiden",
                help="[Clustering Task] Key for storing cluster assignments (default: 'leiden').",
            )
        )

    @staticmethod
    def process_and_validate(
        cli_args: Dict[str, Any], datasets: List[Any]
    ) -> Dict[str, Any]:
        """Processes CLI args into clustering task inputs."""
        use_rep = cli_args.get("use_rep", "X")
        n_iterations = cli_args.get("n_iterations", 2)
        flavor = cli_args.get("flavor", "igraph")
        key_added = cli_args.get("key_added", "leiden")

        return {
            "obs": "@obs",
            "input_labels": process_labels_arg(cli_args),
            "use_rep": use_rep,
            "n_iterations": n_iterations,
            "flavor": flavor,
            "key_added": key_added,
        }


class LabelPredictionTaskHandler(TaskCliHandler):
    """Handler for the 'label_prediction' task."""

    @staticmethod
    def add_cli_options(options: List[click.Option]) -> None:
        """Adds label prediction task options."""
        add_common_labels_option(options)
        options.append(
            click.Option(
                ["--n-folds"],
                type=int,
                default=5,
                help="[Label Prediction Task] Number of cross-validation folds (default: 5).",
            )
        )
        options.append(
            click.Option(
                ["--min-class-size"],
                type=int,
                default=10,
                help="[Label Prediction Task] Minimum samples per class for inclusion (default: 10).",
            )
        )

    @staticmethod
    def process_and_validate(
        cli_args: Dict[str, Any], datasets: List[Any]
    ) -> Dict[str, Any]:
        """Processes CLI args into label prediction task inputs."""
        n_folds = cli_args.get("n_folds", 5)
        min_class_size = cli_args.get("min_class_size", 10)

        return {
            "labels": process_labels_arg(cli_args),
            "n_folds": n_folds,
            "min_class_size": min_class_size,
        }


class BatchIntegrationTaskHandler(TaskCliHandler):
    """Handler for the 'batch_integration' task."""

    @staticmethod
    def add_cli_options(options: List[click.Option]) -> None:
        """Adds batch integration task options."""
        options.append(
            click.Option(
                ["--batch-column", "--batch-labels"],
                type=str,
                default="batch",
                help="[Batch Integration Task] The .obs column with batch information (default: 'batch').",
            )
        )

        add_common_labels_option(options)

    @staticmethod
    def process_and_validate(
        cli_args: Dict[str, Any], datasets: List[Any]
    ) -> Dict[str, Any]:
        """Processes CLI args into batch integration task inputs."""
        return {
            "batch_labels": process_batch_column_arg(cli_args),
            "labels": process_labels_arg(cli_args),
        }


class CrossSpeciesIntegrationHandler(TaskCliHandler):
    """Handler for the 'cross-species_integration' task."""

    @staticmethod
    def add_cli_options(options: List[click.Option]) -> None:
        options.append(
            click.Option(
                ["--cross-species-organisms"],
                multiple=True,
                help="[Cross-Species] Organism name (e.g., 'homo_sapiens:ENSG'). Repeat for each dataset in order.",
            )
        )
        # Note: Cross-species uses multiple labels (one per dataset), so it can't use the common --labels
        options.append(
            click.Option(
                ["--cross-species-labels"],
                type=str,
                multiple=True,
                help="[Cross-Species] Cell type labels column for each dataset. Supports both column name ('cell_type') and reference ('@obs:cell_type') formats. Repeat for each dataset in order.",
            )
        )

    @staticmethod
    def process_and_validate(
        cli_args: Dict[str, Any], datasets: List[Any]
    ) -> Dict[str, Any]:
        """Processes CLI args into cross-species integration inputs."""
        organisms = cli_args.get("cross_species_organisms", [])
        labels = cli_args.get("cross_species_labels", [])

        if not organisms:
            raise CLIError(
                "For cross-species integration, you must provide --cross-species-organisms"
            )
        # Process each label to handle both direct column names and references
        processed_labels = []
        index = 0
        for label in labels:
            if label.startswith("@"):
                processed_labels.append(label)
            else:
                processed_labels.append(f"@{index}:obs:{label}")
            index += 1

        organism_tuples = []
        index = 0
        for org_str in organisms:
            parts = org_str.split(":", 1)
            # if processed_labels at index is null, default to @index:obs:cell_type
            if index >= len(processed_labels) or processed_labels[index] is None:
                processed_labels.append(f"@{index}:obs:cell_type")
            if len(parts) == 2:
                organism_tuples.append((parts[0], parts[1]))
            else:
                organism_tuples.append((parts[0], ""))
            index += 1

        return {
            "organism_list": organism_tuples,
            "labels": processed_labels,
        }


def add_task_specific_cli_options(cmd):
    """
    Add all CLI options for all specialized tasks to the run command.

    Args:
        cmd: The click.Command object to which options will be added.
    """
    options = []
    option_names = set()

    for handler in TaskCliHandler.__subclasses__():
        handler.add_cli_options(options)

    unique_options = []
    for opt in options:
        opt_names = set(opt.opts)
        if not opt_names.intersection(option_names):
            unique_options.append(opt)
            option_names.update(opt_names)

    for opt in unique_options:
        cmd.params.append(opt)


def process_all_task_inputs(
    task_name: str, cli_args: Dict[str, Any], datasets: list
) -> dict:
    """
    Validate and process task inputs for a specialized task by name.

    Args:
        task_name (str): The name of the task to process inputs for.
        cli_args (Dict[str, Any]): CLI arguments from click.
        datasets (list): List of loaded datasets.

    Returns:
        dict: Processed task input arguments for BenchmarkRunSpec.task_inputs.
    """

    task_handlers = {
        "embedding": EmbeddingTaskHandler,
        "clustering": ClusteringTaskHandler,
        "label_prediction": LabelPredictionTaskHandler,
        "batch_integration": BatchIntegrationTaskHandler,
        "cross-species_integration": CrossSpeciesIntegrationHandler,
    }

    handler_class = task_handlers.get(task_name)
    if handler_class:
        return handler_class.process_and_validate(cli_args, datasets)

    return {}
