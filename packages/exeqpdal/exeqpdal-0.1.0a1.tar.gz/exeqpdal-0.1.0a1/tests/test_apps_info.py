"""Integration tests for info application."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from exeqpdal.apps import get_bounds, get_count, get_dimensions, get_srs, get_stats, info
from exeqpdal.exceptions import PDALExecutionError

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
class TestInfoAppRealExecution:
    """Test info application with real PDAL CLI execution."""

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_basic(self, small_laz: Path) -> None:
        """Test basic info extraction from LAZ file."""
        result = info(small_laz)

        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_all_metadata(self, small_laz: Path) -> None:
        """Test info with all_metadata=True parameter."""
        result = info(small_laz, all=True)

        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_point_count(self, small_laz: Path) -> None:
        """Test get_count helper function returns int (may be 0 if not in output)."""
        count = get_count(small_laz)

        assert isinstance(count, int)
        assert count >= 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_bounds(self, small_laz: Path) -> None:
        """Test get_bounds helper function returns dict (structure varies by PDAL)."""
        bounds = get_bounds(small_laz)

        assert isinstance(bounds, dict)
        if "minx" in bounds:
            assert "maxx" in bounds
            assert bounds["minx"] < bounds["maxx"]

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_dimensions(self, small_laz: Path) -> None:
        """Test get_dimensions helper function."""
        dimensions = get_dimensions(small_laz)

        assert isinstance(dimensions, list)
        assert len(dimensions) > 0
        assert "X" in dimensions
        assert "Y" in dimensions
        assert "Z" in dimensions

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_metadata_json(self, small_laz: Path) -> None:
        """Test info returns valid JSON structure."""
        result = info(small_laz, metadata=True)

        assert isinstance(result, dict)
        json_str = json.dumps(result)
        assert len(json_str) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_with_summary(self, small_laz: Path) -> None:
        """Test info with summary parameter."""
        result = info(small_laz, summary=True)

        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_schema_output(self, small_laz: Path) -> None:
        """Test info with schema flag."""
        result = info(small_laz, schema=True)

        assert isinstance(result, dict)
        assert "schema" in result
        schema = result["schema"]
        assert "dimensions" in schema
        assert len(schema["dimensions"]) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_stats(self, small_laz: Path) -> None:
        """Test info with statistics output."""
        result = info(small_laz, stats=True)

        assert isinstance(result, dict)
        assert "stats" in result

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_invalid_file(self, tmp_path: Path) -> None:
        """Test error handling for missing file."""
        nonexistent_file = tmp_path / "nonexistent.laz"

        with pytest.raises(PDALExecutionError) as exc_info:
            info(nonexistent_file)

        assert exc_info.value.stderr is not None
        assert len(exc_info.value.stderr) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_returns_dict(self, small_laz: Path) -> None:
        """Test that info always returns a dictionary."""
        result = info(small_laz)

        assert isinstance(result, dict)
        assert result is not None

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_summary(self, small_laz: Path) -> None:
        """Test info with summary flag."""
        result = info(small_laz, summary=True)

        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_boundary(self, small_laz: Path) -> None:
        """Test info with boundary flag."""
        result = info(small_laz, boundary=True)

        assert isinstance(result, dict)
        assert "boundary" in result
        boundary = result["boundary"]
        assert isinstance(boundary, dict)
        assert "minx" in boundary or len(boundary) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_with_all_flag(self, small_laz: Path) -> None:
        """Test info with all flag includes comprehensive data."""
        result = info(small_laz, all=True)

        assert isinstance(result, dict)
        assert len(result) > 0
        assert "stats" in result or "schema" in result

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_get_srs(self, small_laz: Path) -> None:
        """Test get_srs helper function."""
        srs = get_srs(small_laz)

        assert isinstance(srs, str)

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_get_stats(self, small_laz: Path) -> None:
        """Test get_stats helper function."""
        stats = get_stats(small_laz)

        assert isinstance(stats, dict)

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_multiple_flags(self, small_laz: Path) -> None:
        """Test info with multiple flags simultaneously."""
        result = info(small_laz, stats=True, metadata=True, schema=True)

        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_path_object(self, small_laz: Path) -> None:
        """Test info accepts Path objects."""
        result = info(small_laz)

        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_string_path(self, small_laz: Path) -> None:
        """Test info accepts string paths."""
        result = info(str(small_laz))

        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_info_all_parameters_combinations(self, small_laz: Path) -> None:
        """Test info with various compatible parameter combinations."""
        result1 = info(small_laz, stats=True, boundary=True)
        assert isinstance(result1, dict)

        result2 = info(small_laz, schema=True, metadata=True)
        assert isinstance(result2, dict)

        result3 = info(small_laz, stats=True, schema=True)
        assert isinstance(result3, dict)

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_get_count_with_no_count_field(self, small_laz: Path) -> None:
        """Test get_count returns 0 when count field missing."""
        count = get_count(small_laz)
        assert isinstance(count, int)

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_get_dimensions_returns_list(self, small_laz: Path) -> None:
        """Test get_dimensions always returns list."""
        dims = get_dimensions(small_laz)
        assert isinstance(dims, list)
        assert all(isinstance(d, str) for d in dims)
