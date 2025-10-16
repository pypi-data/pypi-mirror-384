"""Integration tests for translate application."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from exeqpdal.apps import convert, translate
from exeqpdal.exceptions import PDALExecutionError

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
class TestTranslateAppRealExecution:
    """Test translate() application with real PDAL CLI execution."""

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_laz_to_las(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translating LAZ to uncompressed LAS."""
        output = tmp_path / "output.las"

        translate(str(small_laz), str(output))

        assert output.exists()
        assert output.stat().st_size > 0
        assert output.stat().st_size > small_laz.stat().st_size

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_las_to_laz_with_compression(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translating LAS to LAZ with compression."""
        las_file = tmp_path / "temp.las"
        translate(str(small_laz), str(las_file))

        laz_output = tmp_path / "compressed.laz"
        translate(str(las_file), str(laz_output))

        assert laz_output.exists()
        assert laz_output.stat().st_size < las_file.stat().st_size

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_with_filter(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate with filter option."""
        output = tmp_path / "filtered.laz"

        translate(
            str(small_laz),
            str(output),
            filters=["range"],
            filters_range_limits="Classification[2:2]",
        )

        assert output.exists()
        assert output.stat().st_size > 0
        assert output.stat().st_size < small_laz.stat().st_size

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_with_multiple_filters(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate with multiple filters."""
        output = tmp_path / "filtered.las"

        translate(
            str(small_laz),
            str(output),
            filters=["range", "assign"],
            filters_range_limits="Z[0:500]",
            filters_assign_value="Classification = 2",
        )

        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_with_reader_explicit(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate with explicit reader specification."""
        output = tmp_path / "output.las"

        translate(str(small_laz), str(output), reader="readers.las")

        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_with_writer_explicit(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate with explicit writer specification."""
        output = tmp_path / "compressed.laz"

        translate(str(small_laz), str(output), writer="writers.las")

        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_with_dims_option(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate with dims option."""
        output = tmp_path / "output.las"

        translate(str(small_laz), str(output), dims="X,Y,Z,Classification")

        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_returns_none(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate returns None (function completes without value)."""
        output = tmp_path / "output.las"

        translate(str(small_laz), str(output))

        assert output.exists()

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_output_exists(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate creates output file at expected location."""
        output = tmp_path / "test_output.las"

        translate(str(small_laz), str(output))

        assert output.exists()
        assert output.is_file()
        assert output.stat().st_size > 1000

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_invalid_input(self, tmp_path: Path) -> None:
        """Test translate with nonexistent input file."""
        output = tmp_path / "output.las"

        with pytest.raises(PDALExecutionError) as exc_info:
            translate("/nonexistent/file.laz", str(output))

        assert exc_info.value.returncode != 0
        assert exc_info.value.stderr is not None

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_format_detection(self, small_laz: Path, tmp_path: Path) -> None:
        """Test automatic format detection from file extension."""
        output_las = tmp_path / "output.las"
        output_laz = tmp_path / "output.laz"

        translate(str(small_laz), str(output_las))
        assert output_las.exists()

        translate(str(small_laz), str(output_laz))
        assert output_laz.exists()

        assert output_laz.stat().st_size < output_las.stat().st_size

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_with_pathlib_paths(self, small_laz: Path, tmp_path: Path) -> None:
        """Test translate accepts pathlib.Path objects."""
        output = tmp_path / "output.las"

        translate(small_laz, output)

        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_translate_options_underscore_to_dot_conversion(
        self, small_laz: Path, tmp_path: Path
    ) -> None:
        """Test translate converts underscore options to PDAL dot notation."""
        output = tmp_path / "output.laz"

        translate(
            str(small_laz),
            str(output),
            writers_las_compression="laszip",
        )

        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_convert_alias(self, small_laz: Path, tmp_path: Path) -> None:
        """Test convert() function as alias for translate()."""
        output = tmp_path / "output.las"

        convert(str(small_laz), str(output))

        assert output.exists()
        assert output.stat().st_size > 0
