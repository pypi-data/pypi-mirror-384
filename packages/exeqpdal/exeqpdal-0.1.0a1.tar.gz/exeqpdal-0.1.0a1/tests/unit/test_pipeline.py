"""Unit tests for Pipeline construction and serialization."""

from __future__ import annotations

import pytest

import exeqpdal as pdal
from exeqpdal.exceptions import PipelineError
from exeqpdal.stages.base import Stage


class TestPipelineParsing:
    """Validate Pipeline accepts supported representations."""

    def test_pipeline_from_json_string(self) -> None:
        json_str = """
        {
            "pipeline": [
                "input.las",
                {
                    "type": "filters.range",
                    "limits": "Classification[2:2]"
                },
                "output.las"
            ]
        }
        """
        pipeline = pdal.Pipeline(json_str)
        assert "pipeline" in pipeline._pipeline_dict

    def test_pipeline_from_dict(self) -> None:
        pipeline_dict = {
            "pipeline": [
                {"type": "readers.las", "filename": "input.las"},
                {"type": "filters.range", "limits": "Classification[2:2]"},
                {"type": "writers.las", "filename": "output.las"},
            ]
        }
        pipeline = pdal.Pipeline(pipeline_dict)
        assert "pipeline" in pipeline._pipeline_dict

    def test_pipeline_from_stages(self) -> None:
        final_stage = (
            pdal.Reader.las("input.las")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las("output.las")
        )
        pipeline = pdal.Pipeline(final_stage)
        assert "pipeline" in pipeline._pipeline_dict

    def test_pipeline_invalid_type(self) -> None:
        with pytest.raises(PipelineError, match="Invalid pipeline type"):
            pdal.Pipeline(123)  # type: ignore[arg-type]

    def test_pipeline_invalid_json(self) -> None:
        with pytest.raises(PipelineError):
            pdal.Pipeline("{ invalid json }")

    def test_pipeline_json_property(self) -> None:
        pipeline_dict = {
            "pipeline": [
                {"type": "readers.las", "filename": "input.las"},
            ]
        }
        pipeline = pdal.Pipeline(pipeline_dict)
        json_str = pipeline.pipeline_json
        assert "readers.las" in json_str

    def test_metadata_property_pre_execution_raises(self) -> None:
        pipeline = pdal.Pipeline({"pipeline": [{"type": "readers.las", "filename": "input.las"}]})
        with pytest.raises(PipelineError):
            _ = pipeline.metadata

    def test_log_property_pre_execution_raises(self) -> None:
        pipeline = pdal.Pipeline({"pipeline": [{"type": "readers.las", "filename": "input.las"}]})
        with pytest.raises(PipelineError):
            _ = pipeline.log

    def test_arrays_property_pre_execution_raises(self) -> None:
        pipeline = pdal.Pipeline({"pipeline": [{"type": "readers.las", "filename": "input.las"}]})
        with pytest.raises(PipelineError):
            _ = pipeline.arrays

    def test_pipeline_repr_reflects_execution_state(self) -> None:
        pipeline = pdal.Pipeline({"pipeline": [{"type": "readers.las", "filename": "input.las"}]})
        assert "not executed" in repr(pipeline)

        pipeline._executed = True  # simulate execution outcome
        pipeline._point_count = 42
        assert "executed" in repr(pipeline)
        assert "42" in repr(pipeline)


class TestPipelineComposition:
    """Sanity-check stage chaining for representative topologies."""

    def test_stage_chaining(self) -> None:
        pipeline = (
            pdal.Reader.las("input.las")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Filter.outlier(method="statistical", mean_k=8)
            | pdal.Writer.las("output.las", compression="laszip")
        )

        assert isinstance(pipeline, Stage)
        assert pipeline.stage_type == "writers.las"
        assert pipeline.filename == "output.las"

    def test_complex_pipeline(self) -> None:
        pipeline = (
            pdal.Reader.las("input.las")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Filter.hag_nn()
            | pdal.Filter.ferry(dimensions="HeightAboveGround=HAG")
            | pdal.Filter.range(limits="HAG[0:50]")
            | pdal.Writer.las("output.las")
        )

        json_str = pdal.Pipeline(pipeline).pipeline_json
        assert "filters.range" in json_str
        assert "filters.hag_nn" in json_str
