"""PDAL applications - merge, split, tile, tindex."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from exeqpdal.core.executor import executor

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def merge(
    input_files: list[str | Path],
    output_file: str | Path,
) -> None:
    """Merge multiple point cloud files into one.

    Args:
        input_files: List of input file paths
        output_file: Output file path

    Raises:
        PDALExecutionError: If merge fails
    """
    args = [str(f) for f in input_files] + [str(output_file)]

    logger.info(f"Merging {len(input_files)} files to {output_file}")
    executor.execute_application("merge", args)
    logger.info("Merge completed")


def split(
    input_file: str | Path,
    output_pattern: str | Path,
    *,
    length: int | None = None,
    capacity: int | None = None,
) -> None:
    """Split a point cloud file into multiple files.

    Args:
        input_file: Input file path
        output_pattern: Output filename pattern (use # for numbers)
        length: Split by distance (meters)
        capacity: Split by point count

    Raises:
        PDALExecutionError: If split fails

    Examples:
        >>> split("input.las", "output_#.las", capacity=100000)
    """
    args = [str(input_file), str(output_pattern)]

    if length is not None:
        args.extend(["--length", str(length)])

    if capacity is not None:
        args.extend(["--capacity", str(capacity)])

    logger.info(f"Splitting {input_file} to {output_pattern}")
    executor.execute_application("split", args)
    logger.info("Split completed")


def tile(
    input_file: str | Path,
    output_pattern: str | Path,
    *,
    length: float | None = None,
    origin_x: float | None = None,
    origin_y: float | None = None,
    buffer: float | None = None,
) -> None:
    """Create tiles from a point cloud file.

    Args:
        input_file: Input file path
        output_pattern: Output filename pattern (use # for tile numbers, e.g. "tile_#.las")
        length: Tile edge length (meters)
        origin_x: X origin for tiling
        origin_y: Y origin for tiling
        buffer: Buffer around tiles (meters)

    Raises:
        PDALExecutionError: If tiling fails

    Examples:
        >>> tile("input.las", "tiles/tile_#.las", length=100.0)
    """
    args = [str(input_file), str(output_pattern)]

    if length is not None:
        args.extend(["--length", str(length)])

    if origin_x is not None:
        args.extend(["--origin_x", str(origin_x)])

    if origin_y is not None:
        args.extend(["--origin_y", str(origin_y)])

    if buffer is not None:
        args.extend(["--buffer", str(buffer)])

    logger.info(f"Tiling {input_file} to {output_pattern}")
    executor.execute_application("tile", args)
    logger.info("Tiling completed")


def tindex(
    input_files: list[str | Path],
    output_file: str | Path,
    *,
    filespec: str | None = None,
    tindex_name: str | None = None,
    fast_boundary: bool = False,
) -> None:
    """Create a tile index from multiple files.

    Args:
        input_files: List of input file paths
        output_file: Output index file path
        filespec: File specification pattern
        tindex_name: Tile index column name
        fast_boundary: Use fast boundary computation

    Raises:
        PDALExecutionError: If tindex creation fails
    """
    args = ["create", "--tindex", str(output_file), "-f", "GeoJSON"] + [str(f) for f in input_files]

    if filespec is not None:
        args.extend(["--filespec", filespec])

    if tindex_name is not None:
        args.extend(["--tindex_name", tindex_name])

    if fast_boundary:
        args.append("--fast_boundary")

    logger.info(f"Creating tile index from {len(input_files)} files")
    executor.execute_application("tindex", args)
    logger.info("Tile index created")


def pipeline(
    pipeline_file: str | Path,
    *,
    validate: bool = False,
    stream: bool | None = None,
) -> None:
    """Execute a PDAL pipeline from JSON file.

    Args:
        pipeline_file: Path to pipeline JSON file
        validate: Validate without executing
        stream: Force stream mode (True) or standard mode (False)

    Raises:
        PDALExecutionError: If pipeline execution fails
    """
    args = [str(pipeline_file)]

    if validate:
        args.append("--validate")

    if stream is True:
        args.append("--stream")
    elif stream is False:
        args.append("--nostream")

    logger.info(f"Executing pipeline from {pipeline_file}")
    executor.execute_application("pipeline", args)
    logger.info("Pipeline executed")
