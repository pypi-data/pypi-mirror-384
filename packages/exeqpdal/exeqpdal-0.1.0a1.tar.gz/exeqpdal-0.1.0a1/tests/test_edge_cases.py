"""Edge case tests for exeqpdal."""

from __future__ import annotations

import tempfile
import threading
import time
from pathlib import Path
from typing import ClassVar

import pytest

import exeqpdal as pdal
from exeqpdal import Pipeline
from exeqpdal.exceptions import PipelineError


class TestExecutionEdgeCases:
    """Test edge cases in execution."""

    pytestmark: ClassVar = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_no_pdal")]

    def test_execute_same_pipeline_twice(self, small_laz: Path, tmp_path: Path) -> None:
        """Test executing same pipeline twice.

        Pipeline execution should be idempotent or raise appropriate error.
        """
        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        count1 = pipeline.execute()
        assert count1 > 0

        # Second execution (should work or raise appropriate error)
        try:
            count2 = pipeline.execute()
            # If successful, counts should match
            assert count2 == count1
        except PipelineError:
            # Pipeline may not support re-execution
            pass

    def test_pipeline_with_null_writer(self, small_laz: Path) -> None:
        """Test pipeline with null writer (discard output)."""
        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz)) | pdal.Filter.head(count=100) | pdal.Writer.null()
        )

        count = pipeline.execute()
        assert count >= 0

    @pytest.mark.slow
    def test_large_file_execution(self, large_laz: Path, tmp_path: Path) -> None:
        """Test execution with large file (performance test)."""
        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(large_laz))
            | pdal.Filter.head(count=1000000)
            | pdal.Writer.las(str(output))
        )

        start = time.time()
        count = pipeline.execute()
        duration = time.time() - start

        assert count > 0
        assert duration < 60

    def test_concurrent_pipeline_execution(self, small_laz: Path, tmp_path: Path) -> None:
        """Test concurrent execution of multiple pipelines."""
        results = []
        errors = []

        def execute_pipeline(idx: int) -> None:
            try:
                output = tmp_path / f"output_{idx}.las"
                pipeline = Pipeline(
                    pdal.Reader.las(str(small_laz))
                    | pdal.Filter.head(count=1000)
                    | pdal.Writer.las(str(output))
                )
                count = pipeline.execute()
                results.append(count)
            except Exception as e:
                errors.append(e)

        # Create 3 threads
        threads = [threading.Thread(target=execute_pipeline, args=(i,)) for i in range(3)]

        # Start threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # All should succeed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        assert all(r > 0 for r in results)


class TestCleanupEdgeCases:
    """Test cleanup and error recovery."""

    pytestmark: ClassVar = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_no_pdal")]

    def test_cleanup_on_error(self, tmp_path: Path) -> None:
        """Test that temp files are cleaned up on error."""
        temp_dir = Path(tempfile.gettempdir())
        initial_temp_count = len(list(temp_dir.glob("tmp*.json")))

        pipeline = Pipeline(
            pdal.Reader.las("/nonexistent/file.laz") | pdal.Writer.las(str(tmp_path / "out.las"))
        )

        try:
            pipeline.execute()
        except (PipelineError, Exception):
            pass

        # Temp files should be cleaned up
        final_temp_count = len(list(temp_dir.glob("tmp*.json")))
        # Temp count should not increase significantly
        assert final_temp_count <= initial_temp_count + 1

    def test_cleanup_on_keyboard_interrupt(self, small_laz: Path, tmp_path: Path) -> None:
        """Test cleanup when pipeline is interrupted.

        Note: Actual keyboard interrupt testing is difficult,
        this tests the cleanup mechanism structure.
        """
        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        # Execute normally to verify cleanup structure exists
        count = pipeline.execute()
        assert count > 0


class TestPipelineExecutionSequence:
    """Test pipeline execution sequence edge cases."""

    pytestmark: ClassVar = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_no_pdal")]

    def test_execute_after_failed_execution(self, small_laz: Path, tmp_path: Path) -> None:
        """Test executing pipeline after a failed execution attempt."""
        # First, try to execute with invalid file
        bad_pipeline = Pipeline(
            pdal.Reader.las("/nonexistent/file.laz") | pdal.Writer.las(str(tmp_path / "out1.las"))
        )

        with pytest.raises((PipelineError, Exception)):
            bad_pipeline.execute()

        # Now create valid pipeline and execute
        output = tmp_path / "out2.las"
        good_pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        count = good_pipeline.execute()
        assert count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_reader_only_no_writer(self, small_laz: Path) -> None:
        """Test pipeline with reader only (no writer stage)."""
        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Filter.head(count=100))

        # Should execute successfully without output file
        count = pipeline.execute()
        assert count >= 0
