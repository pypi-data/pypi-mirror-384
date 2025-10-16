#!/usr/bin/env python3
"""
Transform benchmark result JSON files by combining task_results arrays into a single JSON array.
Denormalizes sibling attributes (czbenchmarks_version, timestamp) and batch random seeds
from args into each task_result element.
"""

import json
import re
import string
from pathlib import Path
from typing import Any, Dict, List


def extract_batch_random_seeds(args_string: str) -> List[str]:
    """Extract batch random seeds from the args string."""
    # Look for --batch-random-seeds followed by space-delimited values
    match = re.search(r"--batch-random-seeds\s+((?:\d+\s*)+)", args_string)
    if match:
        seeds = match.group(1).strip().split()
        return seeds
    return []


def transform_task_result(
    task_result: Dict[str, Any],
    czbenchmarks_version: str,
    timestamp: str,
    batch_seeds: List[str],
) -> Dict[str, Any]:
    """Transform a single task result by adding denormalized attributes."""
    # Create a copy to avoid modifying the original
    transformed = task_result.copy()
    if "task_name" in transformed:
        transformed["task_key"] = transformed.pop("task_name")
    if "model_type" in transformed:
        base_model_key = transformed.pop("model_type")
        model_variant = None

        if "model_args" in transformed and isinstance(transformed["model_args"], dict):
            model_variant = transformed["model_args"].get("model_variant")
            if model_variant:
                # Remove model_key prefix from model_variant if present (case-insensitive)
                # Also remove any punctuation after the prefix in the variant
                if model_variant.lower().startswith(base_model_key.lower()):
                    model_variant = model_variant[len(base_model_key) :]
                    # Remove leading punctuation (including dash, underscore, etc.)
                    model_variant = model_variant.lstrip(string.punctuation)
            del transformed["model_args"]

        # Construct versioned model key: base-v1-variant or base-v1
        if model_variant:
            transformed["model_key"] = f"{base_model_key}-v1-{model_variant}"
        else:
            transformed["model_key"] = f"{base_model_key}-v1"
    # Remove runtime_metrics
    if "dataset_names" in transformed:
        transformed["dataset_keys"] = transformed.pop("dataset_names")
    del transformed["runtime_metrics"]

    # Add denormalized attributes
    transformed["czbenchmarks_version"] = czbenchmarks_version
    transformed["timestamp"] = timestamp

    # Add batch random seeds to each metric and normalize metric_type to metric_key
    if "metrics" in transformed and isinstance(transformed["metrics"], list):
        for i, metric in enumerate(transformed["metrics"]):
            if i < len(batch_seeds):
                metric["batch_random_seeds"] = batch_seeds
            if "metric_type" in metric:
                metric["metric_key"] = metric.pop("metric_type")

    return transformed


def process_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Process a single JSON file and return transformed task results."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract required attributes
        czbenchmarks_version = data.get("czbenchmarks_version", "")
        timestamp = data.get("timestamp", "")
        args = data.get("args", "")
        task_results = data.get("task_results", [])

        # Extract batch random seeds from args
        batch_seeds = extract_batch_random_seeds(args)

        # Transform each task result
        transformed_results = []
        for task_result in task_results:
            transformed = transform_task_result(
                task_result, czbenchmarks_version, timestamp, batch_seeds
            )
            transformed_results.append(transformed)

        print(f"Processed {file_path.name}: {len(transformed_results)} task results")
        return transformed_results

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {file_path.name}: {e}")
        return []
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return []


def main():
    """Main function to process all JSON files and combine results."""
    # Define input and output paths
    input_dir = Path("src/vcp/commands/benchmarks/stub_data/results")
    output_file = Path("src/vcp/commands/benchmarks/stub_data/results.json")

    # Check if input directory exists
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return

    # Find all JSON files
    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return

    print(f"Found {len(json_files)} JSON files to process")

    # Process all files and combine results
    all_task_results = []
    for json_file in sorted(json_files):
        task_results = process_json_file(json_file)
        all_task_results.extend(task_results)

    # Write combined results to output file
    try:
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_task_results, f, indent=2, ensure_ascii=False)

        print(f"\nCombined {len(all_task_results)} task results into {output_file}")
        print(f"Output file size: {output_file.stat().st_size:,} bytes")

    except Exception as e:
        print(f"Error writing output file: {e}")


if __name__ == "__main__":
    main()
