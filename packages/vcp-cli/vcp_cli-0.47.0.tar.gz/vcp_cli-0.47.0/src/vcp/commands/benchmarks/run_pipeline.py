from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from .run_task import run_task
from .utils import (
    CLIError,
    get_cache_dir,
    handle_cli_error,
    handle_unexpected_error,
    load_from_cache,
    save_to_cache,
)

if TYPE_CHECKING:
    from czbenchmarks.datasets import Dataset

    from .specs import BenchmarkRunSpec
    from .utils import DockerRunner

logger = logging.getLogger(__name__)


def load_czbenchmarks_dataset(dataset_key: str) -> "Dataset":
    """
    Load a dataset using czbenchmarks and provide user feedback.

    Loads the specified dataset using czbenchmarks, printing progress and summary information to the console.
    Handles common errors gracefully and raises CLIError if loading fails.

    Args:
        dataset_key (str): The dataset key to load.

    Returns:
        Dataset: The loaded dataset object.

    Raises:
        CLIError: If the dataset cannot be loaded or czbenchmarks is unavailable.
    """
    try:
        logger.info(f"Loading dataset '{dataset_key}' with czbenchmarks...")

        from czbenchmarks.datasets.utils import (  # noqa: PLC0415
            load_dataset as czb_load_dataset,  # noqa: PLC0415
        )

        dataset = czb_load_dataset(dataset_key)
        logger.info(
            f"  -> Dataset loaded: {dataset.adata.n_obs} cells, {dataset.adata.n_vars} genes"
        )
        return dataset
    except KeyError:
        handle_cli_error(CLIError(f"Dataset key '{dataset_key}' is not valid."))
    except Exception as e:
        handle_unexpected_error(
            e, "vcp benchmarks run: on loading czbenchmarks dataset"
        )


def load_dataset(spec: "BenchmarkRunSpec"):
    """
    Load a dataset based on the BenchmarkRunSpec, supporting both regular and user datasets.

    Loads either a user-provided dataset (from a local file) or a czbenchmarks dataset,
    depending on the fields set in the spec.

    Args:
        spec (BenchmarkRunSpec): The benchmark specification containing dataset information.

    Returns:
        Dataset: The loaded dataset object.

    Raises:
        CLIError: If neither dataset nor user_dataset is specified, or if loading fails.
    """
    if spec.user_dataset:
        try:
            logger.info(f"Loading user dataset from '{spec.user_dataset.path}'...")
            organism = spec.user_dataset.organism

            if isinstance(organism, str):
                if organism.startswith("Organism."):
                    organism = organism.split(".", 1)[1]
                try:
                    from czbenchmarks.datasets import Organism  # noqa: PLC0415

                    organism = Organism[organism]
                except KeyError as e:
                    raise ValueError(f"Invalid organism: {organism}") from e

            from czbenchmarks.datasets.utils import (  # noqa: PLC0415
                load_local_dataset as czb_load_local_dataset,
            )

            dataset = czb_load_local_dataset(
                dataset_class=spec.user_dataset.dataset_class,
                organism=organism,
                path=Path(spec.user_dataset.path),
            )
            logger.info(
                f"  -> User dataset loaded: {dataset.adata.n_obs} cells, {dataset.adata.n_vars} genes"
            )
            return dataset
        except KeyError as e:
            missing_key = str(e).strip("'")
            handle_cli_error(
                CLIError(
                    f"Missing required key '{missing_key}' in user dataset specification. "
                    f"Required keys: dataset_class, organism, path"
                )
            )
        except Exception as e:
            handle_unexpected_error(e, "vcp benchmarks run: on loading user dataset")
    elif spec.czb_dataset_key:
        return load_czbenchmarks_dataset(spec.czb_dataset_key)
    else:
        handle_cli_error(
            CLIError("Either --dataset or --user-dataset must be specified.")
        )


