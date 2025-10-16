"""Test text/ASCII writer with multiple configurations.

Text writer is unique:
- Requires dimension ordering
- Human-readable output
- Supports multiple field combinations
- 100% success rate expected

Tests validate:
1. Multiple dimension orderings (XYZ, XYZI, XYZIC, etc.)
2. Output file readability
3. Column count matches specification
4. Point count preservation

Constitutional Alignment:
- §VII (Testing Strategy): Integration tests
- §VIII (Error Handling): Clear error messages

Dev Guide References:
- §8.3 (Integration Tests)
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

# Test configurations: (config_id, options, expected_columns)
TEXT_WRITER_CONFIGS = [
    ("xyz", {"order": "X,Y,Z", "keep_unspecified": False}, 3),
    ("xyzi", {"order": "X,Y,Z,Intensity", "keep_unspecified": False}, 4),
    ("xyzic", {"order": "X,Y,Z,Intensity,Classification", "keep_unspecified": False}, 5),
    (
        "xyzrgb",
        {"order": "X,Y,Z,Red,Green,Blue", "keep_unspecified": False},
        6,
    ),
    ("all", {"keep_unspecified": True}, None),  # Variable columns
]


@pytest.mark.integration
@pytest.mark.parametrize(
    ("config_id", "options", "expected_columns"),
    TEXT_WRITER_CONFIGS,
    ids=[config[0] for config in TEXT_WRITER_CONFIGS],
)
def test_text_writer_configurations(
    skip_if_no_pdal: None,
    writer_test_laz: Path,
    writer_output_dir: Path,
    config_id: str,
    options: dict[str, str | bool],
    expected_columns: int | None,
) -> None:
    """Test text writer with different dimension configurations.

    Args:
        skip_if_no_pdal: Fixture to skip if PDAL not available
        writer_test_laz: Source LAZ file (49MB, 10.9M points)
        writer_output_dir: Output directory for results
        config_id: Configuration identifier (xyz, xyzi, etc.)
        options: Writer options (order, keep_unspecified)
        expected_columns: Expected number of columns (None = variable)
    """
    from pathlib import Path

    # Get output filename
    output_file = get_output_filename("text", "text", ".txt", config_id)

    # Create pipeline
    pipeline = Pipeline(
        pdal.Reader.las(str(writer_test_laz)) | pdal.Writer.text(output_file, **options)
    )

    # Execute
    try:
        point_count = pipeline.execute()
    except PDALExecutionError as e:
        handle_writer_exception(e, f"text_{config_id}")
        return

    # Validate execution
    assert point_count > 0, f"No points processed for text writer ({config_id})"

    # Validate output file
    validation = validate_output_file(output_file, expected_points=point_count)
    assert validation["valid"], f"Output validation failed for text writer ({config_id})"

    # Read first line to validate column count (CSV format)
    output_path = Path(output_file)
    with output_path.open() as f:
        first_line = f.readline().strip()
        # PDAL text writer outputs CSV format with commas
        columns = first_line.split(",")

        if expected_columns is not None:
            assert len(columns) == expected_columns, (
                f"Column count mismatch for {config_id}: "
                f"expected={expected_columns}, actual={len(columns)}"
            )

        print(
            f"✓ text_{config_id}: {point_count:,} points, "
            f"{len(columns)} columns, {validation['size']:,} bytes"
        )


@pytest.mark.integration
def test_text_writer_basic(
    skip_if_no_pdal: None,
    writer_test_laz: Path,
    writer_output_dir: Path,
) -> None:
    """Test basic text writer (XYZ only).

    Simple test for text writer with minimal configuration.
    """
    from pathlib import Path

    output_file = get_output_filename("text", "text", ".txt", "basic")

    pipeline = Pipeline(
        pdal.Reader.las(str(writer_test_laz))
        | pdal.Writer.text(output_file, order="X,Y,Z", keep_unspecified=False)
    )

    try:
        point_count = pipeline.execute()
    except PDALExecutionError as e:
        handle_writer_exception(e, "text")
        return

    assert point_count > 0, "No points processed for basic text writer"

    # Validate file is readable
    output_path = Path(output_file)
    assert output_path.exists(), "Output file not created"

    # Count lines (should match point count + 1 header line for CSV)
    line_count = sum(1 for _ in output_path.open())
    expected_lines = point_count + 1  # +1 for CSV header
    assert line_count == expected_lines, (
        f"Line count mismatch: expected={expected_lines}, actual={line_count}"
    )

    print(f"✓ text_basic: {point_count:,} points, {line_count:,} lines")
