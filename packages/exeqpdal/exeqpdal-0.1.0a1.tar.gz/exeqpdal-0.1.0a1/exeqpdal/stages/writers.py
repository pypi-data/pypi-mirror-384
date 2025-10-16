"""PDAL Writer stages."""

from __future__ import annotations

from typing import Any

from exeqpdal.stages.base import WriterStage


class Writer:
    """Factory class for creating writer stages."""

    @staticmethod
    def arrow(filename: str, **options: Any) -> WriterStage:
        """Write Arrow/Parquet format."""
        return WriterStage("writers.arrow", filename=filename, **options)

    @staticmethod
    def bpf(filename: str, **options: Any) -> WriterStage:
        """Write BPF (Binary Point Format) files."""
        return WriterStage("writers.bpf", filename=filename, **options)

    @staticmethod
    def copc(filename: str, **options: Any) -> WriterStage:
        """Write Cloud Optimized Point Cloud (COPC) files."""
        return WriterStage("writers.copc", filename=filename, **options)

    @staticmethod
    def draco(filename: str, **options: Any) -> WriterStage:
        """Write Draco compressed point clouds."""
        return WriterStage("writers.draco", filename=filename, **options)

    @staticmethod
    def ept_addon(**options: Any) -> WriterStage:
        """Write EPT addon data."""
        return WriterStage("writers.ept_addon", **options)

    @staticmethod
    def e57(filename: str, **options: Any) -> WriterStage:
        """Write E57 format files."""
        return WriterStage("writers.e57", filename=filename, **options)

    @staticmethod
    def fbi(filename: str, **options: Any) -> WriterStage:
        """Write FBI (Flash-Based LIDAR) format."""
        return WriterStage("writers.fbi", filename=filename, **options)

    @staticmethod
    def fbx(filename: str, **options: Any) -> WriterStage:
        """Write FBX (Autodesk) format."""
        return WriterStage("writers.fbx", filename=filename, **options)

    @staticmethod
    def gdal(filename: str, **options: Any) -> WriterStage:
        """Write raster data using GDAL."""
        return WriterStage("writers.gdal", filename=filename, **options)

    @staticmethod
    def gltf(filename: str, **options: Any) -> WriterStage:
        """Write glTF (GL Transmission Format) files."""
        return WriterStage("writers.gltf", filename=filename, **options)

    @staticmethod
    def las(filename: str, **options: Any) -> WriterStage:
        """Write ASPRS LAS/LAZ format."""
        return WriterStage("writers.las", filename=filename, **options)

    @staticmethod
    def matlab(filename: str, **options: Any) -> WriterStage:
        """Write MATLAB .mat files."""
        return WriterStage("writers.matlab", filename=filename, **options)

    @staticmethod
    def nitf(filename: str, **options: Any) -> WriterStage:
        """Write NITF (National Imagery Transmission Format) files."""
        return WriterStage("writers.nitf", filename=filename, **options)

    @staticmethod
    def null(**options: Any) -> WriterStage:
        """Null writer (discards output, useful for testing)."""
        return WriterStage("writers.null", **options)

    @staticmethod
    def ogr(filename: str, **options: Any) -> WriterStage:
        """Write OGR vector formats."""
        return WriterStage("writers.ogr", filename=filename, **options)

    @staticmethod
    def pcd(filename: str, **options: Any) -> WriterStage:
        """Write PCL Point Cloud Data (PCD) format."""
        return WriterStage("writers.pcd", filename=filename, **options)

    @staticmethod
    def pgpointcloud(**options: Any) -> WriterStage:
        """Write to PostgreSQL PointCloud database."""
        return WriterStage("writers.pgpointcloud", **options)

    @staticmethod
    def ply(filename: str, **options: Any) -> WriterStage:
        """Write PLY (Polygon File Format) files."""
        return WriterStage("writers.ply", filename=filename, **options)

    @staticmethod
    def raster(filename: str, **options: Any) -> WriterStage:
        """Write raster output."""
        return WriterStage("writers.raster", filename=filename, **options)

    @staticmethod
    def sbet(filename: str, **options: Any) -> WriterStage:
        """Write SBET (Smoothed Best Estimate Trajectory) format."""
        return WriterStage("writers.sbet", filename=filename, **options)

    @staticmethod
    def text(filename: str, **options: Any) -> WriterStage:
        """Write ASCII text files."""
        return WriterStage("writers.text", filename=filename, **options)

    @staticmethod
    def tiledb(array_name: str | None = None, **options: Any) -> WriterStage:
        """Write TileDB arrays."""
        if array_name is not None:
            options.setdefault("array_name", array_name)
        return WriterStage("writers.tiledb", **options)


# Convenience aliases
def write_las(filename: str, **options: Any) -> WriterStage:
    """Write ASPRS LAS/LAZ format.

    Args:
        filename: Output LAS/LAZ file path
        **options: Writer options (e.g., compression="laszip")

    Returns:
        Writer stage
    """
    return Writer.las(filename, **options)


def write_copc(filename: str, **options: Any) -> WriterStage:
    """Write Cloud Optimized Point Cloud (COPC) files.

    Args:
        filename: Output COPC file path
        **options: Writer options

    Returns:
        Writer stage
    """
    return Writer.copc(filename, **options)


def write_text(filename: str, **options: Any) -> WriterStage:
    """Write ASCII text files.

    Args:
        filename: Output text file path
        **options: Writer options

    Returns:
        Writer stage
    """
    return Writer.text(filename, **options)
