"""Integration tests for Pipeline execution with real PDAL CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pytest

import exeqpdal as pdal
from exeqpdal import Pipeline
from exeqpdal.exceptions import PipelineError

if TYPE_CHECKING:
    from pathlib import Path


class TestPipelineRealExecution:
    """Test Pipeline.execute() with real PDAL CLI."""

    pytestmark: ClassVar = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_no_pdal")]

    def test_pipeline_execute_simple(self, small_laz: Path, tmp_path: Path) -> None:
        """Test basic pipeline execution."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        point_count = pipeline.execute()

        assert point_count > 0
        assert output.exists()
        assert pipeline._executed is True

    def test_pipeline_execute_with_metadata(self, small_laz: Path, tmp_path: Path) -> None:
        """Test accessing metadata after execution."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        pipeline.execute()

        metadata = pipeline.metadata
        assert metadata is not None
        assert isinstance(metadata, dict)
        assert "stages" in metadata or len(metadata) > 0

    def test_pipeline_validate_before_execute(self, small_laz: Path, tmp_path: Path) -> None:
        """Test validating pipeline before execution."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        is_valid = pipeline.validate()
        assert is_valid is True

        point_count = pipeline.execute()
        assert point_count >= 0

    def test_pipeline_arrays_not_loaded(self, small_laz: Path, tmp_path: Path) -> None:
        """Test that arrays are not loaded by default."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        pipeline.execute()

        arrays = pipeline.arrays
        assert isinstance(arrays, list)
        assert len(arrays) == 0

    def test_pipeline_streaming_enabled(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline execution with streaming mode enabled."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)), stream_mode=True
        )

        point_count = pipeline.execute()

        assert point_count > 0
        assert output.exists()

    def test_pipeline_execution_error(self, tmp_path: Path) -> None:
        """Test pipeline execution with invalid input file raises error."""
        pipeline = Pipeline(
            pdal.Reader.las("/nonexistent/file.laz") | pdal.Writer.las(str(tmp_path / "out.las"))
        )

        with pytest.raises(PipelineError) as exc_info:
            pipeline.execute()

        assert "Pipeline execution failed" in str(exc_info.value)


class TestPipelineValidation:
    """Test Pipeline validation methods."""

    pytestmark: ClassVar = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_no_pdal")]

    def test_validate_valid_pipeline(self, small_laz: Path, tmp_path: Path) -> None:
        """Test validation of valid pipeline returns True."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        is_valid = pipeline.validate()
        assert is_valid is True
        assert pipeline._is_valid is True

    def test_validate_sets_streamable_flag(self, small_laz: Path, tmp_path: Path) -> None:
        """Test validation sets is_streamable flag."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        pipeline.validate()

        assert pipeline._is_streamable is not None
        assert isinstance(pipeline._is_streamable, bool)

    def test_is_streamable_property(self, small_laz: Path, tmp_path: Path) -> None:
        """Test is_streamable property triggers validation."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        is_streamable = pipeline.is_streamable
        assert isinstance(is_streamable, bool)
        assert pipeline._is_streamable is not None
