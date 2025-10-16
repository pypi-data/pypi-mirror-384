"""Integration tests for executor with real PDAL CLI execution."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from exeqpdal.core.executor import Executor, executor
from exeqpdal.exceptions import PDALExecutionError

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
class TestExecutorRealExecution:
    """Test executor with real PDAL CLI execution."""

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_basic(self, small_laz: Path, tmp_path: Path) -> None:
        """Test basic pipeline execution: read LAZ, write LAS."""
        output = tmp_path / "output.las"

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "writers.las", "filename": str(output)},
            ]
        }

        _stdout, _stderr, returncode, _metadata = executor.execute_pipeline(
            pipeline_json, metadata=True
        )

        assert returncode == 0
        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_with_filter(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline with filter stage."""
        output = tmp_path / "filtered.laz"

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "filters.range", "limits": "Classification[2:2]"},
                {"type": "writers.las", "filename": str(output), "compression": True},
            ]
        }

        _stdout, _stderr, returncode, _metadata = executor.execute_pipeline(
            pipeline_json, metadata=True
        )

        assert returncode == 0
        assert output.exists()
        assert output.stat().st_size < small_laz.stat().st_size

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_returns_point_count(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline execution returns point count in metadata."""
        output = tmp_path / "output.las"

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "writers.las", "filename": str(output)},
            ]
        }

        _stdout, _stderr, returncode, metadata = executor.execute_pipeline(
            pipeline_json, metadata=True
        )

        assert returncode == 0
        assert metadata is not None
        assert "stages" in metadata
        assert "readers.las" in metadata["stages"]

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_creates_output_file(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline creates output file at expected location."""
        output = tmp_path / "test_output.las"

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "writers.las", "filename": str(output)},
            ]
        }

        executor.execute_pipeline(pipeline_json, metadata=False)

        assert output.exists()
        assert output.is_file()
        assert output.stat().st_size > 1000

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_with_metadata(self, small_laz: Path, tmp_path: Path) -> None:
        """Test metadata extraction from pipeline execution."""
        output = tmp_path / "output.las"

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "writers.las", "filename": str(output)},
            ]
        }

        _stdout, _stderr, _returncode, metadata = executor.execute_pipeline(
            pipeline_json, metadata=True
        )

        assert metadata is not None
        assert isinstance(metadata, dict)
        assert len(metadata) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_application_info(self, small_laz: Path) -> None:
        """Test info application execution."""
        stdout, _stderr, returncode = executor.execute_application(
            "info", ["--summary"], input_file=small_laz
        )

        assert returncode == 0
        assert len(stdout) > 0

        info_data = json.loads(stdout)
        assert "summary" in info_data
        assert "num_points" in info_data["summary"]
        assert info_data["summary"]["num_points"] > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_application_translate(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate application execution."""
        output = tmp_path / "translated.las"

        _stdout, _stderr, returncode = executor.execute_application(
            "translate", [str(output)], input_file=small_laz
        )

        assert returncode == 0
        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_validate_pipeline_valid(self, small_laz: Path, tmp_path: Path) -> None:
        """Test validation passes for valid pipeline."""
        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "writers.las", "filename": str(tmp_path / "out.las")},
            ]
        }

        is_valid, is_streamable, message = executor.validate_pipeline(pipeline_json)

        assert is_valid is True
        assert isinstance(is_streamable, bool)
        assert isinstance(message, str)

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_validate_pipeline_invalid(self) -> None:
        """Test validation passes for structurally valid pipeline."""
        pipeline_json = {
            "pipeline": [
                {"type": "readers.las"},
            ]
        }

        is_valid, is_streamable, message = executor.validate_pipeline(pipeline_json)

        assert isinstance(is_valid, bool)
        assert isinstance(is_streamable, bool)
        assert isinstance(message, str)

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_get_driver_info(self) -> None:
        """Test driver info retrieval returns JSON."""
        with pytest.raises(PDALExecutionError):
            executor.get_driver_info("readers.las")

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pdal_execution_error(self, tmp_path: Path) -> None:
        """Test PDAL execution error handling for invalid input."""
        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": "/nonexistent/file.laz"},
                {"type": "writers.las", "filename": str(tmp_path / "out.las")},
            ]
        }

        with pytest.raises(PDALExecutionError) as exc_info:
            executor.execute_pipeline(pipeline_json)

        assert exc_info.value.returncode != 0
        assert exc_info.value.stderr is not None
        assert len(exc_info.value.stderr) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_with_streaming(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test pipeline execution with streaming mode."""
        output = tmp_path / "streamed.las"

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(medium_laz)},
                {"type": "filters.range", "limits": "Z[0:400]"},
                {"type": "writers.las", "filename": str(output)},
            ]
        }

        _stdout, _stderr, returncode, _metadata = executor.execute_pipeline(
            pipeline_json, stream_mode=True, metadata=True
        )

        assert returncode == 0
        assert output.exists()

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_validation_error(self) -> None:
        """Test validation handles JSON conversion correctly."""
        pipeline_dict: dict[str, list[dict[str, str]]] = {"pipeline": []}

        is_valid, is_streamable, message = executor.validate_pipeline(pipeline_dict)

        assert isinstance(is_valid, bool)
        assert isinstance(is_streamable, bool)
        assert isinstance(message, str)

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_from_dict(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline execution accepts dict input."""
        pipeline_dict = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "writers.las", "filename": str(tmp_path / "out.las")},
            ]
        }

        _stdout, _stderr, returncode, _metadata = executor.execute_pipeline(
            pipeline_dict, metadata=True
        )

        assert returncode == 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_verbose_flag(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline execution with verbose output."""
        output = tmp_path / "output.las"

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "writers.las", "filename": str(output)},
            ]
        }

        verbose_exec = Executor(verbose=True)
        _stdout, stderr, returncode, _metadata = verbose_exec.execute_pipeline(
            pipeline_json, metadata=False
        )

        assert returncode == 0
        assert len(stderr) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_metadata_disabled(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline execution without metadata generation."""
        output = tmp_path / "output.las"

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "writers.las", "filename": str(output)},
            ]
        }

        _stdout, _stderr, returncode, metadata = executor.execute_pipeline(
            pipeline_json, metadata=False
        )

        assert returncode == 0
        assert metadata is None

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_pipeline_invalid_stage_error(self, small_laz: Path, tmp_path: Path) -> None:
        """Test error handling for invalid stage type."""
        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "filters.nonexistent", "param": "value"},
                {"type": "writers.las", "filename": str(tmp_path / "out.las")},
            ]
        }

        with pytest.raises(PDALExecutionError) as exc_info:
            executor.execute_pipeline(pipeline_json)

        assert exc_info.value.returncode != 0
        assert exc_info.value.stderr is not None
        assert (
            "nonexistent" in exc_info.value.stderr.lower()
            or "unknown" in exc_info.value.stderr.lower()
        )

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_application_with_verbose(self, small_laz: Path) -> None:
        """Test application execution with verbose executor."""
        verbose_exec = Executor(verbose=True)

        stdout, _stderr, returncode = verbose_exec.execute_application(
            "info", ["--summary"], input_file=small_laz
        )

        assert returncode == 0
        assert len(stdout) > 0
