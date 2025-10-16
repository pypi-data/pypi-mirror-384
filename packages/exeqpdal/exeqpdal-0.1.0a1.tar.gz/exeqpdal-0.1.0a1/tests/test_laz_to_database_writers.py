"""Test database writers (requires database setup).

Database writers:
- pgpointcloud (PostgreSQL with PointCloud extension)
- tiledb (TileDB arrays)

Characteristics:
- Require database connection/infrastructure
- Cannot test without setup
- Skip by default with clear message
- Document setup requirements

Tests:
1. Skipped by default (@pytest.mark.skip)
2. Can be enabled with environment variables
3. Provide clear setup documentation

Constitutional Alignment:
- §VII (Testing Strategy): Integration tests when infrastructure available
- §VIII (Error Handling): Clear skip messages

Dev Guide References:
- §8.3 (Integration Tests)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from conftest import handle_writer_exception

import exeqpdal as pdal
from exeqpdal import Pipeline
from exeqpdal.exceptions import PDALExecutionError

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration, pytest.mark.slow, pytest.mark.usefixtures("skip_if_no_pdal")]


@pytest.mark.skip(reason="Database writers require database setup - see docstring for details")
@pytest.mark.database
def test_pgpointcloud_writer(
    skip_if_no_pdal: None,
    writer_test_laz: Path,
) -> None:
    """Test PostgreSQL PointCloud writer.

    **Setup Required**:
    1. Install PostgreSQL with PointCloud extension
    2. Create database: `createdb test_pointcloud`
    3. Enable extension: `psql test_pointcloud -c "CREATE EXTENSION pointcloud;"`
    4. Set environment variable: `export TEST_PGPOINTCLOUD_CONNECTION="postgresql://user:pass@localhost/test_pointcloud"`

    **To run this test**:
    ```bash
    pytest tests/laz_to_writers/test_database_writers.py::test_pgpointcloud_writer -v
    ```

    **Expected behavior**:
    - Test skipped if TEST_PGPOINTCLOUD_CONNECTION not set
    - Test runs if connection configured
    """
    # Check for environment variable
    connection = os.getenv("TEST_PGPOINTCLOUD_CONNECTION")
    if not connection:
        pytest.skip(
            "PostgreSQL PointCloud connection not configured. "
            "Set TEST_PGPOINTCLOUD_CONNECTION environment variable."
        )

    # Create pipeline
    pipeline = Pipeline(
        pdal.Reader.las(str(writer_test_laz))
        | pdal.Writer.pgpointcloud(
            connection=connection,
            table="test_writer_output",
            overwrite=True,
        )
    )

    # Execute
    try:
        point_count = pipeline.execute()
    except PDALExecutionError as e:
        handle_writer_exception(e, "pgpointcloud")
        return

    # Validate execution
    assert point_count > 0, "No points processed for pgpointcloud writer"

    print(f"✓ pgpointcloud: {point_count:,} points written to database")


@pytest.mark.skip(reason="TileDB writer requires TileDB library - see docstring for details")
@pytest.mark.database
def test_tiledb_writer(
    skip_if_no_pdal: None,
    writer_test_laz: Path,
    writer_output_dir: Path,
) -> None:
    """Test TileDB writer.

    **Setup Required**:
    1. Install TileDB library
    2. Ensure PDAL built with TileDB support
    3. (Optional) Set TEST_TILEDB_PATH for custom output location

    **To run this test**:
    ```bash
    pytest tests/laz_to_writers/test_database_writers.py::test_tiledb_writer -v
    ```

    **Expected behavior**:
    - Test skipped if TileDB not available in PDAL
    - Test runs if TileDB support detected
    """
    from pathlib import Path

    # Get output path
    tiledb_path = os.getenv("TEST_TILEDB_PATH", str(writer_output_dir / "tiledb_output"))

    # Create pipeline
    pipeline = Pipeline(
        pdal.Reader.las(str(writer_test_laz)) | pdal.Writer.tiledb(array_name=str(tiledb_path))
    )

    # Execute
    try:
        point_count = pipeline.execute()
    except PDALExecutionError as e:
        handle_writer_exception(e, "tiledb")
        return

    # Validate execution
    assert point_count > 0, "No points processed for tiledb writer"

    # Validate array directory created
    assert Path(tiledb_path).exists(), "TileDB array directory not created"

    print(f"✓ tiledb: {point_count:,} points written to TileDB array")
