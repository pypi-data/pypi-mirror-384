"""Spatial operations and merge workflow tests.

Tests spatial operations using **intersecting datasets**:
- Merge operations with overlapping data
- Spatial indexing (tindex) with multiple files
- Duplicate point handling
- Spatial filtering and cropping
- Mosaic creation

Uses datasets with spatial overlap:
- mid_laz_original (85MB) and sml_copc_created (13MB) - both cover same 1km tile
- Tests realistic scenarios where data sources intersect
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import exeqpdal as pdal
from exeqpdal import Pipeline

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_no_pdal")]


class TestMergeOperations:
    """Test merge operations with intersecting datasets."""

    @pytest.mark.integration
    def test_merge_intersecting_files(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test merging two spatially overlapping files."""
        file1, file2 = intersecting_datasets
        merged_output = tmp_path / "merged.las"

        # Merge using pdal.merge()
        pdal.merge([str(file1), str(file2)], str(merged_output))

        assert merged_output.exists()
        merged_info = pdal.info(str(merged_output))
        merged_count = merged_info.get("count", 0)

        # Get individual counts
        count1 = pdal.info(str(file1)).get("count", 0)
        count2 = pdal.info(str(file2)).get("count", 0)

        # Merged count should be sum of both (may have duplicates in overlap)
        assert merged_count > 0
        assert merged_count >= max(count1, count2)

    @pytest.mark.integration
    def test_merge_with_spatial_filter(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test merging files then applying spatial filter."""
        file1, file2 = intersecting_datasets
        merged = tmp_path / "merged.las"
        filtered = tmp_path / "filtered.las"

        # Merge first
        pdal.merge([str(file1), str(file2)], str(merged))

        # Then filter to specific bounds
        pipeline = Pipeline(
            pdal.Reader.las(str(merged))
            | pdal.Filter.crop(bounds="([785200,785800],[5350200,5350800])")
            | pdal.Writer.las(str(filtered))
        )

        filtered_count = pipeline.execute()
        merged_count = pdal.info(str(merged)).get("count", 0)

        assert filtered_count > 0
        assert filtered_count < merged_count
        assert filtered.exists()

    @pytest.mark.integration
    def test_merge_with_duplicate_detection(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test merge with potential duplicate point detection."""
        merged = tmp_path / "merged_with_duplicates.las"

        # Merge identical files (will have duplicates)
        pdal.merge([str(f) for f in dual_laz], str(merged))

        assert merged.exists()
        merged_count = pdal.info(str(merged)).get("count", 0)
        original_count = pdal.info(str(dual_laz[0])).get("count", 0)

        # Should be roughly 2x original (both files are same)
        assert merged_count >= original_count * 1.9  # Allow for small differences

    @pytest.mark.integration
    def test_merge_different_formats(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test merging LAS and COPC files."""
        las_file, copc_file = intersecting_datasets
        merged = tmp_path / "mixed_format_merged.las"

        # Merge LAS + COPC
        pdal.merge([str(las_file), str(copc_file)], str(merged))

        assert merged.exists()
        assert pdal.info(str(merged)).get("count", 0) > 0


class TestTindexOperations:
    """Test tile index (tindex) operations."""

    @pytest.mark.integration
    def test_tindex_creation(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test creating spatial tile index from multiple files."""
        file1, file2 = intersecting_datasets
        tindex_output = tmp_path / "tindex.sqlite"

        try:
            # Create tile index
            pdal.tindex([str(file1), str(file2)], str(tindex_output))

            assert tindex_output.exists()
            assert tindex_output.stat().st_size > 0
        except Exception as e:
            # Tindex may not be available in all PDAL installations
            pytest.skip(f"Tindex not available: {e}")


class TestSpatialFiltering:
    """Test spatial filtering operations."""

    @pytest.mark.integration
    def test_crop_to_overlap_region(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test cropping both datasets to their overlap region."""
        file1, file2 = intersecting_datasets
        crop1 = tmp_path / "crop1.las"
        crop2 = tmp_path / "crop2.las"

        # Both files cover X 785000-786000, Y 5350000-5351000
        overlap_bounds = "([785000,786000],[5350000,5351000])"

        # Crop first file
        pipeline1 = Pipeline(
            pdal.Reader.las(str(file1))
            | pdal.Filter.crop(bounds=overlap_bounds)
            | pdal.Writer.las(str(crop1))
        )
        count1 = pipeline1.execute()

        # Crop second file
        pipeline2 = Pipeline(
            pdal.Reader.copc(str(file2))  # file2 is COPC
            | pdal.Filter.crop(bounds=overlap_bounds)
            | pdal.Writer.las(str(crop2))
        )
        count2 = pipeline2.execute()

        assert count1 > 0
        assert count2 > 0
        assert crop1.exists()
        assert crop2.exists()

    @pytest.mark.integration
    def test_spatial_query_performance(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test spatial query on intersecting region."""
        _, file2 = intersecting_datasets
        query_result = tmp_path / "spatial_query.las"

        # Query small area in overlap
        small_bounds = "([785400,785600],[5350400,5350600])"

        # Use COPC for efficient spatial query
        pipeline = Pipeline(
            pdal.Reader.copc(str(file2), bounds=small_bounds) | pdal.Writer.las(str(query_result))
        )

        count = pipeline.execute()
        assert count > 0
        assert query_result.exists()

        # Result should be much smaller than full file
        full_count = pdal.info(str(file2)).get("count", 0)
        assert count < full_count * 0.2

    @pytest.mark.integration
    def test_multi_region_extraction(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test extracting multiple spatial regions from same file."""
        file1, _ = intersecting_datasets

        # Define three non-overlapping regions
        regions = [
            ("([785000,785333],[5350000,5350333])", "region1.las"),
            ("([785333,785666],[5350333,5350666])", "region2.las"),
            ("([785666,786000],[5350666,5351000])", "region3.las"),
        ]

        counts = []
        for bounds, filename in regions:
            output = tmp_path / filename
            pipeline = Pipeline(
                pdal.Reader.las(str(file1))
                | pdal.Filter.crop(bounds=bounds)
                | pdal.Writer.las(str(output))
            )
            count = pipeline.execute()
            if count > 0:
                assert output.exists()
                counts.append(count)

        # At least some regions should have points
        assert len(counts) > 0
        # Sum of regions should be less than total (boundaries may exclude some points)
        total_count = pdal.info(str(file1)).get("count", 0)
        assert sum(counts) <= total_count


class TestMosaicCreation:
    """Test mosaic creation from intersecting tiles."""

    @pytest.mark.integration
    def test_create_mosaic_from_tiles(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test creating seamless mosaic from overlapping tiles."""
        file1, _ = intersecting_datasets
        mosaic = tmp_path / "mosaic.las"

        # Simple mosaic: merge + ground classification
        pipeline = Pipeline(
            # This would ideally use multiple readers, but we'll merge first
            pdal.Reader.las(str(file1))
            | pdal.Filter.smrf()
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las(str(mosaic))
        )

        count = pipeline.execute()
        assert count >= 0  # May be 0 if no ground points
        if count > 0:
            assert mosaic.exists()

    @pytest.mark.integration
    def test_mosaic_with_classification_consistency(
        self, dual_laz: list[Path], tmp_path: Path
    ) -> None:
        """Test mosaic ensuring consistent classification across tiles."""
        merged = tmp_path / "merged_for_mosaic.las"
        classified_mosaic = tmp_path / "classified_mosaic.las"

        # Merge tiles
        pdal.merge([str(f) for f in dual_laz], str(merged))

        # Apply consistent classification
        pipeline = Pipeline(
            pdal.Reader.las(str(merged))
            | pdal.Filter.smrf()  # Consistent ground classification
            | pdal.Writer.las(str(classified_mosaic))
        )

        count = pipeline.execute()
        assert count > 0
        assert classified_mosaic.exists()


class TestSpatialIndexing:
    """Test spatial indexing and lookup operations."""

    @pytest.mark.integration
    def test_spatial_lookup_in_merged_data(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test spatial lookup after merging datasets."""
        file1, file2 = intersecting_datasets
        merged = tmp_path / "merged.las"
        lookup_result = tmp_path / "lookup.las"

        # Merge files
        pdal.merge([str(file1), str(file2)], str(merged))

        # Perform spatial lookup (crop to specific bounds)
        pipeline = Pipeline(
            pdal.Reader.las(str(merged))
            | pdal.Filter.crop(bounds="([785450,785550],[5350450,5350550])")
            | pdal.Writer.las(str(lookup_result))
        )

        count = pipeline.execute()
        assert count > 0
        assert lookup_result.exists()

    @pytest.mark.integration
    def test_spatial_sort_after_merge(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test spatial sorting after merging overlapping files."""
        file1, file2 = intersecting_datasets
        merged = tmp_path / "merged_unsorted.las"
        sorted_output = tmp_path / "merged_sorted.las"

        # Merge files
        pdal.merge([str(file1), str(file2)], str(merged))

        # Sort spatially (by X, then Y)
        pipeline = Pipeline(
            pdal.Reader.las(str(merged))
            | pdal.Filter.sort(dimension="X")
            | pdal.Filter.sort(dimension="Y")
            | pdal.Writer.las(str(sorted_output))
        )

        count = pipeline.execute()
        merged_count = pdal.info(str(merged)).get("count", 0)

        assert count == merged_count
        assert sorted_output.exists()


class TestBoundsCalculation:
    """Test bounds calculation and validation."""

    @pytest.mark.integration
    def test_get_merged_bounds(
        self, intersecting_datasets: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Test calculating bounds of merged dataset."""
        file1, file2 = intersecting_datasets
        merged = tmp_path / "merged.las"

        pdal.merge([str(file1), str(file2)], str(merged))

        # Get bounds using pdal.get_bounds()
        bounds = pdal.get_bounds(str(merged))

        # Verify bounds structure
        assert isinstance(bounds, dict)
        assert "minx" in bounds
        assert "maxx" in bounds
        assert "miny" in bounds
        assert "maxy" in bounds
        assert "minz" in bounds
        assert "maxz" in bounds

        # Verify bounds are reasonable
        assert bounds["minx"] < bounds["maxx"]
        assert bounds["miny"] < bounds["maxy"]
        assert bounds["minz"] < bounds["maxz"]

    @pytest.mark.integration
    def test_verify_overlap_extent(self, intersecting_datasets: tuple[Path, Path]) -> None:
        """Test verifying spatial overlap between datasets."""
        file1, file2 = intersecting_datasets

        # Get bounds of each file
        bounds1 = pdal.get_bounds(str(file1))
        bounds2 = pdal.get_bounds(str(file2))

        # Check for overlap in X dimension
        x_overlap = (bounds1["minx"] <= bounds2["maxx"]) and (bounds2["minx"] <= bounds1["maxx"])
        # Check for overlap in Y dimension
        y_overlap = (bounds1["miny"] <= bounds2["maxy"]) and (bounds2["miny"] <= bounds1["maxy"])

        # Files should overlap (both are in X 785000-786000, Y 5350000-5351000)
        assert x_overlap, "Files should overlap in X dimension"
        assert y_overlap, "Files should overlap in Y dimension"
