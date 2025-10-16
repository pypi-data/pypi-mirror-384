"""Test special format writers with external dependencies.

Special writers may require external libraries:
- NITF (military format)
- GLTF (3D scene format)
- E57 (already tested in standard, included for completeness)
- Draco (already tested in standard, included for completeness)
- SBET (already tested in standard, included for completeness)

Characteristics:
- May not be available in all PDAL builds
- Format-specific options
- Graceful skip if unavailable
- Success rate 60-80% (installation-dependent)

Tests validate:
1. Writer availability check
2. Output file creation (if available)
3. Graceful skip with informative message

Constitutional Alignment:
- §VII (Testing Strategy): Integration tests
- §VIII (Error Handling): Graceful skip for missing dependencies

Dev Guide References:
- §8.3 (Integration Tests)
- §7.2 (CLI Error Parsing)
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

# Special format writers
SPECIAL_WRITERS: list[tuple[str, str, dict[str, str | float]]] = [
    ("nitf", ".ntf", {}),
    ("gltf", ".gltf", {}),
]


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.parametrize(
    ("writer_name", "extension", "options"),
    SPECIAL_WRITERS,
    ids=[w[0] for w in SPECIAL_WRITERS],
)
def test_special_writer(
    skip_if_no_pdal: None,
    writer_test_laz: Path,
    writer_output_dir: Path,
    writer_name: str,
    extension: str,
    options: dict[str, str | float],
) -> None:
    """Test special format writer with external dependency.

    Args:
        skip_if_no_pdal: Fixture to skip if PDAL not available
        writer_test_laz: Source LAZ file (49MB, 10.9M points)
        writer_output_dir: Output directory for results
        writer_name: Writer type (nitf, gltf)
        extension: File extension (.ntf, .gltf)
        options: Writer-specific options
    """
    # Get output filename
    output_file = get_output_filename("special", writer_name, extension)

    # Create pipeline
    writer_method = getattr(pdal.Writer, writer_name)
    pipeline = Pipeline(
        pdal.Reader.las(str(writer_test_laz)) | writer_method(output_file, **options)
    )

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
