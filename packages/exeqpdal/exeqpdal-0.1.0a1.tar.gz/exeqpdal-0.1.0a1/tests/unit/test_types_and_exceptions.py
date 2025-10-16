"""Unit tests for type helpers and custom exceptions."""

from __future__ import annotations

import pytest

import exeqpdal as pdal


class TestDimensions:
    """Ensure dimension helpers expose expected constants."""

    def test_dimension_constants(self) -> None:
        assert pdal.Dimension.X == "X"
        assert pdal.Dimension.Y == "Y"
        assert pdal.Dimension.Z == "Z"
        assert pdal.Dimension.CLASSIFICATION == "Classification"

    def test_dimension_types(self) -> None:
        assert pdal.DIMENSION_TYPES[pdal.Dimension.X] == pdal.DataType.DOUBLE
        assert pdal.DIMENSION_TYPES[pdal.Dimension.INTENSITY] == pdal.DataType.UINT16
        assert pdal.DIMENSION_TYPES[pdal.Dimension.CLASSIFICATION] == pdal.DataType.UINT8

    def test_classification_codes(self) -> None:
        assert pdal.Classification.GROUND == 2  # type: ignore[comparison-overlap]
        assert pdal.Classification.LOW_VEGETATION == 3  # type: ignore[unreachable]
        assert pdal.Classification.BUILDING == 6


class TestExceptions:
    """Validate custom exception hierarchy."""

    def test_pdal_error(self) -> None:
        with pytest.raises(pdal.PDALError):
            raise pdal.PDALError("Test error")

    def test_pdal_not_found_error(self) -> None:
        with pytest.raises(pdal.PDALNotFoundError):
            raise pdal.PDALNotFoundError()

    def test_pdal_execution_error(self) -> None:
        error = pdal.PDALExecutionError(
            "Execution failed",
            returncode=1,
            stderr="Error output",
        )
        assert error.returncode == 1
        assert "Error output" in str(error)

    def test_pipeline_error(self) -> None:
        with pytest.raises(pdal.PipelineError):
            raise pdal.PipelineError("Pipeline failed")
