"""Denoising and outlier removal workflow tests.

Tests noise removal and outlier detection filters using **non-filtered datasets**:
- Statistical outlier removal (SOR)
- Radius outlier removal
- Extended Local Minimum (ELM) filter for ground-level noise
- Combined denoising workflows
- Before/after comparisons

Uses appropriate non-filtered datasets:
- noisy_dataset (64MB, 8M pts, class 1-31) for standard tests
- large_noisy_dataset (618MB, 115M pts, class 1-31) for stress tests

Dataset characteristics:
- Contains unclassified points (class 1)
- Full classification range including noise (class 7)
- Suitable for realistic denoising scenarios
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
    pytest.mark.denoising,
    pytest.mark.usefixtures("skip_if_no_pdal"),
]


class TestStatisticalOutlierRemoval:
    """Test statistical outlier removal (SOR) filter."""

    @pytest.mark.integration
    def test_sor_basic(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test basic statistical outlier removal."""
        output = tmp_path / "sor_cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        cleaned_count = pipeline.execute()
        assert cleaned_count > 0
        assert output.exists()

        # Verify some points were marked as outliers
        original_count = pdal.info(str(noisy_dataset)).get("count", 0)
        assert cleaned_count < original_count, "Outlier filter should remove some points"

    @pytest.mark.integration
    def test_sor_parameter_comparison(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test SOR with different parameter sets."""
        # Conservative filtering (larger multiplier = fewer outliers removed)
        conservative_output = tmp_path / "conservative.las"
        conservative_pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=3.0)
            | pdal.Writer.las(str(conservative_output))
        )
        conservative_count = conservative_pipeline.execute()

        # Aggressive filtering (smaller multiplier = more outliers removed)
        aggressive_output = tmp_path / "aggressive.las"
        aggressive_pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=1.0)
            | pdal.Writer.las(str(aggressive_output))
        )
        aggressive_count = aggressive_pipeline.execute()

        # Aggressive should remove more points
        assert aggressive_count < conservative_count
        assert conservative_output.exists()
        assert aggressive_output.exists()

    @pytest.mark.integration
    def test_sor_with_classification_filtering(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test SOR combined with classification filtering."""
        output = tmp_path / "sor_classified.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            # Remove unclassified points first
            | pdal.Filter.range(limits="Classification![1:1]")
            # Then apply outlier removal
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()


class TestRadiusOutlierRemoval:
    """Test radius-based outlier removal."""

    @pytest.mark.integration
    def test_radius_outlier_basic(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test basic radius outlier removal."""
        output = tmp_path / "radius_cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.outlier(method="radius", radius=2.0, min_k=4)
            | pdal.Writer.las(str(output))
        )

        cleaned_count = pipeline.execute()
        assert cleaned_count > 0
        assert output.exists()

        # Verify outliers were removed
        original_count = pdal.info(str(noisy_dataset)).get("count", 0)
        assert cleaned_count < original_count

    @pytest.mark.integration
    def test_radius_parameter_variations(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test radius outlier removal with different parameters."""
        # Small radius (more aggressive)
        small_radius_output = tmp_path / "small_radius.las"
        small_pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.outlier(method="radius", radius=1.0, min_k=4)
            | pdal.Writer.las(str(small_radius_output))
        )
        small_count = small_pipeline.execute()

        # Large radius (more conservative)
        large_radius_output = tmp_path / "large_radius.las"
        large_pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.outlier(method="radius", radius=5.0, min_k=4)
            | pdal.Writer.las(str(large_radius_output))
        )
        large_count = large_pipeline.execute()

        # Smaller radius should be more aggressive
        assert small_count < large_count
        assert small_radius_output.exists()
        assert large_radius_output.exists()


