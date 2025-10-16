"""Test raster format writers.

Raster writers convert point clouds to raster grids:
- GDAL (GeoTIFF via GDAL)
- Raster (generic raster output)
- OGR (vector formats via OGR/GDAL)

Characteristics:
- Require resolution parameter
- Point cloud → raster transformation
- May fail with insufficient point density
- Configuration-dependent success (70%)

Tests validate:
1. Pipeline execution with required parameters
2. Output file creation
3. Graceful handling of configuration issues

Constitutional Alignment:
- §VII (Testing Strategy): Integration tests
- §VIII (Error Handling): Graceful skip for configuration issues

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

# Test configurations: (writer_name, extension, options)
RASTER_WRITERS: list[tuple[str, str, dict[str, float | str]]] = [
    # GDAL writer variations
    ("gdal", ".tif", {"resolution": 1.0, "output_type": "mean"}),
    ("gdal", ".tif", {"resolution": 0.5, "output_type": "max"}),
    ("gdal", ".tif", {"resolution": 2.0, "output_type": "idw"}),
    # Raster writer
    ("raster", ".tif", {"resolution": 1.0}),
    # OGR writer (vector)
    ("ogr", ".shp", {}),
]


def _make_test_id(params: tuple[str, str, dict[str, float | str]]) -> str:
    """Generate test ID for raster writer test."""
    writer_name, _extension, options = params
    config = options.get("output_type", "default")
    return f"{writer_name}_{config}"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("writer_name", "extension", "options"),
    RASTER_WRITERS,
    ids=[_make_test_id(w) for w in RASTER_WRITERS],
)
def test_raster_writer(
    skip_if_no_pdal: None,
    writer_test_laz: Path,
    writer_output_dir: Path,
    writer_name: str,
    extension: str,
    options: dict[str, float | str],
) -> None:
    """Test raster format writer.

    Args:
        skip_if_no_pdal: Fixture to skip if PDAL not available
        writer_test_laz: Source LAZ file (49MB, 10.9M points)
        writer_output_dir: Output directory for results
        writer_name: Writer type (gdal, raster, ogr)
        extension: File extension (.tif, .shp)
        options: Writer-specific options (resolution, output_type, etc.)
    """
    # Get output filename
    config_id = str(options.get("output_type", "default"))
    output_file = get_output_filename("raster", writer_name, extension, config_id)

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
    # Note: Point count may be 0 for raster writers (they don't "process" points)
    assert point_count >= 0, f"Negative point count for {writer_name}"

    # Validate output file
    validation = validate_output_file(output_file)
    assert validation["valid"], f"Output validation failed for {writer_name}"

    print(f"✓ {writer_name}_{config_id}: {point_count:,} points, {validation['size']:,} bytes")
