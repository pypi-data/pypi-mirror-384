"""Performance benchmark tests for exeqpdal.

Tests performance characteristics using **large datasets**:
- Large file I/O performance (1.1GB, 115M points)
- Filter operation benchmarks
- COPC vs LAS performance comparison
- Memory usage and efficiency
- Pipeline optimization

Uses:
- large_performance_dataset (1.1GB, 115M points) for stress tests
- large_noisy_dataset (618MB COPC, 115M points) for COPC performance

**Expected Runtime**: 1-10 minutes per test
All tests marked with @pytest.mark.slow and @pytest.mark.benchmark
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

import exeqpdal as pdal
from exeqpdal import Pipeline

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [
    pytest.mark.slow,
    pytest.mark.benchmark,
    pytest.mark.integration,
    pytest.mark.usefixtures("skip_if_no_pdal"),
]


class TestLargeFileIO:
    """Test I/O performance with large datasets."""

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_large_file_read_write(self, large_performance_dataset: Path, tmp_path: Path) -> None:
        """Benchmark large file read and write (1.1GB, 115M points)."""
        output = tmp_path / "large_output.las"

        start_time = time.time()

        pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset)) | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        duration = time.time() - start_time

        assert count > 100_000_000  # Should be ~115M points
        assert output.exists()
        assert duration < 600  # Should complete within 10 minutes

        print(
            f"\nLarge file I/O: {count:,} points in {duration:.2f}s ({count / duration:.0f} pts/s)"
        )

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_large_file_with_head_filter(
        self, large_performance_dataset: Path, tmp_path: Path
    ) -> None:
        """Benchmark reading large file with early termination."""
        output = tmp_path / "large_head.las"

        start_time = time.time()

        pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.head(count=10_000_000)  # First 10M points
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        duration = time.time() - start_time

        assert count == 10_000_000
        assert output.exists()
        assert duration < 120  # Should be fast with early termination

        print(f"\nLarge file with head: {count:,} points in {duration:.2f}s")

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_large_file_info_stats(self, large_performance_dataset: Path) -> None:
        """Benchmark info+stats operation on large file."""
        start_time = time.time()

        info = pdal.info(str(large_performance_dataset), stats=True)
        duration = time.time() - start_time

        assert "stats" in info
        assert info.get("count", 0) > 100_000_000
        assert duration < 300  # Should complete within 5 minutes

        print(f"\nLarge file info+stats: {duration:.2f}s")


class TestFilterPerformance:
    """Test filter operation performance on large datasets."""

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_crop_filter_performance(self, large_performance_dataset: Path, tmp_path: Path) -> None:
        """Benchmark spatial crop filter on large dataset."""
        output = tmp_path / "large_cropped.las"

        start_time = time.time()

        pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.crop(bounds="([785000,786000],[5350000,5351000])")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        duration = time.time() - start_time

        assert count > 0
        assert output.exists()
        assert duration < 600

        print(f"\nCrop filter (large): {count:,} points in {duration:.2f}s")

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_range_filter_performance(
        self, large_performance_dataset: Path, tmp_path: Path
    ) -> None:
        """Benchmark range filter on large dataset."""
        output = tmp_path / "large_range_filtered.las"

        start_time = time.time()

        pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.range(limits="Z[0:500]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        duration = time.time() - start_time

        assert count > 0
        assert output.exists()
        assert duration < 600

        print(f"\nRange filter (large): {count:,} points in {duration:.2f}s")

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_outlier_filter_performance(self, large_noisy_dataset: Path, tmp_path: Path) -> None:
        """Benchmark outlier removal on large dataset."""
        output = tmp_path / "large_outlier_removed.las"

        start_time = time.time()

        pipeline = Pipeline(
            pdal.Reader.copc(str(large_noisy_dataset))
            | pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        duration = time.time() - start_time

        assert count > 0
        assert output.exists()
        assert duration < 900  # Outlier removal is computationally expensive

        print(f"\nOutlier filter (large): {count:,} points in {duration:.2f}s")

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_sort_filter_performance(self, large_performance_dataset: Path, tmp_path: Path) -> None:
        """Benchmark sort filter on large dataset."""
        output = tmp_path / "large_sorted.las"

        start_time = time.time()

        # Sort by Z dimension (common use case)
        pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.head(count=20_000_000)  # Limit to 20M for reasonable runtime
            | pdal.Filter.sort(dimension="Z")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        duration = time.time() - start_time

        assert count == 20_000_000
        assert output.exists()
        assert duration < 300

        print(f"\nSort filter (20M points): {duration:.2f}s")


class TestCOPCvsLASPerformance:
    """Compare COPC vs LAS performance."""

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_copc_vs_las_full_read(
        self, large_performance_dataset: Path, large_noisy_dataset: Path, tmp_path: Path
    ) -> None:
        """Compare full read performance: LAS vs COPC."""
        las_output = tmp_path / "las_full_read.las"
        copc_output = tmp_path / "copc_full_read.las"

        # Read LAS
        start_las = time.time()
        las_pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.head(count=10_000_000)
            | pdal.Writer.las(str(las_output))
        )
        las_count = las_pipeline.execute()
        las_duration = time.time() - start_las

        # Read COPC
        start_copc = time.time()
        copc_pipeline = Pipeline(
            pdal.Reader.copc(str(large_noisy_dataset))
            | pdal.Filter.head(count=10_000_000)
            | pdal.Writer.las(str(copc_output))
        )
        copc_count = copc_pipeline.execute()
        copc_duration = time.time() - start_copc

        assert las_count == copc_count == 10_000_000
        assert las_output.exists()
        assert copc_output.exists()

        print("\nFull read (10M points):")
        print(f"  LAS:  {las_duration:.2f}s ({las_count / las_duration:.0f} pts/s)")
        print(f"  COPC: {copc_duration:.2f}s ({copc_count / copc_duration:.0f} pts/s)")

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_copc_vs_las_spatial_query(
        self, large_performance_dataset: Path, large_noisy_dataset: Path, tmp_path: Path
    ) -> None:
        """Compare spatial query performance: LAS vs COPC."""
        las_output = tmp_path / "las_query.las"
        copc_output = tmp_path / "copc_query.las"

        bounds = "([785000,786000],[5350000,5351000])"

        # LAS spatial query (requires full scan)
        start_las = time.time()
        las_pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.crop(bounds=bounds)
            | pdal.Writer.las(str(las_output))
        )
        las_count = las_pipeline.execute()
        las_duration = time.time() - start_las

        # COPC spatial query (uses spatial index)
        start_copc = time.time()
        copc_pipeline = Pipeline(
            pdal.Reader.copc(str(large_noisy_dataset), bounds=bounds)
            | pdal.Writer.las(str(copc_output))
        )
        copc_count = copc_pipeline.execute()
        copc_duration = time.time() - start_copc

        assert las_count > 0
        assert copc_count > 0
        assert las_output.exists()
        assert copc_output.exists()

        # COPC should be significantly faster for spatial queries
        speedup = las_duration / copc_duration if copc_duration > 0 else 0

        print("\nSpatial query performance:")
        print(f"  LAS:  {las_duration:.2f}s ({las_count:,} points)")
        print(f"  COPC: {copc_duration:.2f}s ({copc_count:,} points)")
        print(f"  COPC speedup: {speedup:.1f}x")


class TestPipelineOptimization:
    """Test pipeline optimization strategies."""

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_filter_order_optimization(
        self, large_performance_dataset: Path, tmp_path: Path
    ) -> None:
        """Compare pipeline performance with different filter orders."""
        # Strategy 1: Crop first (reduces data early)
        output1 = tmp_path / "crop_first.las"
        start1 = time.time()
        pipeline1 = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.crop(bounds="([785000,786000],[5350000,5351000])")
            | pdal.Filter.range(limits="Z[0:500]")
            | pdal.Writer.las(str(output1))
        )
        count1 = pipeline1.execute()
        duration1 = time.time() - start1

        # Strategy 2: Range first (may be less efficient)
        output2 = tmp_path / "range_first.las"
        start2 = time.time()
        pipeline2 = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.range(limits="Z[0:500]")
            | pdal.Filter.crop(bounds="([785000,786000],[5350000,5351000])")
            | pdal.Writer.las(str(output2))
        )
        count2 = pipeline2.execute()
        duration2 = time.time() - start2

        assert count1 == count2  # Same result
        assert output1.exists()
        assert output2.exists()

        print("\nFilter order optimization:")
        print(f"  Crop first:  {duration1:.2f}s")
        print(f"  Range first: {duration2:.2f}s")
        print(f"  Difference:  {abs(duration1 - duration2):.2f}s")

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_multi_stage_pipeline_performance(
        self, large_performance_dataset: Path, tmp_path: Path
    ) -> None:
        """Benchmark complex multi-stage pipeline on large data."""
        output = tmp_path / "multi_stage_output.las"

        start_time = time.time()

        pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.crop(bounds="([785000,786000],[5350000,5351000])")
            | pdal.Filter.range(limits="Z[0:500]")
            | pdal.Filter.smrf()  # Ground classification
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las(str(output))
        )

        count = pipeline.execute()
        duration = time.time() - start_time

        assert count >= 0  # May be 0 if no ground points
        if count > 0:
            assert output.exists()

        print(f"\nMulti-stage pipeline: {count:,} points in {duration:.2f}s")


class TestMemoryEfficiency:
    """Test memory efficiency with large datasets."""

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_streaming_vs_full_load(self, large_noisy_dataset: Path, tmp_path: Path) -> None:
        """Compare streaming (COPC with bounds) vs full load."""
        # Streaming approach (efficient)
        streaming_output = tmp_path / "streaming.las"
        start_stream = time.time()
        stream_pipeline = Pipeline(
            pdal.Reader.copc(str(large_noisy_dataset), bounds="([785000,786000],[5350000,5351000])")
            | pdal.Writer.las(str(streaming_output))
        )
        stream_count = stream_pipeline.execute()
        stream_duration = time.time() - start_stream

        assert stream_count > 0
        assert streaming_output.exists()

        print(f"\nStreaming approach: {stream_count:,} points in {stream_duration:.2f}s")

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_chunked_processing(self, large_performance_dataset: Path, tmp_path: Path) -> None:
        """Test processing large file in chunks."""
        chunk_size = 20_000_000  # 20M points per chunk

        start_time = time.time()

        # Process first chunk
        chunk_output = tmp_path / "chunk_1.las"
        pipeline = Pipeline(
            pdal.Reader.las(str(large_performance_dataset))
            | pdal.Filter.head(count=chunk_size)
            | pdal.Writer.las(str(chunk_output))
        )

        count = pipeline.execute()
        duration = time.time() - start_time

        assert count == chunk_size
        assert chunk_output.exists()

        print(f"\nChunk processing: {count:,} points in {duration:.2f}s")


class TestScalability:
    """Test scalability with different data sizes."""

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_scalability_comparison(self, large_performance_dataset: Path, tmp_path: Path) -> None:
        """Compare processing time for different point counts."""
        sizes = [1_000_000, 5_000_000, 10_000_000, 20_000_000]
        results = []

        for size in sizes:
            output = tmp_path / f"scale_{size}.las"
            start = time.time()

            pipeline = Pipeline(
                pdal.Reader.las(str(large_performance_dataset))
                | pdal.Filter.head(count=size)
                | pdal.Writer.las(str(output))
            )

            count = pipeline.execute()
            duration = time.time() - start

            assert count == size
            assert output.exists()

            throughput = count / duration if duration > 0 else 0
            results.append((size, duration, throughput))

        print("\nScalability analysis:")
        for size, duration, throughput in results:
            print(f"  {size:>11,} pts: {duration:6.2f}s ({throughput:>11,.0f} pts/s)")
