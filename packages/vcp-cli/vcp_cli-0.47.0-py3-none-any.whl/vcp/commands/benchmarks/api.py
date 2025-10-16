from typing import List, Optional

from pydantic import BaseModel

from vcp.utils import http

from .utils import (
    CLIError,
    get_config,
    handle_cli_error,
    validate_benchmark_filters,
)


class BenchmarkFilters(BaseModel):
    """
    Filter criteria for querying benchmarks.

    Use this model to specify optional filters when searching for benchmarks.
    All filters are optional and can be combined to narrow down results.

    Attributes:
        model_filter: Filter benchmarks by model key (e.g., 'scvi-model')
        dataset_filter: Filter benchmarks by dataset key (e.g., 'pbmc-3k')
        task_filter: Filter benchmarks by task type (e.g., 'batch_integration')
    """

    model_config = {"protected_namespaces": ()}

    model_filter: str | None = None
    dataset_filter: str | None = None
    task_filter: str | None = None


class BenchmarkMetric(BaseModel):
    """
    Performance metric from a benchmark run.

    Represents a single evaluation metric (e.g., accuracy, silhouette score)
    with statistical information including mean, standard deviation, and raw values
    from multiple benchmark runs.

    Attributes:
        params: Additional parameters used for this metric calculation
        n_values: Number of values used to compute the statistics
        value: Mean value of the metric across all runs
        value_std_dev: Standard deviation of the metric values
        values_raw: List of individual metric values from each run
        batch_random_seeds: Random seeds used for each batch run (if applicable)
        metric_key: Identifier for the metric type (e.g., 'silhouette_score')
    """

    params: dict = {}
    n_values: int
    value: float
    value_std_dev: float
    values_raw: list[float]
    batch_random_seeds: list[str] | None = None
    metric_key: str


class BenchmarkRecord(BaseModel):
    """
    Complete benchmark result record.

    Represents the results of running a specific model on specific datasets
    for a particular task, including all performance metrics and metadata.

    Attributes:
        benchmark_key: Unique identifier for this benchmark run
        model_key: Key identifying the model that was benchmarked
        model_name_display: Human-readable name of the model
        dataset_keys: List of dataset keys used in this benchmark
        dataset_names_display: Human-readable names of the datasets
        task_key: Key identifying the type of task performed
        task_name_display: Human-readable name of the task
        metrics: List of performance metrics from this benchmark
        czbenchmarks_version: Version of the benchmarking framework used
        timestamp: When this benchmark was run (ISO format)
    """

    model_config = {"protected_namespaces": ()}

    benchmark_key: str
    model_key: str
    model_name_display: str
    dataset_keys: list[str]
    dataset_names_display: list[str]
    task_key: str
    task_name_display: str
    metrics: list[BenchmarkMetric]
    czbenchmarks_version: str | None = None
    timestamp: str | None = None


class BenchmarksResponse(BaseModel):
    """
    API response for benchmark list queries.

    Container for the results of a GET /benchmarks API call, including
    the matching benchmark records, total count, and applied filters.

    Attributes:
        benchmarks: List of benchmark records matching the query
        total_count: Total number of benchmarks available (before pagination)
        filters: The filter criteria that were applied to this query
    """

    benchmarks: list[BenchmarkRecord]
    total_count: int
    filters: BenchmarkFilters


class BenchmarkModelDetails(BaseModel):
    """
    Benchmark model configuration and capabilities.

    Detailed information about a model's supported datasets, tasks,
    and the Docker images required to run benchmarks with this model.

    Attributes:
        supported_datasets: List of dataset keys this model can work with
        supported_tasks: List of task types this model can perform
        adapter_image: Docker image for the model adapter/wrapper
        model_image: Docker image containing the actual model
    """

    model_config = {"protected_namespaces": ()}

    supported_datasets: list[str]
    supported_tasks: list[str]
    adapter_image: str
    model_image: str


class BenchmarkModelResponse(BaseModel):
    """
    API response for model details queries.

    Container for the results of a GET /benchmarks/models/{model_key} API call,
    providing detailed configuration information about a specific model.

    Attributes:
        model_key: The key identifying this model
        model: Detailed configuration and capabilities of the model
    """

    model_config = {"protected_namespaces": ()}

    model_key: str
    model: BenchmarkModelDetails


def fetch_benchmarks_list(
    model_filter: Optional[str] = None,
    dataset_filter: Optional[str] = None,
    task_filter: Optional[str] = None,
) -> List[BenchmarkRecord]:
    """
    Retrieve benchmark results with optional filtering.

    Fetches a list of benchmark records from the API, optionally filtered by
    model, dataset, or task. Use filters to narrow down results to specific
    combinations of interest.

    Args:
        model_filter: Filter by model key (e.g., 'scvi-model'). If None,
            includes all models.
        dataset_filter: Filter by dataset key (e.g., 'pbmc-3k'). If None,
            includes all datasets.
        task_filter: Filter by task type (e.g., 'batch_integration'). If None,
            includes all task types.

    Returns:
        A list of BenchmarkRecord objects matching the specified filters.
        Returns empty list if no benchmarks match the criteria.
    """

    validate_benchmark_filters(model_filter, dataset_filter, task_filter)

    config = get_config()
    endpoint_url = f"{config.benchmarks_api.base_url}{config.benchmarks_api.endpoints.list_benchmarks}"

    response_data = http.get_json(
        endpoint_url,
        params={
            "model_filter": model_filter,
            "dataset_filter": dataset_filter,
            "task_filter": task_filter,
        },
    )
    benchmarks_response = BenchmarksResponse.model_validate(response_data)
    return benchmarks_response.benchmarks


def fetch_benchmarks_by_key(benchmark_key: str) -> BenchmarkRecord:
    """
    Retrieve a specific benchmark by its unique key.

    Fetches detailed information about a single benchmark run, including
    all metrics and metadata.

    Args:
        benchmark_key: The unique identifier for the benchmark. Must be a
            non-empty string no longer than 50 characters.

    Returns:
        A BenchmarkRecord object containing the complete benchmark results.

    Raises:
        CLIError: If the benchmark_key is None, empty, or longer than 50 characters.
    """

    if not benchmark_key or len(benchmark_key) > 50:
        handle_cli_error(CLIError("Invalid benchmark key"))
        return

    config = get_config()
    endpoint_url = f"{config.benchmarks_api.base_url}{config.benchmarks_api.endpoints.get_benchmarks_by_key.format(benchmark_key=benchmark_key)}"

    response_data = http.get_json(endpoint_url)
    return BenchmarkRecord.model_validate(response_data)


def fetch_benchmark_models(model_key: str) -> BenchmarkModelResponse:
    """
    Retrieve detailed configuration for a specific model.

    Fetches comprehensive information about a model including supported
    datasets, tasks, and Docker images required for benchmarking.

    Args:
        model_key: The unique identifier for the model. Must be a non-empty
            string no longer than 50 characters.

    Returns:
        A BenchmarkModelResponse object containing the model's configuration,
        capabilities, and Docker image information.

    Raises:
        CLIError: If the model_key is None, empty, or longer than 50 characters.
    """

    if not model_key or len(model_key) > 50:
        handle_cli_error(CLIError("Invalid model key"))
        return

    config = get_config()
    endpoint_url = f"{config.benchmarks_api.base_url}{config.benchmarks_api.endpoints.get_benchmark_models.format(model_key=model_key)}"

    response_data = http.get_json(endpoint_url)
    return BenchmarkModelResponse.model_validate(response_data)
