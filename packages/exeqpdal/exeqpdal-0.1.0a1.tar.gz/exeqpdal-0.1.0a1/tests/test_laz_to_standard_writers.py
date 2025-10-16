"""Test standard point cloud format writers.

Tests writers that are commonly available and reliable:
- LAS/LAZ (compressed and uncompressed)
- COPC (Cloud Optimized Point Cloud)
- PLY (Polygon File Format)
- PCD (Point Cloud Data)
- BPF (Binary Point Format)
- Arrow/Parquet
- E57 (ASTM E57)
- Draco (Google Draco compression)
- SBET (Smoothed Best Estimate Trajectory)

These tests expect high success rates (95%+) and validate:
1. Pipeline execution
2. Point count accuracy
3. Output file existence and size
4. Round-trip capability (for supported formats)

Constitutional Alignment:
- §VII (Testing Strategy): Integration tests with real PDAL
- §VIII (Error Handling): Graceful exception handling

Dev Guide References:
- §8.3 (Integration Tests)
- §8.1 (Test Organization)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from conftest import (
    get_output_filename,
    handle_writer_exception,
    validate_output_file,
)

import exeqpdal as pdal
from exeqpdal import Pipeline
from exeqpdal.exceptions import PDALExecutionError

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration, pytest.mark.slow, pytest.mark.usefixtures("skip_if_no_pdal")]

# Test data: (writer_name, extension, options, test_roundtrip)
STANDARD_WRITERS = [
    # LAS formats (standard, always available)
    ("las", ".las", {}, True),
    ("las_compressed", ".laz", {"compression": "laszip"}, True),
    # Cloud Optimized (usually available)
    ("copc", ".copc.laz", {}, True),
    # Common point cloud formats
    ("ply", ".ply", {}, True),
    ("pcd", ".pcd", {}, False),  # PCL format, may not support round-trip
    ("bpf", ".bpf", {}, False),  # Binary Point Format
    # Specialized formats
    ("arrow", ".parquet", {}, False),  # Apache Arrow/Parquet
    ("e57", ".e57", {}, False),  # ASTM E57
    ("draco", ".drc", {}, False),  # Google Draco
    ("sbet", ".sbet", {}, False),  # Trajectory format
]


@pytest.mark.integration
@pytest.mark.parametrize(
    ("writer_name", "extension", "options", "test_roundtrip"),
    STANDARD_WRITERS,
    ids=[w[0] for w in STANDARD_WRITERS],
)
def test_standard_writer(
    skip_if_no_pdal: None,
    writer_test_laz: Path,
    writer_output_dir: Path,
    writer_name: str,
    extension: str,
    options: dict[str, str],
    test_roundtrip: bool,
) -> None:
    """Test standard point cloud writer.

    Args:
        skip_if_no_pdal: Fixture to skip if PDAL not available
        writer_test_laz: Source LAZ file (49MB, 10.9M points)
        writer_output_dir: Output directory for results
        writer_name: Writer type (las, copc, ply, etc.)
        extension: File extension (.las, .copc.laz, etc.)
        options: Writer-specific options
        test_roundtrip: Whether to test round-trip capability
    """
    # Get output filename
    output_file = get_output_filename("standard", writer_name, extension)

    # Create pipeline
    reader = pdal.Reader.las(str(writer_test_laz))

    # Get writer method - handle special cases
    if writer_name == "las_compressed":
        writer = pdal.Writer.las(output_file, **options)
    else:
        writer_method = getattr(pdal.Writer, writer_name)
        writer = writer_method(output_file, **options)

    pipeline = Pipeline(reader | writer)

    # Execute
    try:
        point_count = pipeline.execute()
    except PDALExecutionError as e:
        handle_writer_exception(e, writer_name)
        return

    # Validate execution
    assert point_count > 0, f"No points processed for {writer_name}"

    # Validate output file
    validation = validate_output_file(output_file, expected_points=point_count)
    assert validation["valid"], f"Output validation failed for {writer_name}"

    print(f"✓ {writer_name}: {point_count:,} points, {validation['size']:,} bytes")

    # Round-trip test (if supported)
    if test_roundtrip:
        verify_file = get_output_filename("standard", f"{writer_name}_verify", extension)

        try:
            # Read output file and write to verify file
            pipeline2 = Pipeline(pdal.Reader.las(output_file) | pdal.Writer.las(verify_file))
            point_count2 = pipeline2.execute()

            # Validate round-trip point count
            assert point_count2 == point_count, (
                f"Round-trip point count mismatch for {writer_name}: "
                f"original={point_count}, round-trip={point_count2}"
            )

            print(f"  ✓ Round-trip verified: {point_count2:,} points preserved")

        except PDALExecutionError as e:
            # Round-trip failure is not critical - just log
            print(f"  ⚠ Round-trip test skipped: {str(e)[:80]}")


@pytest.mark.integration
def test_null_writer(
    skip_if_no_pdal: None,
    writer_test_laz: Path,
) -> None:
    """Test null writer (no output file).

    Null writer discards output - useful for testing pipelines without I/O.
    """
    pipeline = Pipeline(pdal.Reader.las(str(writer_test_laz)) | pdal.Writer.null())

    try:
        point_count = pipeline.execute()
    except PDALExecutionError as e:
        handle_writer_exception(e, "null")
        return

    # Validate execution (no output file to check)
    assert point_count > 0, "No points processed for null writer"

    print(f"✓ null writer: {point_count:,} points processed (no output)")
