"""Unit tests for base stage abstractions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import exeqpdal as pdal
from exeqpdal.exceptions import StageError
from exeqpdal.stages.base import FilterStage, ReaderStage, Stage, WriterStage

if TYPE_CHECKING:
    from pathlib import Path


class TestStageConstruction:
    """Validate basic Stage initialisation behaviour."""

    def test_reader_stage_creation(self) -> None:
        reader = ReaderStage("readers.las", filename="input.las")
        assert reader.stage_type == "readers.las"
        assert reader.filename == "input.las"

    def test_filter_stage_creation(self) -> None:
        filter_stage = FilterStage("filters.range", limits="Classification[2:2]")
        assert filter_stage.stage_type == "filters.range"
        assert filter_stage.options["limits"] == "Classification[2:2]"

    def test_writer_stage_creation(self) -> None:
        writer = WriterStage("writers.las", filename="output.las", compression="laszip")
        assert writer.stage_type == "writers.las"
        assert writer.filename == "output.las"
        assert writer.options["compression"] == "laszip"

    def test_stage_to_dict(self) -> None:
        reader = ReaderStage("readers.las", filename="input.las", tag="reader")
        stage_dict = reader.to_dict()

        assert stage_dict["type"] == "readers.las"
        assert stage_dict["filename"] == "input.las"
        assert stage_dict["tag"] == "reader"

    def test_reader_accepts_empty_filename(self) -> None:
        reader = ReaderStage("readers.las", filename="")
        assert reader.filename == ""

    def test_reader_accepts_none_filename(self) -> None:
        reader = ReaderStage("readers.las", filename=None)
        assert reader.filename is None

    def test_path_like_inputs_coerce_to_strings(self, tmp_path: Path) -> None:
        input_path = tmp_path / "input.las"
        output_path = tmp_path / "output.las"

        reader = ReaderStage("readers.las", filename=str(input_path))
        writer = WriterStage("writers.las", filename=str(output_path))

        assert reader.filename == str(input_path)
        assert writer.filename == str(output_path)

    def test_unicode_filename_roundtrip(self, tmp_path: Path) -> None:
        unicode_name = "üñíçödé_file.las"
        output_path = tmp_path / unicode_name

        writer = WriterStage("writers.las", filename=str(output_path))
        assert writer.filename is not None
        assert unicode_name in writer.filename


class TestStagePiping:
    """Check Stage piping semantics."""

    def test_stage_pipe_operator(self) -> None:
        reader = pdal.Reader.las("input.las")
        filter_stage = pdal.Filter.range(limits="Classification[2:2]")
        writer = pdal.Writer.las("output.las")

        pipeline = reader | filter_stage | writer

        assert isinstance(pipeline, Stage)
        assert pipeline.stage_type == "writers.las"
        assert pipeline.inputs and pipeline.inputs[-1] is filter_stage

    def test_stage_pipe_invalid_type(self) -> None:
        reader = pdal.Reader.las("input.las")

        with pytest.raises(StageError, match="Cannot pipe"):
            _ = reader | "invalid"  # type: ignore[operator]
