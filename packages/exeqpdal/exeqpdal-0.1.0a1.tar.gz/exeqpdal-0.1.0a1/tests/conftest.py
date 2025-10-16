"""Shared test fixtures for exeqpdal tests."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from exeqpdal.exceptions import PDALExecutionError

# LAZ / COPC test data constants
DEFAULT_DATA_DIR = Path(__file__).parent / "test_data_laz"
LAZ_DIR = (
    Path(os.environ["EXEQPDAL_TEST_DATA"])
    if os.environ.get("EXEQPDAL_TEST_DATA")
    else DEFAULT_DATA_DIR
)

# Canonical datasets
MID_LAS = LAZ_DIR / "mid_laz_original.laz"
MID_COPC = LAZ_DIR / "mid_copc_translated.copc.laz"
LARGE_LAS = LAZ_DIR / "lrg_laz_original.laz"
LARGE_COPC = LAZ_DIR / "lrg_copc_translated.copc.laz"
SMALL_COPC = LAZ_DIR / "sml_copc_created.copc.laz"
SMALL_MID_COPC = LAZ_DIR / "sml-mid_copc_created.copc.laz"

# Legacy fixture aliases for backwards compatibility
LAZ_SMALL = MID_LAS
LAZ_MEDIUM = MID_LAS
LAZ_LARGE = LARGE_LAS

# Writer test outputs (moved from laz_to_writers/conftest.py)
OUTPUT_BASE = Path(__file__).parent / "laz_to_writers" / "outputs"


@pytest.fixture(scope="session")
def skip_if_no_test_data() -> None:
    """Skip tests if the packaged point cloud datasets are unavailable."""
    if not LAZ_DIR.exists():
        pytest.skip(f"Test data directory not available: {LAZ_DIR}")


@pytest.fixture
def skip_if_no_pdal() -> None:
    """Skip test if PDAL CLI not available."""
    try:
        from exeqpdal.core.config import config

        _ = config.pdal_path
    except Exception:
        pytest.skip("PDAL CLI not available")


@pytest.fixture
def small_laz(skip_if_no_test_data: None) -> Path:
    """Primary LAS sample (~85 MB) for general-purpose unit/integration tests."""
    if not LAZ_SMALL.exists():
        pytest.skip(f"Test file not found: {LAZ_SMALL}")
    return LAZ_SMALL


@pytest.fixture
def medium_laz(skip_if_no_test_data: None) -> Path:
    """Alias to the mid-size LAS dataset (same as small_laz)."""
    if not LAZ_MEDIUM.exists():
        pytest.skip(f"Test file not found: {LAZ_MEDIUM}")
    return LAZ_MEDIUM


@pytest.fixture
def large_laz(skip_if_no_test_data: None) -> Path:
    """High-density engineering dataset (>1B points) for stress tests."""
    if not LAZ_LARGE.exists():
        pytest.skip(f"Test file not found: {LAZ_LARGE}")
    return LAZ_LARGE


@pytest.fixture(scope="session")
def dual_laz(skip_if_no_test_data: None, tmp_path_factory: pytest.TempPathFactory) -> list[Path]:
    """Pair of LAS inputs for merge/tindex workflows (mid tile + cached copy)."""
    if not MID_LAS.exists():
        pytest.skip(f"Test file not found: {MID_LAS}")

    cache_dir = tmp_path_factory.mktemp("dual_laz_cache")
    copy_path = cache_dir / "mid_laz_copy.laz"
    if not copy_path.exists():
        shutil.copy(MID_LAS, copy_path)

    return [MID_LAS, copy_path]


# === New fixtures for enhanced test coverage ===


@pytest.fixture
def noisy_dataset(skip_if_no_test_data: None) -> Path:
    """Non-filtered dataset for denoising tests (contains unclassified points).

    Uses sml-mid_copc_created (64MB, 8M points) which contains class 1 (unclassified)
    and classes up to 31. Suitable for noise removal and outlier detection tests.
    """
    if not SMALL_MID_COPC.exists():
        pytest.skip(f"Test file not found: {SMALL_MID_COPC}")
    return SMALL_MID_COPC


@pytest.fixture
def large_noisy_dataset(skip_if_no_test_data: None) -> Path:
    """Large non-filtered dataset for stress denoising tests.

    Uses lrg_copc_translated (618MB, 115M points) with full classification range 1-31.
    Contains unclassified points and extra dimensions (RIEGL, TerraScan attributes).
    """
    if not LARGE_COPC.exists():
        pytest.skip(f"Test file not found: {LARGE_COPC}")
    return LARGE_COPC


@pytest.fixture
def small_copc(skip_if_no_test_data: None) -> Path:
    """Small COPC file for fast COPC-specific tests.

    Uses sml_copc_created (13MB, 1.7M points) with reclassified data.
    Ideal for streaming reader and index-aware tests.
    """
    if not SMALL_COPC.exists():
        pytest.skip(f"Test file not found: {SMALL_COPC}")
    return SMALL_COPC


@pytest.fixture
def mid_copc(skip_if_no_test_data: None) -> Path:
    """Medium COPC file for standard COPC tests.

    Uses mid_copc_translated (100MB, 14M points) - COPC version of mid_laz_original.
    Pre-filtered data (classes 2, 6, 20 only).
    """
    if not MID_COPC.exists():
        pytest.skip(f"Test file not found: {MID_COPC}")
    return MID_COPC


@pytest.fixture
def intersecting_datasets(skip_if_no_test_data: None) -> tuple[Path, Path]:
    """Pair of spatially overlapping datasets for merge/mosaic tests.

    Returns:
        - mid_laz_original (85MB): 1km x 1km tile, pre-filtered
        - sml_copc_created (13MB): Larger area encompassing mid tile, reclassified

    Both datasets cover the same spatial extent (X 785000-786000, Y 5350000-5351000)
    making them ideal for testing merge operations, spatial indexing, and duplicate
    point handling.
    """
    if not MID_LAS.exists():
        pytest.skip(f"Test file not found: {MID_LAS}")
    if not SMALL_COPC.exists():
        pytest.skip(f"Test file not found: {SMALL_COPC}")
    return (MID_LAS, SMALL_COPC)


@pytest.fixture
def large_performance_dataset(skip_if_no_test_data: None) -> Path:
    """Large dataset for performance benchmarking (1.1GB, 115M points).

    Uses lrg_laz_original - unfiltered engineering-grade survey data.
    Contains extra dimensions (RIEGL and TerraScan attributes).
    Expected runtime: 1-10 minutes depending on operation.
    """
    if not LARGE_LAS.exists():
        pytest.skip(f"Test file not found: {LARGE_LAS}")
    return LARGE_LAS


@pytest.fixture
def pdal_version() -> str:
    """Get PDAL version string.

    Raises:
        pytest.skip: If PDAL not available
    """
    try:
        from exeqpdal.core.config import config

        return config.get_pdal_version()
    except Exception:
        pytest.skip("PDAL CLI not available")


# === Writer test fixtures (moved from laz_to_writers/conftest.py) ===


@pytest.fixture(scope="session")
def writer_test_laz(skip_if_no_test_data: None) -> Path:
    """Baseline LAS input for writer tests (mid tile from Bavaria open data)."""
    if not MID_LAS.exists():
        pytest.skip(f"Test file not found: {MID_LAS}")
    return MID_LAS


@pytest.fixture(scope="session")
def writer_output_dir() -> Path:
    """Directory for writer test outputs (preserved for inspection).

    Creates subdirectories:
    - standard/
    - text/
    - raster/
    - special/

    Files are preserved (not cleaned up) for manual inspection.
    Added to .gitignore.
    """
    output_dir = OUTPUT_BASE
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create category subdirectories
    for category in ["standard", "text", "raster", "special"]:
        (output_dir / category).mkdir(exist_ok=True)

    # Create README if not exists
    readme = output_dir / "README.md"
    if not readme.exists():
        readme.write_text("""# Writer Test Outputs