class TestELMFilter:
    """Test Extended Local Minimum (ELM) filter for low-noise removal."""

    @pytest.mark.integration
    def test_elm_basic(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test basic ELM filter application."""
        output = tmp_path / "elm_filtered.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset)) | pdal.Filter.elm() | pdal.Writer.las(str(output))
        )

        filtered_count = pipeline.execute()
        assert filtered_count > 0
        assert output.exists()

        # ELM marks points as noise (class 7), doesn't remove them
        # So count should be similar to original
        original_count = pdal.info(str(noisy_dataset)).get("count", 0)
        assert filtered_count == original_count

    @pytest.mark.integration
    def test_elm_with_noise_removal(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test ELM filter followed by noise classification removal."""
        output = tmp_path / "elm_cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            # ELM marks ground-level noise as class 7
            | pdal.Filter.elm()
            # Remove noise classification
            | pdal.Filter.range(limits="Classification![7:7]")
            | pdal.Writer.las(str(output))
        )

        cleaned_count = pipeline.execute()
        assert cleaned_count > 0
        assert output.exists()

        # Should have removed some noise points
        original_count = pdal.info(str(noisy_dataset)).get("count", 0)
        assert cleaned_count < original_count, "ELM + range filter should remove noise points"

    @pytest.mark.integration
    def test_elm_with_parameters(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test ELM filter with custom parameters."""
        output = tmp_path / "elm_custom.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.elm(cell=10.0, threshold=1.0)
            | pdal.Filter.range(limits="Classification![7:7]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()


class TestCombinedDenoising:
    """Test combined denoising workflows."""

    @pytest.mark.integration
    def test_elm_plus_sor(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test ELM followed by statistical outlier removal."""
        output = tmp_path / "elm_sor_cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            # First: ELM for ground-level noise
            | pdal.Filter.elm()
            | pdal.Filter.range(limits="Classification![7:7]")
            # Second: Statistical outlier removal for aerial noise
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        cleaned_count = pipeline.execute()
        assert cleaned_count > 0
        assert output.exists()

        # Combined approach should remove more noise
        original_count = pdal.info(str(noisy_dataset)).get("count", 0)
        assert cleaned_count < original_count * 0.98, "Combined filtering should remove noise"

    @pytest.mark.integration
    def test_multi_pass_sor(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test multiple passes of statistical outlier removal."""
        output = tmp_path / "multi_pass_cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            # First pass: conservative
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=3.0)
            # Second pass: moderate
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        cleaned_count = pipeline.execute()
        assert cleaned_count > 0
        assert output.exists()

    @pytest.mark.integration
    def test_comprehensive_cleaning_workflow(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Test comprehensive cleaning: classification filter + ELM + SOR."""
        output = tmp_path / "comprehensive_cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            # Step 1: Remove existing noise classification
            | pdal.Filter.range(limits="Classification![7:7]")
            # Step 2: Remove unclassified points
            | pdal.Filter.range(limits="Classification![1:1]")
            # Step 3: ELM for ground noise
            | pdal.Filter.elm()
            | pdal.Filter.range(limits="Classification![7:7]")
            # Step 4: Statistical outlier removal
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        cleaned_count = pipeline.execute()
        assert cleaned_count > 0
        assert output.exists()

        # Comprehensive cleaning should significantly reduce point count
        original_count = pdal.info(str(noisy_dataset)).get("count", 0)
        removal_rate = (original_count - cleaned_count) / original_count
        assert removal_rate > 0.01, "Comprehensive cleaning should remove noise"


class TestDenoisingComparison:
    """Test comparing different denoising methods."""

    @pytest.mark.integration
    def test_sor_vs_radius_comparison(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Compare statistical vs radius outlier removal."""
        sor_output = tmp_path / "sor.las"
        radius_output = tmp_path / "radius.las"

        # Statistical outlier removal
        sor_pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(sor_output))
        )
        sor_count = sor_pipeline.execute()

        # Radius outlier removal
        radius_pipeline = Pipeline(
            pdal.Reader.copc(str(noisy_dataset))
            | pdal.Filter.outlier(method="radius", radius=2.0, min_k=4)
            | pdal.Writer.las(str(radius_output))
        )
        radius_count = radius_pipeline.execute()

        # Both should remove outliers
        original_count = pdal.info(str(noisy_dataset)).get("count", 0)
        assert sor_count < original_count
        assert radius_count < original_count

        # Results may differ
        assert sor_output.exists()
        assert radius_output.exists()

    @pytest.mark.integration
    def test_denoising_method_statistics(self, noisy_dataset: Path, tmp_path: Path) -> None:
        """Collect statistics on different denoising methods."""
        original_count = pdal.info(str(noisy_dataset)).get("count", 0)
        results = {}

        # Test different methods
        methods = [
            ("elm_only", pdal.Filter.elm(), pdal.Filter.range(limits="Classification![7:7]")),
            (
                "sor_conservative",
                pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=3.0),
                None,
            ),
            (
                "sor_moderate",
                pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0),
                None,
            ),
            ("radius", pdal.Filter.outlier(method="radius", radius=2.0, min_k=4), None),
        ]

        for method_name, filter1, filter2 in methods:
            output = tmp_path / f"{method_name}.las"
            if filter2:
                pipeline = Pipeline(
                    pdal.Reader.copc(str(noisy_dataset))
                    | filter1
                    | filter2
                    | pdal.Writer.las(str(output))
                )
            else:
                pipeline = Pipeline(
                    pdal.Reader.copc(str(noisy_dataset)) | filter1 | pdal.Writer.las(str(output))
                )

            count = pipeline.execute()
            removal_rate = ((original_count - count) / original_count) * 100 if count > 0 else 0
            results[method_name] = {"count": count, "removal_rate": removal_rate}

        # Verify all methods processed successfully
        assert all(r["count"] > 0 for r in results.values())
        print(f"\nDenoising comparison (original: {original_count} points):")
        for method, stats in results.items():
            print(f"  {method}: {stats['count']} pts ({stats['removal_rate']:.2f}% removed)")


class TestLargeDatasetDenoising:
    """Test denoising on large datasets (stress tests)."""

    @pytest.mark.slow
    def test_large_dataset_sor(self, large_noisy_dataset: Path, tmp_path: Path) -> None:
        """Test statistical outlier removal on large dataset (618MB, 115M points)."""
        output = tmp_path / "large_sor_cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(large_noisy_dataset))
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        cleaned_count = pipeline.execute()
        assert cleaned_count > 0
        assert output.exists()

        original_count = pdal.info(str(large_noisy_dataset)).get("count", 0)
        assert cleaned_count < original_count
        print(f"\nLarge SOR: {original_count} → {cleaned_count} points")

    @pytest.mark.slow
    def test_large_dataset_elm(self, large_noisy_dataset: Path, tmp_path: Path) -> None:
        """Test ELM filter on large dataset."""
        output = tmp_path / "large_elm_cleaned.las"

        pipeline = Pipeline(
            pdal.Reader.copc(str(large_noisy_dataset))
            | pdal.Filter.elm()
            | pdal.Filter.range(limits="Classification![7:7]")
            | pdal.Writer.las(str(output))
        )

        cleaned_count = pipeline.execute()
        assert cleaned_count > 0
        assert output.exists()
        print(f"\nLarge ELM: processed {cleaned_count} points")

    @pytest.mark.slow
    def test_large_dataset_spatial_denoising(
        self, large_noisy_dataset: Path, tmp_path: Path
    ) -> None:
        """Test denoising on spatial subset of large dataset for efficiency."""
        output = tmp_path / "large_spatial_cleaned.las"

        # Process only a subset with spatial bounds
        pipeline = Pipeline(
            pdal.Reader.copc(str(large_noisy_dataset), bounds="([785000,786000],[5350000,5351000])")
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        assert count > 0
        assert output.exists()