def load_datasets(spec: "BenchmarkRunSpec") -> list["Dataset"]:
    """
    Load multiple datasets based on the BenchmarkRunSpec.

    Loads either user-provided datasets (from local files) or czbenchmarks datasets,
    based on the fields set in the spec.

    Args:
        spec (BenchmarkRunSpec): The benchmark specification containing dataset information.

    Returns:
        list[Dataset]: The loaded dataset objects.

    Raises:
        CLIError: If no datasets are specified or if loading fails.
    """
    datasets = []

    for dataset_key in spec.czb_dataset_keys:
        datasets.append(load_czbenchmarks_dataset(dataset_key))

    for user_dataset_spec in spec.user_datasets:
        try:
            logger.info(f"Loading user dataset from '{user_dataset_spec.path}'...")
            organism = user_dataset_spec.organism

            if isinstance(organism, str):
                if organism.startswith("Organism."):
                    organism = organism.split(".", 1)[1]
                try:
                    from czbenchmarks.datasets import Organism  # noqa: PLC0415

                    organism = Organism[organism]
                except KeyError as e:
                    raise ValueError(f"Invalid organism: {organism}") from e

            from czbenchmarks.datasets.utils import (  # noqa: PLC0415
                load_local_dataset as czb_load_local_dataset,
            )

            dataset = czb_load_local_dataset(
                dataset_class=user_dataset_spec.dataset_class,
                organism=organism,
                path=Path(user_dataset_spec.path),
            )
            logger.info(
                f"  -> User dataset loaded: {dataset.adata.n_obs} cells, {dataset.adata.n_vars} genes"
            )
            datasets.append(dataset)
        except KeyError as e:
            missing_key = str(e).strip("'")
            handle_cli_error(
                CLIError(
                    f"Missing required key '{missing_key}' in user dataset specification. "
                    f"Required keys: dataset_class, organism, path"
                )
            )
        except Exception as e:
            handle_unexpected_error(e, "vcp benchmarks run: on loading user dataset")

    if not datasets:
        handle_cli_error(
            CLIError("Either --dataset-key or --user-dataset must be specified.")
        )

    return datasets


