"""PDAL info application."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, cast

from exeqpdal.core.executor import executor
from exeqpdal.exceptions import PDALExecutionError

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def info(
    filename: str | Path,
    *,
    all: bool = False,
    stats: bool = False,
    metadata: bool = False,
    schema: bool = False,
    boundary: bool = False,
    dimensions: bool = False,
    summary: bool = False,
    pipeline: bool = False,
    pointcloudschema: bool = False,
) -> dict[str, Any]:
    """Get information about a point cloud file.

    Args:
        filename: Input file path
        all: Include all information
        stats: Include statistics
        metadata: Include metadata
        schema: Include schema information
        boundary: Include boundary information
        dimensions: Include dimension information
        summary: Include summary information
        pipeline: Include pipeline information
        pointcloudschema: Include point cloud schema

    Returns:
        Dictionary with file information

    Raises:
        PDALExecutionError: If info command fails
    """
    args = [str(filename)]

    if all:
        args.append("--all")
    if stats:
        args.append("--stats")
    if metadata:
        args.append("--metadata")
    if schema:
        args.append("--schema")
    if boundary:
        args.append("--boundary")
    if dimensions:
        args.append("--dimensions")
    if summary:
        args.append("--summary")
    if pipeline:
        args.append("--pipeline")
    if pointcloudschema:
        args.append("--pointcloudschema")

    logger.info(f"Getting info for: {filename}")
    stdout, stderr, _ = executor.execute_application("info", args)

    try:
        result = json.loads(stdout)
        logger.debug(f"Info result: {len(stdout)} bytes")
        return cast("dict[str, Any]", result)
    except json.JSONDecodeError as e:
        raise PDALExecutionError(
            f"Failed to parse info output: {e}",
            stdout=stdout,
            stderr=stderr,
        ) from e


def get_bounds(filename: str | Path) -> dict[str, float]:
    """Get bounds of a point cloud file.

    Args:
        filename: Input file path

    Returns:
        Dictionary with bounds (minx, miny, minz, maxx, maxy, maxz)
    """
    result = info(filename, boundary=True)
    return cast("dict[str, float]", result.get("boundary", {}))


def get_count(filename: str | Path) -> int:
    """Get point count from a file.

    Args:
        filename: Input file path

    Returns:
        Number of points in file
    """
    result = info(filename)
    return cast("int", result.get("count", 0))


def get_dimensions(filename: str | Path) -> list[str]:
    """Get list of dimensions in a file.

    Args:
        filename: Input file path

    Returns:
        List of dimension names
    """
    result = info(filename, schema=True)
    schema = result.get("schema", {}).get("dimensions", [])
    return [dim.get("name", "") for dim in schema]


def get_srs(filename: str | Path) -> str:
    """Get spatial reference system of a file.

    Args:
        filename: Input file path

    Returns:
        SRS string (WKT format)
    """
    result = info(filename, metadata=True)
    metadata = result.get("metadata", {})
    return cast("str", metadata.get("srs", {}).get("wkt", ""))


def get_stats(filename: str | Path) -> dict[str, Any]:
    """Get statistics for all dimensions in a file.

    Args:
        filename: Input file path

    Returns:
        Dictionary with dimension statistics
    """
    result = info(filename, stats=True)
    return cast("dict[str, Any]", result.get("stats", {}))
