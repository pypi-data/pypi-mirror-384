"""Integration tests for pipeline applications (merge, split, tile, tindex)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from exeqpdal.apps import merge, split, tile, tindex

if TYPE_CHECKING:
    from pathlib import Path


class TestMergeApp:
    """Test merge() application."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_merge_two_files(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test merging two LAZ files into single output."""
        output = tmp_path / "merged.las"

        merge([str(f) for f in dual_laz], str(output))

        assert output.exists()
        assert output.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_merge_output_exists(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test merge creates output file with expected size."""
        output = tmp_path / "merged.laz"

        merge([str(f) for f in dual_laz], str(output))

        assert output.exists()
        assert output.stat().st_size > dual_laz[0].stat().st_size

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_merge_path_objects(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test merge with Path objects instead of strings."""
        output = tmp_path / "merged_path.las"

        merge([str(f) for f in dual_laz], str(output))

        assert output.exists()


class TestSplitApp:
    """Test split() application."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_split_by_capacity(self, small_laz: Path, tmp_path: Path) -> None:
        """Test splitting file by point capacity."""
        output_pattern = tmp_path / "split_#.las"

        split(str(small_laz), str(output_pattern), capacity=1000000)

        split_files = list(tmp_path.glob("split_*.las"))
        assert len(split_files) > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_split_creates_files(self, small_laz: Path, tmp_path: Path) -> None:
        """Test split creates multiple output files."""
        output_pattern = tmp_path / "output_#.las"

        split(str(small_laz), str(output_pattern), capacity=500000)

        split_files = list(tmp_path.glob("output_*.las"))
        assert len(split_files) >= 1
        for f in split_files:
            assert f.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_split_by_length(self, small_laz: Path, tmp_path: Path) -> None:
        """Test splitting file by distance length."""
        output_pattern = tmp_path / "length_#.las"

        split(str(small_laz), str(output_pattern), length=500)

        split_files = list(tmp_path.glob("length_*.las"))
        assert len(split_files) > 0


class TestTileApp:
    """Test tile() application."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_tile_basic(self, medium_laz: Path, tmp_path: Path) -> None:
        """Test basic tiling with length parameter."""
        output_pattern = tmp_path / "tiles" / "tile_#.las"
        output_pattern.parent.mkdir()

        tile(str(medium_laz), str(output_pattern), length=500.0)

        tile_files = list(output_pattern.parent.glob("tile_*.las"))
        assert len(tile_files) > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_tile_creates_grid(self, small_laz: Path, tmp_path: Path) -> None:
        """Test tiling creates grid structure output."""
        output_pattern = tmp_path / "grid" / "grid_#.las"
        output_pattern.parent.mkdir()

        tile(str(small_laz), str(output_pattern), length=1000.0)

        tile_files = list(output_pattern.parent.glob("grid_*.las"))
        assert len(tile_files) >= 1
        for f in tile_files:
            assert f.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_tile_with_buffer(self, small_laz: Path, tmp_path: Path) -> None:
        """Test tiling with buffer parameter."""
        output_pattern = tmp_path / "buffered" / "buffered_#.las"
        output_pattern.parent.mkdir()

        tile(str(small_laz), str(output_pattern), length=1000.0, buffer=50.0)

        tile_files = list(output_pattern.parent.glob("buffered_*.las"))
        assert len(tile_files) > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_tile_with_origin(self, small_laz: Path, tmp_path: Path) -> None:
        """Test tiling with custom origin parameters."""
        output_pattern = tmp_path / "origin" / "origin_#.las"
        output_pattern.parent.mkdir()

        tile(
            str(small_laz),
            str(output_pattern),
            length=1000.0,
            origin_x=785000.0,
            origin_y=5351000.0,
        )

        tile_files = list(output_pattern.parent.glob("origin_*.las"))
        assert len(tile_files) > 0


class TestTindexApp:
    """Test tindex() application."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_tindex_creates_index(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test creating basic tile index."""
        tindex_file = tmp_path / "index.geojson"

        tindex([str(f) for f in dual_laz], str(tindex_file))

        assert tindex_file.exists()
        assert tindex_file.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_tindex_multiple_files(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test tindex with multiple files."""
        tindex_file = tmp_path / "index_multi.geojson"

        tindex([str(f) for f in dual_laz], str(tindex_file))

        assert tindex_file.exists()
        assert tindex_file.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_tindex_with_fast_boundary(self, dual_laz: list[Path], tmp_path: Path) -> None:
        """Test tindex with fast_boundary flag."""
        tindex_file = tmp_path / "index_fast.geojson"

        tindex([str(f) for f in dual_laz], str(tindex_file), fast_boundary=True)

        assert tindex_file.exists()
