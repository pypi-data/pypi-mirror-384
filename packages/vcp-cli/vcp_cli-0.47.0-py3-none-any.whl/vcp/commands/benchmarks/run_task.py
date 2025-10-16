"""
Unified task execution module for benchmarking tasks.

This module provides a single, robust task runner that supports both single and
multi-dataset benchmarks, with automatic reference resolution and baseline computation.
"""

import logging
from typing import Any, Dict, List, Union

import numpy as np
import scipy.sparse as sp
from anndata import AnnData
from czbenchmarks.tasks import TASK_REGISTRY
from czbenchmarks.tasks.types import CellRepresentation

from .resolve_references import resolve_anndata_references

logger = logging.getLogger(__name__)
RANDOM_SEED = 42


def _ensure_dense_matrix(cell_rep: Union[CellRepresentation, np.ndarray]) -> np.ndarray:
    if sp.issparse(cell_rep):
        return cell_rep.toarray()
    return cell_rep


def run_task(
    task_name: str,
    *,
    adata_input: Union[AnnData, List[AnnData]],
    cell_representation_input: Union[
        str, CellRepresentation, List[Union[str, CellRepresentation]]
    ],
    run_baseline: bool = False,
    baseline_params: Dict[str, Any] | None = None,
    task_params: Dict[str, Any] | None = None,
    random_seed: int = RANDOM_SEED,
) -> List[Dict[str, Any]]:
    """
    Unified task runner for single and multi-dataset benchmarks.
    """

    if random_seed is None:
        random_seed = RANDOM_SEED

    logger.info(f"Preparing to run task: '{task_name}'")

    TaskClass = TASK_REGISTRY.get_task_class(task_name)
    task_instance = TaskClass(random_seed=random_seed)
    is_multi_dataset_task = getattr(task_instance, "requires_multiple_datasets", False)

    if isinstance(adata_input, list):
        anndata_objects = [
            dataset.adata if hasattr(dataset, "adata") else dataset
            for dataset in adata_input
        ]
    else:
        anndata_objects = (
            adata_input.adata if hasattr(adata_input, "adata") else adata_input
        )

    resolved_task_params = resolve_anndata_references(
        task_params or {}, anndata_objects
    )
    resolved_baseline_params = resolve_anndata_references(
        baseline_params or {}, anndata_objects
    )
    resolved_cell_repr = resolve_anndata_references(
        cell_representation_input, anndata_objects
    )

    if run_baseline:
        if is_multi_dataset_task:
            logger.warning(
                f"Baseline computation is not supported for multi-dataset task '{task_name}'."
            )
        else:
            logger.info(f"Computing baseline for '{task_name}'...")
            try:
                resolved_cell_repr = task_instance.compute_baseline(
                    expression_data=resolved_cell_repr, **resolved_baseline_params
                )
                logger.info("Baseline computation complete.")
            except NotImplementedError:
                logger.warning(f"Baseline not implemented for '{task_name}'.")
            except Exception as e:
                logger.warning(
                    f"Baseline computation failed for '{task_name}': {e}. "
                    f"Continuing with original cell representation."
                )

    final_cell_repr = (
        [_ensure_dense_matrix(rep) for rep in resolved_cell_repr]
        if isinstance(resolved_cell_repr, list)
        else _ensure_dense_matrix(resolved_cell_repr)
    )

    TASK_REGISTRY.validate_task_input(task_name, resolved_task_params)
    task_input_model = TaskClass.input_model(**resolved_task_params)

    logger.info(f"Executing task logic for '{task_name}'...")
    results = task_instance.run(
        cell_representation=final_cell_repr,
        task_input=task_input_model,
    )
    logger.info(f"Task '{task_name}' execution complete.")
    return [res.model_dump() for res in results]
