import logging
from typing import Any, Dict

from rich.console import Console

from .api import fetch_benchmark_models
from .specs import BenchmarkRunSpec
from .utils import (
    CLIError,
    handle_cli_error,
)

logger = logging.getLogger(__name__)
console = Console()


class ModelRegistry:
    """
    Registry for managing model configurations and validation.

    Provides functionality to fetch model configurations from the API,
    validate benchmark specifications against model capabilities, and
    ensure compatibility between models, datasets, and tasks.
    """

    def __init__(self):
        """Initialize the ModelRegistry."""
        pass

    def get_model_config(self, model_key: str) -> Dict[str, Any]:
        """
        Fetch and return model configuration from the API.

        Retrieves the complete model configuration including adapter image,
        model image, supported datasets, and supported tasks.

        Args:
            model_key (str): The unique identifier for the model.

        Returns:
            Dict[str, Any]: Model configuration containing:
                - adapter_image: Docker image for preprocessing/postprocessing
                - model_image: Docker image for model inference
                - supported_datasets: List of compatible dataset keys
                - supported_tasks: List of compatible task keys

        Raises:
            CLIError: If the model key is invalid or API request fails.
        """
        try:
            model_response = fetch_benchmark_models(model_key)
            model_details = model_response.model.model_dump()

            config = {
                "adapter_image": model_details["adapter_image"],
                "model_image": model_details["model_image"],
                "supported_datasets": model_details["supported_datasets"],
                "supported_tasks": model_details["supported_tasks"],
            }

            return config
        except Exception as e:
            handle_cli_error(
                CLIError(f"Failed to fetch model '{model_key}' from API: {e}")
            )

    def validate(self, spec: BenchmarkRunSpec) -> bool:
        """
        Validate that a benchmark specification is compatible with the model configuration.

        Args:
            spec: The benchmark run specification to validate

        Returns:
            True if the specification is valid

        Raises:
            CLIError: If validation fails for any reason
        """
        try:
            model_config = self.get_model_config(spec.model_key)
        except CLIError:
            handle_cli_error(CLIError(f"Invalid model key: {spec.model_key}"))
            return False

        if not model_config:
            handle_cli_error(CLIError(f"Invalid model key: {spec.model_key}"))
            return False

        supported_datasets = model_config.get("supported_datasets", [])
        supported_tasks = model_config.get("supported_tasks", [])

        if not (
            spec.dataset_key in supported_datasets
            or spec.dataset_key.startswith("user_dataset_")
        ):
            console.print(
                f"[yellow]Warning: Dataset {spec.dataset_key!r} is not listed as supported for model {spec.model_key!r} and may fail. "
                f"Supported datasets: {supported_datasets!r}[/yellow]"
            )

        if spec.task_key not in supported_tasks:
            console.print(
                f"[yellow]Warning: Task {spec.task_key!r} is not listed as supported for model {spec.model_key!r} and may fail. "
                f"Supported tasks: {supported_tasks!r}[/yellow]"
            )

        return True