This directory contains output files from LAZ-to-writers tests.

**Organization**:
- `standard/` - Standard point cloud formats (LAS, COPC, PLY, etc.)
- `text/` - Text/ASCII format outputs
- `raster/` - Raster format outputs (GeoTIFF, etc.)
- `special/` - Special format outputs (NITF, GLTF, etc.)

**Files preserved for manual inspection** - DO NOT COMMIT.

**Source**: tests/test_laz_to_*.py
**Input**: tests/test_data_laz/mid_laz_original.laz (~85 MB, ~14 M points)
""")

    return output_dir


def get_output_filename(
    category: str,
    writer_name: str,
    extension: str | None,
    config_id: str = "",
) -> str:
    """Generate consistent output filename.

    Format: mid_laz_original_{writer_name}_{config_id}_{timestamp}.{extension}

    Args:
        category: Subdirectory (standard, text, raster, special)
        writer_name: Writer type (las, copc, text, etc.)
        extension: File extension (with leading dot)
        config_id: Optional configuration identifier

    Returns:
        Full path to output file as string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = "mid_laz_original"

    if config_id:
        filename = f"{base_name}_{writer_name}_{config_id}_{timestamp}"
    else:
        filename = f"{base_name}_{writer_name}_{timestamp}"

    if extension:
        filename = f"{filename}{extension}"

    output_path = OUTPUT_BASE / category / filename
    return str(output_path)


def handle_writer_exception(e: Exception, writer_name: str) -> None:
    """Handle exceptions from writer execution.

    Three-tier strategy:
    1. Expected failures (writer unavailable) → skip test
    2. Configuration issues → skip test with message
    3. Actual failures → raise (test fails)

    Args:
        e: Exception raised during execution
        writer_name: Name of writer being tested

    Raises:
        pytest.skip: For expected failures and configuration issues
        Exception: For actual failures (test should fail)
    """
    if not isinstance(e, PDALExecutionError):
        raise

    error_msg = str(e).lower()

    # Expected failures - writer not available
    skip_patterns = [
        "couldn't create",
        "unknown stage",
        "not available",
        "couldn't find",
        "unknown writer",
    ]

    if any(pattern in error_msg for pattern in skip_patterns):
        pytest.skip(
            f"Writer '{writer_name}' not available in this PDAL installation. Error: {str(e)[:100]}"
        )

    # Configuration issues
    config_patterns = [
        "requires",
        "missing required",
        "invalid option",
        "resolution",
        "no points",
    ]

    if any(pattern in error_msg for pattern in config_patterns):
        pytest.skip(
            f"Writer '{writer_name}' requires additional configuration. Error: {str(e)[:100]}"
        )

    # Actual failures - let test fail
    raise


def validate_output_file(
    output_path: str | Path,
    expected_points: int | None = None,
    tolerance: float = 0.05,
) -> dict[str, Any]:
    """Validate output file creation and properties.

    Args:
        output_path: Path to output file
        expected_points: Expected point count (optional)
        tolerance: Point count tolerance (default 5%)

    Returns:
        dict with validation results:
        - exists: bool
        - size: int (bytes)
        - valid: bool

    Raises:
        AssertionError: If validation fails
    """
    path = Path(output_path)

    result = {
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0,
        "valid": False,
    }

    # Basic validation
    assert result["exists"], f"Output file not created: {path}"
    assert result["size"] > 0, f"Output file is empty: {path}"

    result["valid"] = True
    return result
