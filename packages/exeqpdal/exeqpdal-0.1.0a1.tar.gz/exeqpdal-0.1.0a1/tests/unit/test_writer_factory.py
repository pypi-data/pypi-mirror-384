"""Unit tests for Writer factory wrappers."""

from __future__ import annotations

import exeqpdal as pdal


class TestWriterFactory:
    """Smoke tests for representative writer factories."""

    def test_writer_las(self) -> None:
        writer = pdal.Writer.las("output.las")
        assert writer.stage_type == "writers.las"
        assert writer.filename == "output.las"

    def test_writer_copc(self) -> None:
        writer = pdal.Writer.copc("output.copc.laz")
        assert writer.stage_type == "writers.copc"

    def test_writer_with_compression(self) -> None:
        writer = pdal.Writer.las("output.laz", compression="laszip")
        assert writer.options["compression"] == "laszip"

    def test_writer_null_without_filename(self) -> None:
        writer = pdal.Writer.null()
        assert writer.stage_type == "writers.null"
        assert writer.filename is None
        assert "filename" not in writer.to_dict()

    def test_writer_pgpointcloud_without_filename(self) -> None:
        writer = pdal.Writer.pgpointcloud(
            connection="postgresql://user:pass@localhost/db",
            table="pcpatches",
        )
        assert writer.stage_type == "writers.pgpointcloud"
        assert writer.filename is None
        assert "filename" not in writer.to_dict()

    def test_writer_ept_addon_without_filename(self) -> None:
        writer = pdal.Writer.ept_addon(addons={"Autzen": "autzen-smrf.las"})
        assert writer.stage_type == "writers.ept_addon"
        assert writer.filename is None
        assert "filename" not in writer.to_dict()

    def test_writer_tiledb_array_name_alias(self) -> None:
        writer = pdal.Writer.tiledb("tiledb:///arrays/demo", append=True)
        assert writer.stage_type == "writers.tiledb"
        assert writer.filename is None
        assert writer.options["array_name"] == "tiledb:///arrays/demo"