class CellRepresentationPipeline:
    """
    Pipeline for running benchmarks using precomputed cell representations.

    Loads precomputed cell representations, runs the specified benchmarking task, and optionally includes baseline metrics.
    Results are saved to cache unless caching is disabled.
    """

    def run(
        self,
        spec: "BenchmarkRunSpec",
        use_cache: bool,
        random_seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute the benchmarking pipeline using precomputed cell representations.

        Loads the dataset(s) and cell embeddings, runs the benchmarking task, and saves results
        to cache if caching is enabled.

        Args:
            spec (BenchmarkRunSpec): The benchmark specification.
            use_cache (bool): If True, uses cached of results.
            random_seed (Optional[int]): Random seed for reproducibility.

        Returns:
            Dict[str, Any]: The benchmarking results.
        """

        logger.info(
            f"Starting Cell Representation Run: {spec.dataset_keys}/{spec.task_key}"
        )

        if len(spec.czb_dataset_keys) + len(spec.user_datasets) == 1:
            dataset_obj = load_dataset(spec)
            datasets = [dataset_obj]
        else:
            datasets = load_datasets(spec)

        if not spec.cell_representations:
            handle_cli_error(CLIError("No cell representation specified."))

        embeddings = []
        for cr_path in spec.cell_representations:
            if isinstance(cr_path, str) and cr_path.startswith("@"):
                embeddings.append(cr_path)
            else:
                from numpy import load  # noqa: PLC0415

                embeddings.append(load(Path(cr_path)))

        if len(datasets) == 1 and len(embeddings) == 1:
            task_params = spec.task_inputs or {}

            results = run_task(
                spec.task_key,
                adata_input=datasets[0],
                cell_representation_input=embeddings[0],
                run_baseline=spec.run_baseline,
                baseline_params=spec.baseline_args,
                task_params=task_params,
                random_seed=random_seed,
            )
        else:
            task_params = spec.task_inputs or {}

            results = run_task(
                spec.task_key,
                adata_input=datasets,
                cell_representation_input=embeddings,
                run_baseline=spec.run_baseline,
                baseline_params=spec.baseline_args,
                task_params=task_params,
                random_seed=random_seed,
            )

        if use_cache:
            if spec.model_key:
                model_key = spec.model_key
            else:
                first_cr = spec.cell_representations[0]
                if isinstance(first_cr, str) and first_cr.startswith("@"):
                    model_key = "anndata_ref"
                else:
                    model_key = Path(first_cr).stem
            save_to_cache(
                model_key, spec.dataset_key, spec.task_key, results, "results"
            )

        return results


class FullBenchmarkPipeline:
    """
    Pipeline for running a full benchmark, including model inference and evaluation.

    Handles the complete process: loading the dataset, running the model pipeline
    (preprocessing, inference, postprocessing), generating embeddings, and running the benchmarking
    task. Results and embeddings are cached unless caching is disabled.
    """

    def __init__(self, registry, docker: "DockerRunner"):
        """
        Initialize the FullBenchmarkPipeline.

        Args:
            registry (ModelRegistry): The model registry for configuration and validation.
            docker (DockerRunner): The Docker runner for executing containerized steps.
        """
        self.registry = registry
        self.docker = docker

    def run(
        self,
        spec: "BenchmarkRunSpec",
        use_cache: bool,
        random_seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full benchmarking pipeline from scratch.

        Loads the dataset, runs the model pipeline to generate embeddings, and executes the
        benchmarking task. Utilizes cached results and embeddings if available and caching is enabled.

        Args:
            spec (BenchmarkRunSpec): The benchmark specification.
            use_cache (bool): If True, uses cached results and embeddings.
            random_seed (Optional[int]): Random seed for reproducibility.

        Returns:
            Dict[str, Any]: The benchmarking results.

        Raises:
            CLIError: If required files are missing or pipeline steps fail.
        """

        logger.info(f"Starting Full Benchmark: {spec.key}")

        if use_cache:
            try:
                results = load_from_cache(
                    spec.model_key, spec.dataset_key, spec.task_key, "results"
                )
                logger.info("Reusing cached task results.")
                return results
            except FileNotFoundError:
                pass

        if len(spec.czb_dataset_keys) + len(spec.user_datasets) == 1:
            dataset_obj = load_dataset(spec)
            datasets = [dataset_obj]
        else:
            datasets = load_datasets(spec)

        all_embeddings = []
        for i, _dataset in enumerate(datasets):
            if i < len(spec.czb_dataset_keys):
                temp_spec_data = {
                    "model_key": spec.model_key,
                    "czb_dataset_keys": [spec.czb_dataset_keys[i]],
                    "task_key": spec.task_key,
                    "run_baseline": spec.run_baseline,
                    "baseline_args": spec.baseline_args,
                    "task_inputs": spec.task_inputs,
                }
            else:
                temp_spec_data = {
                    "model_key": spec.model_key,
                    "user_datasets": [
                        spec.user_datasets[i - len(spec.czb_dataset_keys)]
                    ],
                    "task_key": spec.task_key,
                    "run_baseline": spec.run_baseline,
                    "baseline_args": spec.baseline_args,
                    "task_inputs": spec.task_inputs,
                }

            from .specs import BenchmarkRunSpec  # noqa: PLC0415

            temp_spec = BenchmarkRunSpec(**temp_spec_data)

            embeddings = None
            if use_cache:
                try:
                    embeddings = load_from_cache(
                        spec.model_key, temp_spec.dataset_key, None, "embeddings"
                    )
                    logger.info(
                        f"Reusing cached embeddings for dataset {temp_spec.dataset_key}."
                    )
                except FileNotFoundError:
                    pass

            if embeddings is None:
                self._run_model_pipeline(temp_spec)

                embeddings_path = (
                    get_cache_dir(spec.model_key, temp_spec.dataset_key, None)
                    / "task_input"
                    / "embeddings.npy"
                )
                if embeddings_path.exists():
                    from numpy import load  # noqa: PLC0415

                    embeddings = load(embeddings_path)
                    if use_cache:
                        save_to_cache(
                            spec.model_key,
                            temp_spec.dataset_key,
                            None,
                            embeddings,
                            "embeddings",
                        )
                else:
                    raise CLIError(
                        f"Embeddings file not found at {embeddings_path}. Pipeline may have failed."
                    )

            all_embeddings.append(embeddings)

        if len(datasets) == 1:
            task_params = spec.task_inputs or {}

            results = run_task(
                spec.task_key,
                adata_input=datasets[0],
                cell_representation_input=all_embeddings[0],
                run_baseline=spec.run_baseline,
                baseline_params=spec.baseline_args,
                task_params=task_params,
                random_seed=random_seed,
            )
        else:
            task_params = spec.task_inputs or {}

            results = run_task(
                spec.task_key,
                adata_input=datasets,
                cell_representation_input=all_embeddings,
                run_baseline=spec.run_baseline,
                baseline_params=spec.baseline_args,
                task_params=task_params,
                random_seed=random_seed,
            )

        save_to_cache(
            spec.model_key, spec.dataset_key, spec.task_key, results, "results"
        )
        return results

    def _run_model_pipeline(self, spec: "BenchmarkRunSpec") -> None:
        """
        Run the model pipeline to generate cell embeddings.

        Executes the preprocessing, inference, and postprocessing steps using Docker containers
        as specified in the model registry. Ensures that the final embeddings file is created.

        Args:
            spec (BenchmarkRunSpec): The benchmark specification.

        Raises:
            CLIError: If any pipeline step fails or required files are missing.
        """

        config = self.registry.get_model_config(spec.model_key)

        run_cache_dir = get_cache_dir(spec.model_key, spec.dataset_key, None)
        model_input_json_path = run_cache_dir / "model_input" / "input.json"
        final_embeddings_path = run_cache_dir / "task_input" / "embeddings.npy"

        self._run_preprocess(spec, config, run_cache_dir)
        self._run_inference(config, run_cache_dir, model_input_json_path)
        self._run_postprocess(config, run_cache_dir)

        if not final_embeddings_path.exists():
            raise CLIError(
                f"Postprocessing failed: Expected embeddings file {final_embeddings_path} was not created. "
                f"Check adapter configuration and Docker logs."
            )

    def _run_preprocess(
        self, spec: "BenchmarkRunSpec", config: Dict, run_cache_dir: Path
    ):
        """
        Run the preprocessing step of the model pipeline.

        Executes the model adapter's preprocessing Docker container, preparing input data
        for model inference.

        Args:
            spec (BenchmarkRunSpec): The benchmark specification.
            config (Dict): Model configuration from the registry.
            run_cache_dir (Path): Directory for caching pipeline files.

        Raises:
            CLIError: If preprocessing fails.
        """
        logger.info("1. Running Preprocessing Step...")

        model_input_dir = run_cache_dir / "model_input"
        model_input_dir.mkdir(exist_ok=True)

        if spec.user_dataset:
            dataset_file_path = spec.user_dataset.path.expanduser().resolve()
            # copy the user dataset file into the model_input directory
            shutil.copy(dataset_file_path, model_input_dir)

            container_dataset_path = f"/model_input/{dataset_file_path.name}"
            user_dataset_spec = spec.user_dataset.model_copy(deep=True)
            user_dataset_spec.path = container_dataset_path
            user_dataset_spec_json = user_dataset_spec.model_dump_json()

            logger.info(
                f"Running preprocessing with user dataset: {user_dataset_spec_json}"
            )
            logger.debug(
                f"Executing Docker command: adapter_image={config['adapter_image']}, "
                f"mounts=[{str(model_input_dir)}, '/model_input', 'rw'], "
                f"cmd_args=['preprocess', '--dataset-spec', {user_dataset_spec_json}], "
                "description='Preprocessing'"
            )
            try:
                self.docker.run(
                    image=config["adapter_image"],
                    mounts=[(str(model_input_dir), "/model_input", "rw")],
                    cmd_args=[
                        "preprocess",
                        "--dataset-spec",
                        str(user_dataset_spec_json),
                    ],
                    description="Preprocessing",
                )
            except Exception as e:
                handle_cli_error(
                    CLIError(
                        f"Docker execution failed during preprocessing with user dataset: {e}"
                    )
                )
        else:
            dataset_name = spec.dataset_key
            logger.info(f"Running preprocessing with dataset: {dataset_name}")
            logger.debug(
                f"Executing Docker command: adapter_image={config['adapter_image']}, "
                f"mounts=[{str(model_input_dir)}, '/model_input', 'rw'], "
                f"cmd_args=['preprocess', '--dataset-name', {dataset_name}], "
                f"description='Preprocessing'"
            )
            try:
                self.docker.run(
                    image=config["adapter_image"],
                    mounts=[(str(model_input_dir), "/model_input", "rw")],
                    cmd_args=["preprocess", "--dataset-name", dataset_name],
                    description="Preprocessing",
                )
            except Exception as e:
                handle_cli_error(
                    CLIError(
                        f"Docker execution failed during preprocessing with dataset '{dataset_name}': {e}"
                    )
                )

    def _run_inference(
        self, config: Dict, run_cache_dir: Path, model_input_json_path: Path
    ):
        """
        Run the model inference step of the pipeline.

        Executes the model's inference Docker container, generating output from preprocessed input.

        Args:
            config (Dict): Model configuration from the registry.
            run_cache_dir (Path): Directory for caching pipeline files.
            model_input_json_path (Path): Path to the model input JSON file.

        Raises:
            CLIError: If inference fails or output file is missing.
        """
        logger.info("2. Running Model Inference Step...")

        model_input_dir = run_cache_dir / "model_input"
        model_output_dir = run_cache_dir / "model_output"
        model_output_dir.mkdir(exist_ok=True)

        input_json_path = model_input_dir / "input.json"
        if input_json_path.exists():
            logger.info("Using input.json created by preprocessing step.")
        else:
            raise CLIError(
                f"input.json not found in {model_input_dir}. Preprocessing may have failed."
            )

        self.docker.run(
            image=config["model_image"],
            mounts=[
                (str(model_input_dir), "/model_input", "ro"),
                (str(model_output_dir), "/model_output", "rw"),
            ],
            env_vars=config.get("inference_env_vars"),
            cmd_args=[],
            description="Inference",
        )

        output_json_path = model_output_dir / "output.json"
        if not output_json_path.exists():
            raise CLIError(
                f"Model inference failed: Expected output file {output_json_path} was not created. "
                f"Check model configuration and Docker logs."
            )

    def _run_postprocess(self, config: Dict, run_cache_dir: Path):
        """
        Run the postprocessing step of the model pipeline.

        Executes the model adapter's postprocessing Docker container, converting model output
        into final cell embeddings.

        Args:
            config (Dict): Model configuration from the registry.
            run_cache_dir (Path): Directory for caching pipeline files.

        Raises:
            CLIError: If postprocessing fails or embeddings file is missing.
        """
        logger.info("3. Running Postprocessing Step...")

        model_output_dir = run_cache_dir / "model_output"
        task_input_dir = run_cache_dir / "task_input"
        task_input_dir.mkdir(exist_ok=True)

        output_json_path = model_output_dir / "output.json"
        if output_json_path.exists():
            logger.info("Using output.json created by inference step.")
        else:
            raise CLIError(
                f"output.json not found in {model_output_dir}. Model inference may have failed."
            )

        self.docker.run(
            image=config["adapter_image"],
            mounts=[
                (str(model_output_dir), "/model_output", "ro"),
                (str(task_input_dir), "/task_input", "rw"),
            ],
            cmd_args=["postprocess"],
            description="Postprocessing",
        )
