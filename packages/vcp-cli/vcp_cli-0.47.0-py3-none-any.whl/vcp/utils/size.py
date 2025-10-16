import re
from typing import List, Optional, Union

from vcp.datasets.api import (
    DataItem,
    DataItemSimplified,
    DatasetRecord,
    DatasetSizeModel,
)


def format_size_bytes(bytes_size: int) -> str:
    """Format bytes to human readable size."""
    if bytes_size < 0:
        return "Unknown"

    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def parse_content_size(content_size: Optional[Union[str, int]]) -> int:
    """
    Parse various size string formats to bytes.

    Handles formats like:
    - "1024" (bytes)
    - "1.5 KB", "2.3MB", "1 GB"
    - "1,024 bytes"

    Returns 0 if unable to parse.
    """
    if not content_size:
        return 0

    if isinstance(content_size, int):
        return content_size

    if isinstance(content_size, str):
        # Remove commas and convert to lowercase for easier parsing
        content_size = content_size.replace(",", "").lower().strip()

        # Handle plain numbers (assume bytes)
        if content_size.isdigit():
            return int(content_size)

        # Define unit multipliers
        units = {
            "b": 1,
            "byte": 1,
            "bytes": 1,
            "kb": 1024,
            "kib": 1024,
            "kilobyte": 1024,
            "kilobytes": 1024,
            "mb": 1024**2,
            "mib": 1024**2,
            "megabyte": 1024**2,
            "megabytes": 1024**2,
            "gb": 1024**3,
            "gib": 1024**3,
            "gigabyte": 1024**3,
            "gigabytes": 1024**3,
            "tb": 1024**4,
            "tib": 1024**4,
            "terabyte": 1024**4,
            "terabytes": 1024**4,
        }

        # Try to extract number and unit using regex
        match = re.match(r"^(\d*\.?\d+)\s*([a-z]+)?$", content_size)
        if match:
            number_str, unit = match.groups()
            try:
                number = float(number_str)
                unit = unit or "b"  # Default to bytes if no unit specified

                if unit in units:
                    return int(number * units[unit])
            except ValueError:
                pass

    return 0


def calculate_total_dataset_size(record: DatasetRecord) -> int:
    """Calculate total size of all files in a dataset."""
    total_size = 0

    # Get distribution from md field if available
    md = record.md
    distribution = md.distribution if md else []

    if distribution:
        for asset in distribution:
            if isinstance(asset, dict):
                content_size = asset.get("contentSize")
            else:
                # Handle CroissantFileObject
                content_size = getattr(asset, "content_size", None)

            total_size += parse_content_size(content_size)

    elif hasattr(record, "distribution") and record.distribution:
        # Fallback to record.distribution
        for f in record.distribution:
            content_size = getattr(f, "content_size", None)
            total_size += parse_content_size(content_size)

    return total_size


def calculate_search_results_total_size(
    items: List[Union[DataItem, DataItemSimplified]],
) -> int:
    """Calculate total size across multiple datasets from search results."""
    total_size = 0

    for item in items:
        # Check if locations contain DatasetSizeModel objects with size info
        for location in item.locations:
            if (
                isinstance(location, DatasetSizeModel)
                and location.contentSize is not None
            ):
                total_size += location.contentSize

    return total_size


def get_file_count_from_dataset(record: DatasetRecord) -> int:
    """Count the number of files in a dataset."""
    file_count = 0

    # Get distribution from md field if available
    md = record.md
    distribution = md.distribution if md else []

    if distribution:
        file_count = len(distribution)
    elif hasattr(record, "distribution") and record.distribution:
        file_count = len(record.distribution)
    elif hasattr(record, "locations") and record.locations:
        file_count = len(record.locations)

    return file_count


def get_file_count_from_search_results(
    items: List[Union[DataItem, DataItemSimplified]],
) -> int:
    """Count the number of files across multiple datasets from search results."""
    file_count = 0

    for item in items:
        # Count DatasetSizeModel objects in locations as files
        for location in item.locations:
            if isinstance(location, DatasetSizeModel):
                file_count += 1

    return file_count


def calculate_dataset_size_from_search_item(
    item: Union[DataItem, DataItemSimplified],
) -> int:
    """Calculate total size of a single dataset from search results."""
    total_size = 0

    for location in item.locations:
        if isinstance(location, DatasetSizeModel) and location.contentSize is not None:
            total_size += location.contentSize

    return total_size
