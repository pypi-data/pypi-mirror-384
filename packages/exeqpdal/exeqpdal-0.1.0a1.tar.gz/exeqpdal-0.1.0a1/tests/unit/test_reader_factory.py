"""Unit tests for Reader factory helpers."""

from __future__ import annotations

import exeqpdal as pdal


class TestReaderFactory:
    """Ensure Reader factories expose the PDAL reader catalogue."""

    def test_reader_las(self) -> None:
        reader = pdal.Reader.las("input.las")
        assert reader.stage_type == "readers.las"
        assert reader.filename == "input.las"

    def test_reader_copc(self) -> None:
        reader = pdal.Reader.copc("input.copc.laz")
        assert reader.stage_type == "readers.copc"

    def test_reader_text(self) -> None:
        reader = pdal.Reader.text("input.txt")
        assert reader.stage_type == "readers.text"

    def test_reader_with_options(self) -> None:
        reader = pdal.Reader.las("input.las", spatialreference="EPSG:4326")
        assert reader.options["spatialreference"] == "EPSG:4326"

    def test_reader_buffer_without_filename(self) -> None:
        reader = pdal.Reader.buffer(data="dummy")
        assert reader.stage_type == "readers.buffer"
        assert reader.filename is None
        assert "filename" not in reader.to_dict()

    def test_reader_pgpointcloud_without_filename(self) -> None:
        reader = pdal.Reader.pgpointcloud(
            connection="postgresql://user:pass@localhost/db",
            table="pcpatches",
        )
        assert reader.stage_type == "readers.pgpointcloud"
        assert reader.filename is None
        assert "filename" not in reader.to_dict()
