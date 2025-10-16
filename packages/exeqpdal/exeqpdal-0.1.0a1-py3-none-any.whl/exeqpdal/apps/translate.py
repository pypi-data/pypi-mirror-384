"""PDAL translate application."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from exeqpdal.core.executor import executor

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def translate(
    input_file: str | Path,
    output_file: str | Path,
    *,
    filters: list[str] | None = None,
    reader: str | None = None,
    writer: str | None = None,
    **options: Any,
) -> None:
    """Translate between point cloud formats.

    Args:
        input_file: Input file path
        output_file: Output file path
        filters: List of filter names to apply
        reader: Explicit reader type (e.g., 'readers.las')
        writer: Explicit writer type (e.g., 'writers.las')
        **options: Filter/reader/writer options (prefix with stage name, e.g., filters_range_limits)

    Raises:
        PDALExecutionError: If translation fails

    Examples:
        >>> translate("input.las", "output.laz")
        >>> translate("input.las", "output.las", filters=["range", "outlier"])
        >>> translate(
        ...     "input.las",
        ...     "output.las",
        ...     filters=["range"],
        ...     filters_range_limits="Classification[2:2]"
        ... )
    """
    args = [str(input_file), str(output_file)]

    # Add reader
    if reader:
        args.extend(["--reader", reader])

    # Add writer
    if writer:
        args.extend(["--writer", writer])

    # Add filters
    if filters:
        for filter_name in filters:
            args.extend(["--filter", filter_name])

    # Add options
    for key, value in options.items():
        # Convert underscores to dots for PDAL options
        option_name = key.replace("_", ".")
        args.append(f"--{option_name}={value}")

    logger.info(f"Translating {input_file} to {output_file}")
    executor.execute_application("translate", args)
    logger.info("Translation completed")


def convert(
    input_file: str | Path,
    output_file: str | Path,
    **options: Any,
) -> None:
    """Convert between point cloud formats (alias for translate).

    Args:
        input_file: Input file path
        output_file: Output file path
        **options: Translation options

    Raises:
        PDALExecutionError: If conversion fails
    """
    translate(input_file, output_file, **options)
