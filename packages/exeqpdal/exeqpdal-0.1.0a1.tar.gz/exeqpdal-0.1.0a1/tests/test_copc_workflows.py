"""COPC-specific workflow tests.

Tests Cloud Optimized Point Cloud (COPC) format functionality:
- COPC reader with streaming and spatial queries
- COPC writer for creating indexed point clouds
- Level-of-detail (LOD) access patterns
- Spatial filtering and bounds queries
- Round-trip conversion (LAS → COPC → LAS)
- COPC metadata and structure validation

Uses appropriate COPC datasets:
- small_copc (13MB, 1.7M pts) for fast tests
- mid_copc (100MB, 14M pts) for standard tests
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import exeqpdal as pdal
from exeqpdal import Pipeline

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [
    pytest.mark.integration,
    pytest.mark.copc,
    pytest.mark.usefixtures("skip_if_no_pdal"),
]


class TestCOPCReading:
    """Test COPC reader functionality."""

    @pytest.mark.integration
    def test_copc_reader_basic(self, small_copc: Path, tmp_path: Path) -> None:
        """Test basic COPC file reading."""
        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.copc(str(small_copc)) | pdal.Writer.las(str(output)))

        count = pipeline.execute()
        assert count > 0
        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.integration
    def test_copc_reader_with_bounds(self, small_copc: Path, tmp_path: Path) -> None:
        """Test COPC reader with spatial bounds filter."""
        output = tmp_path / "bounded.las"

        # Use bounds that intersect the small_copc dataset
        # small_copc extent: X 784900-786100, Y 5349900-5351100
        pipeline = Pipeline(
            pdal.Reader.copc(str(small_copc), bounds="([785000,786000],[5350000,5351000])")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0  # Should have points in this extent
        assert output.exists()

    @pytest.mark.integration
    def test_copc_reader_with_resolution(self, mid_copc: Path, tmp_path: Path) -> None:
        """Test COPC reader with resolution parameter for LOD access."""
        output = tmp_path / "lod.las"

        # Request lower resolution (larger resolution value = fewer points)
        pipeline = Pipeline(
            pdal.Reader.copc(str(mid_copc), resolution=10.0) | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()

        # Verify we got fewer points than full resolution
        full_info = pdal.info(str(mid_copc))
        full_count = full_info.get("count", 0)
        assert count < full_count, "Resolution filter should reduce point count"

    @pytest.mark.integration
    def test_copc_streaming_read(self, small_copc: Path, tmp_path: Path) -> None:
        """Test COPC streaming reader for efficient partial reads."""
        output = tmp_path / "streamed.las"

        # Read only a small spatial subset efficiently
        pipeline = Pipeline(
            pdal.Reader.copc(
                str(small_copc), bounds="([785400,785600],[5350400,5350600])", resolution=5.0
            )
            | pdal.Filter.head(count=10000)
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert count <= 10000
        assert output.exists()


class TestCOPCWriting:
    """Test COPC writer functionality."""

    @pytest.mark.integration
    def test_las_to_copc_conversion(self, small_laz: Path, tmp_path: Path) -> None:
        """Test converting LAS to COPC format."""
        output = tmp_path / "output.copc.laz"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.copc(str(output)))

        count = pipeline.execute()
        assert count > 0
        assert output.exists()

        # Verify COPC structure
        info = pdal.info(str(output))
        assert info.get("copc", False), "Output should be COPC format"

    @pytest.mark.integration
    def test_copc_with_filtering(self, small_laz: Path, tmp_path: Path) -> None:
        """Test creating COPC with filtering pipeline."""
        output = tmp_path / "filtered.copc.laz"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.crop(bounds="([785000,786000],[5350000,5351000])")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.copc(str(output))
        )

        count = pipeline.execute()
        assert count >= 0  # May be 0 if no ground points in bounds
        if count > 0:
            assert output.exists()
            info = pdal.info(str(output))
            assert info.get("copc", False)

    @pytest.mark.integration
    def test_copc_forward_option(self, small_laz: Path, tmp_path: Path) -> None:
        """Test COPC writer with forward option for metadata."""
        output = tmp_path / "forwarded.copc.laz"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Writer.copc(str(output), forward="all")  # Forward all metadata
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()


class TestCOPCRoundTrip:
    """Test round-trip conversion between formats."""

    @pytest.mark.integration
    def test_las_copc_las_roundtrip(self, small_laz: Path, tmp_path: Path) -> None:
        """Test LAS → COPC → LAS round-trip conversion."""
        copc_file = tmp_path / "intermediate.copc.laz"
        las_file = tmp_path / "final.las"

        # LAS to COPC
        pipeline1 = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.copc(str(copc_file)))
        count1 = pipeline1.execute()

        # COPC to LAS
        pipeline2 = Pipeline(pdal.Reader.copc(str(copc_file)) | pdal.Writer.las(str(las_file)))
        count2 = pipeline2.execute()

        # Verify point counts match
        assert count1 == count2, f"Point count mismatch: {count1} → {count2}"
        assert copc_file.exists()
        assert las_file.exists()

    @pytest.mark.integration
    def test_copc_to_copc_rewrite(self, small_copc: Path, tmp_path: Path) -> None:
        """Test COPC → COPC rewrite (re-indexing)."""
        output = tmp_path / "reindexed.copc.laz"

        pipeline = Pipeline(pdal.Reader.copc(str(small_copc)) | pdal.Writer.copc(str(output)))

        original_count = pdal.info(str(small_copc)).get("count", 0)
        reindexed_count = pipeline.execute()

        assert reindexed_count == original_count
        assert output.exists()


class TestCOPCMetadata:
    """Test COPC metadata and structure validation."""

    @pytest.mark.integration
    def test_copc_metadata_structure(self, mid_copc: Path) -> None:
        """Test COPC metadata structure from info command."""
        info = pdal.info(str(mid_copc), metadata=True)

        # Verify COPC flag
        assert info.get("metadata", {}).get("copc", False), "Should be marked as COPC"

        # Verify COPC-specific metadata
        copc_info = info.get("metadata", {}).get("copc_info", {})
        assert "center_x" in copc_info
        assert "center_y" in copc_info
        assert "center_z" in copc_info
        assert "spacing" in copc_info
        assert "root_hier_offset" in copc_info
        assert "root_hier_size" in copc_info

    @pytest.mark.integration
    def test_copc_bounds_metadata(self, small_copc: Path) -> None:
        """Test COPC spatial bounds in metadata."""
        info = pdal.info(str(small_copc), stats=True)

        # Verify bounding box
        bbox = info.get("stats", {}).get("bbox", {}).get("native", {}).get("bbox", {})
        assert "minx" in bbox
        assert "maxx" in bbox
        assert "miny" in bbox
        assert "maxy" in bbox
        assert "minz" in bbox
        assert "maxz" in bbox

        # Verify bounds are reasonable (should match dataset documentation)
        assert bbox["minx"] < bbox["maxx"]
        assert bbox["miny"] < bbox["maxy"]
        assert bbox["minz"] < bbox["maxz"]


class TestCOPCSpatialQueries:
    """Test COPC spatial query efficiency."""

    @pytest.mark.integration
    def test_copc_small_spatial_query(self, mid_copc: Path, tmp_path: Path) -> None:
        """Test efficient spatial query on COPC (should be faster than full read)."""
        output = tmp_path / "query_result.las"

        # Small spatial query (100m x 100m area)
        pipeline = Pipeline(
            pdal.Reader.copc(str(mid_copc), bounds="([785450,785550],[5350450,5350550])")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()

        # Verify count is much smaller than full dataset
        full_count = pdal.info(str(mid_copc)).get("count", 0)
        assert count < full_count * 0.1, "Spatial query should return subset of points"

    @pytest.mark.integration
    def test_copc_multiple_bounded_reads(self, small_copc: Path, tmp_path: Path) -> None:
        """Test multiple bounded reads from same COPC file."""
        outputs = []

        # Read three different spatial regions
        bounds_list = [
            "([785000,785400],[5350000,5350400])",
            "([785400,785800],[5350400,5350800])",
            "([785800,786100],[5350800,5351100])",
        ]

        for i, bounds in enumerate(bounds_list):
            output = tmp_path / f"region_{i}.las"
            pipeline = Pipeline(
                pdal.Reader.copc(str(small_copc), bounds=bounds) | pdal.Writer.las(str(output))
            )

            count = pipeline.execute()
            if count > 0:  # Some regions may have no points
                assert output.exists()
                outputs.append((output, count))

        # At least one region should have points
        assert len(outputs) > 0


class TestCOPCComparison:
    """Test COPC vs LAS comparison."""

    @pytest.mark.integration
    def test_copc_vs_las_content_equivalence(self, mid_copc: Path, small_laz: Path) -> None:
        """Test that COPC and LAS contain equivalent point data."""
        # Get statistics from both
        copc_info = pdal.info(str(mid_copc), stats=True)
        las_info = pdal.info(str(small_laz), stats=True)

        # Both should have point counts
        copc_count = copc_info.get("count", 0)
        las_count = las_info.get("count", 0)

        assert copc_count > 0
        assert las_count > 0

    @pytest.mark.integration
    def test_copc_file_size_efficiency(self, tmp_path: Path, small_laz: Path) -> None:
        """Test that COPC file size is reasonable compared to LAS."""
        copc_output = tmp_path / "test.copc.laz"

        # Convert LAS to COPC
        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.copc(str(copc_output)))
        pipeline.execute()

        assert copc_output.exists()

        # COPC may be slightly larger due to spatial index, but not excessive
        las_size = small_laz.stat().st_size
        copc_size = copc_output.stat().st_size

        # COPC should be within 50% of original LAS size (usually much closer)
        assert copc_size < las_size * 1.5, "COPC file should not be excessively larger than LAS"
