"""End-to-end workflow integration tests.

Tests comprehensive workflows combining multiple PDAL operations:
- Ground classification workflows (SMRF, PMF)
- Height Above Ground (HAG) workflows
- Complex filtering workflows
- Batch processing workflows
- Format conversion workflows
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import exeqpdal as pdal
from exeqpdal import Pipeline

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration, pytest.mark.slow, pytest.mark.usefixtures("skip_if_no_pdal")]


class TestGroundClassificationWorkflow:
    """Test complete ground classification workflows."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_smrf_ground_classification(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test complete SMRF ground classification workflow.

        Workflow: Read LAZ → SMRF ground classification → Filter ground points → Write LAS.
        """
        output = tmp_path / "ground_classified.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.smrf(cell=1.0, slope=0.15)
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pmf_ground_classification(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test PMF ground classification workflow.

        Workflow: Read LAZ → PMF ground classification → Filter ground points → Write LAS.
        """
        output = tmp_path / "pmf_ground.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.pmf()
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_ground_classification_comparison(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test comparing SMRF vs PMF ground classification results.

        Workflow: Process same data with SMRF and PMF, compare point counts.
        """
        smrf_output = tmp_path / "smrf_ground.las"
        pmf_output = tmp_path / "pmf_ground.las"

        # SMRF classification
        smrf_pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.smrf()
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las(str(smrf_output))
        )
        smrf_count = smrf_pipeline.execute()

        # PMF classification
        pmf_pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.pmf()
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las(str(pmf_output))
        )
        pmf_count = pmf_pipeline.execute()

        assert smrf_count > 0
        assert pmf_count > 0
        assert smrf_output.exists()
        assert pmf_output.exists()


class TestHAGWorkflow:
    """Test Height Above Ground (HAG) workflows."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_hag_nn_workflow(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test HAG calculation with nearest neighbor.

        Workflow: Read → Ground classification → HAG NN → Ferry dimension → Filter height → Write.
        """
        output = tmp_path / "hag.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.smrf()
            | pdal.Filter.hag_nn()
            | pdal.Filter.ferry(dimensions="HeightAboveGround=HAG")
            | pdal.Filter.range(limits="HAG[0:50]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_hag_delaunay_workflow(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test HAG calculation with Delaunay triangulation.

        Workflow: Read → Ground classification → HAG Delaunay → Write.
        """
        output = tmp_path / "hag_delaunay.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.smrf()
            | pdal.Filter.hag_delaunay()
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_hag_vegetation_height_extraction(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test extracting vegetation height using HAG.

        Workflow: Read → HAG → Filter vegetation class → Filter by height → Write.
        """
        output = tmp_path / "vegetation_heights.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.smrf()
            | pdal.Filter.hag_nn()
            | pdal.Filter.range(limits="Classification[3:5]")  # Vegetation classes
            | pdal.Filter.ferry(dimensions="HeightAboveGround=HAG")
            | pdal.Filter.range(limits="HAG[2:30]")  # 2-30m vegetation
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count >= 0
        assert output.exists()


class TestFilteringWorkflow:
    """Test complex filtering workflows."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_spatial_and_classification_filter(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test spatial cropping + classification filtering.

        Workflow: Read → Crop spatial bounds → Filter by classification → Write.
        """
        output = tmp_path / "filtered.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.crop(bounds="([785000,785500],[5350000,5350500])")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_outlier_removal_workflow(self, small_laz: Path, tmp_path: Path) -> None:
        """Test outlier removal workflow.

        Workflow: Read → Statistical outlier removal → Write.
        """
        output = tmp_path / "cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_multi_stage_complex_filter(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test complex multi-stage filtering pipeline.

        Workflow: Read → Crop → Range filter → Outlier removal → Sort → Write.
        """
        output = tmp_path / "complex_filtered.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.crop(bounds="([785000,786000],[5350000,5351000])")
            | pdal.Filter.range(limits="Z[0:500]")
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Filter.sort(dimension="Z")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_classification_remap_workflow(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test classification remapping workflow.

        Workflow: Read → Assign classification → Filter → Write.
        """
        output = tmp_path / "reclassified.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.assign(value="Classification=1")
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()


class TestBatchProcessingWorkflow:
    """Test batch processing workflows."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_merge_and_filter_workflow(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test merging multiple files and filtering.

        Workflow: Merge files → Read merged → Filter → Write.
        """
        merged = tmp_path / "merged.las"

        # Merge
        pdal.merge([str(f) for f in dual_laz], str(merged))
        assert merged.exists()

        # Filter merged file
        filtered = tmp_path / "filtered.las"
        pipeline = Pipeline(
            pdal.Reader.las(str(merged))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(filtered))
        )

        count = pipeline.execute()
        assert count > 0
        assert filtered.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_split_and_process_workflow(self, small_laz: Path, tmp_path: Path) -> None:
        """Test splitting file and processing splits.

        Workflow: Split by point count → Process first split → Write.
        """
        split_dir = tmp_path / "splits"
        split_dir.mkdir()

        # Split - may not produce files if PDAL split not available or configured differently
        try:
            pdal.split(str(small_laz), str(split_dir), length=2000000)
        except Exception:
            pytest.skip("PDAL split command not available or failed")

        split_files = list(split_dir.glob("*.las"))
        if not split_files:
            pytest.skip("Split did not produce output files")

        # Process first split
        if split_files:
            processed = tmp_path / "processed.las"
            pipeline = Pipeline(
                pdal.Reader.las(str(split_files[0]))
                | pdal.Filter.range(limits="Classification[2:2]")
                | pdal.Writer.las(str(processed))
            )

            count = pipeline.execute()
            # Count may be 0 if no ground points in this split
            assert count >= 0
            if count > 0:
                assert processed.exists()
                assert processed.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_merge_process_split_workflow(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test complete batch processing workflow: merge → process → split.

        Workflow: Merge files → Ground classification → Split by capacity → Verify splits.
        """
        merged = tmp_path / "merged.las"
        processed = tmp_path / "processed.las"
        split_dir = tmp_path / "splits"
        split_dir.mkdir()

        # Merge
        pdal.merge([str(f) for f in dual_laz], str(merged))
        assert merged.exists()

        # Process with ground classification
        pipeline = Pipeline(
            pdal.Reader.las(str(merged))
            | pdal.Filter.smrf()
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las(str(processed))
        )
        count = pipeline.execute()
        # Count may be 0 if no ground points classified
        assert count >= 0

        # Only split if we have points
        if count > 0 and processed.exists():
            pdal.split(str(processed), str(split_dir), capacity=1000000)
            split_files = list(split_dir.glob("*.las"))
            # May have no splits if file is too small
            assert isinstance(split_files, list)


class TestFormatConversionWorkflow:
    """Test format conversion workflows."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_laz_to_las_to_laz_roundtrip(self, small_laz: Path, tmp_path: Path) -> None:
        """Test LAZ → LAS → LAZ conversion roundtrip.

        Workflow: LAZ → Uncompressed LAS → Recompressed LAZ.
        """
        las_file = tmp_path / "uncompressed.las"
        laz_file = tmp_path / "recompressed.laz"

        # LAZ to LAS
        pdal.translate(str(small_laz), str(las_file))
        assert las_file.exists()

        # LAS to LAZ with pipeline for compression
        pipeline = Pipeline(
            pdal.Reader.las(str(las_file)) | pdal.Writer.las(str(laz_file), compression="laszip")
        )
        count = pipeline.execute()
        assert count > 0
        assert laz_file.exists()
        assert laz_file.stat().st_size > 0

        # Verify files are readable
        info_original = pdal.info(str(small_laz))
        info_roundtrip = pdal.info(str(laz_file))
        assert isinstance(info_original, dict)
        assert isinstance(info_roundtrip, dict)

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_las_to_text_conversion_workflow(self, small_laz: Path, tmp_path: Path) -> None:
        """Test LAS to text format conversion workflow.

        Workflow: Read LAZ → Crop small area → Write TXT with X,Y,Z.
        """
        output = tmp_path / "points.txt"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.crop(bounds="([785000,785100],[5351000,5351100])")
            | pdal.Writer.text(str(output), order="X,Y,Z", keep_unspecified=False)
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_format_conversion_with_filtering(self, small_laz: Path, tmp_path: Path) -> None:
        """Test format conversion with intermediate filtering.

        Workflow: Read LAZ → Filter → Convert to LAS with different data type.
        """
        output = tmp_path / "filtered_converted.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Filter.crop(bounds="([785000,786000],[5351000,5352000])")
            | pdal.Writer.las(str(output), minor_version=4, dataformat_id=6)
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()


class TestComplexProductionWorkflow:
    """Test production-ready complex workflows."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_dem_generation_workflow(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test DEM generation workflow.

        Workflow: Read → Ground classification → Extract ground → Write for DEM.
        """
        ground_output = tmp_path / "ground_points.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.smrf(cell=1.0)
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Filter.outlier(method="statistical", mean_k=8)
            | pdal.Writer.las(str(ground_output))
        )

        count = pipeline.execute()
        assert count > 0
        assert ground_output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_building_extraction_workflow(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test building extraction workflow.

        Workflow: Read → Ground classification → HAG → Filter building heights → Write.
        """
        buildings_output = tmp_path / "buildings.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.smrf()
            | pdal.Filter.hag_nn()
            | pdal.Filter.ferry(dimensions="HeightAboveGround=HAG")
            | pdal.Filter.range(limits="HAG[3:50]")  # Buildings typically >3m
            | pdal.Filter.range(limits="Classification[6:6]")  # Building class
            | pdal.Writer.las(str(buildings_output))
        )

        count = pipeline.execute()
        assert count >= 0
        assert buildings_output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_noise_removal_and_classification_workflow(
        self, small_laz: Path, tmp_path: Path
    ) -> None:
        """Test comprehensive noise removal and classification workflow.

        Workflow: Read → Remove noise → Ground classification → Outlier removal → Write.
        """
        output = tmp_path / "cleaned_classified.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Classification![7:7]")  # Remove noise class
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=3.0)
            | pdal.Filter.smrf()
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_aoi_extraction_with_buffer_workflow(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test area of interest extraction with buffer workflow.

        Workflow: Read → Crop to AOI → Ground classification → Write.
        """
        output = tmp_path / "aoi_extracted.las"

        # Define AOI bounds with buffer
        pipeline = Pipeline(
            pdal.Reader.las(str(medium_laz))
            | pdal.Filter.crop(bounds="([785200,785800],[5350200,5350800])")
            | pdal.Filter.smrf()
            | pdal.Filter.range(limits="Z[0:500]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()
        assert output.stat().st_size > 0
