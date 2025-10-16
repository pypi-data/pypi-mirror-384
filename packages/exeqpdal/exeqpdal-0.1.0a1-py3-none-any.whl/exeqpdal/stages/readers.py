"""PDAL Reader stages."""

from __future__ import annotations

from typing import Any

from exeqpdal.stages.base import ReaderStage


class Reader:
    """Factory class for creating reader stages."""

    @staticmethod
    def arrow(filename: str, **options: Any) -> ReaderStage:
        """Read Arrow/Parquet format."""
        return ReaderStage("readers.arrow", filename=filename, **options)

    @staticmethod
    def bpf(filename: str, **options: Any) -> ReaderStage:
        """Read BPF (Binary Point Format) files."""
        return ReaderStage("readers.bpf", filename=filename, **options)

    @staticmethod
    def buffer(**options: Any) -> ReaderStage:
        """Read from memory buffer."""
        return ReaderStage("readers.buffer", **options)

    @staticmethod
    def copc(filename: str, **options: Any) -> ReaderStage:
        """Read Cloud Optimized Point Cloud (COPC) files."""
        return ReaderStage("readers.copc", filename=filename, **options)

    @staticmethod
    def draco(filename: str, **options: Any) -> ReaderStage:
        """Read Draco compressed point clouds."""
        return ReaderStage("readers.draco", filename=filename, **options)

    @staticmethod
    def ept(filename: str, **options: Any) -> ReaderStage:
        """Read Entwine Point Tiles."""
        return ReaderStage("readers.ept", filename=filename, **options)

    @staticmethod
    def e57(filename: str, **options: Any) -> ReaderStage:
        """Read E57 format files."""
        return ReaderStage("readers.e57", filename=filename, **options)

    @staticmethod
    def faux(filename: str | None = None, **options: Any) -> ReaderStage:
        """Generate synthetic point data for testing."""
        return ReaderStage("readers.faux", filename=filename, **options)

    @staticmethod
    def fbi(filename: str, **options: Any) -> ReaderStage:
        """Read FBI (Flash-Based LIDAR) format."""
        return ReaderStage("readers.fbi", filename=filename, **options)

    @staticmethod
    def gdal(filename: str, **options: Any) -> ReaderStage:
        """Read raster data using GDAL."""
        return ReaderStage("readers.gdal", filename=filename, **options)

    @staticmethod
    def hdf(filename: str, **options: Any) -> ReaderStage:
        """Read HDF5 format files."""
        return ReaderStage("readers.hdf", filename=filename, **options)

    @staticmethod
    def i3s(filename: str, **options: Any) -> ReaderStage:
        """Read I3S (Indexed 3D Scene) format."""
        return ReaderStage("readers.i3s", filename=filename, **options)

    @staticmethod
    def ilvis2(filename: str, **options: Any) -> ReaderStage:
        """Read ILVIS2 NASA format."""
        return ReaderStage("readers.ilvis2", filename=filename, **options)

    @staticmethod
    def las(filename: str, **options: Any) -> ReaderStage:
        """Read ASPRS LAS/LAZ format."""
        return ReaderStage("readers.las", filename=filename, **options)

    @staticmethod
    def matlab(filename: str, **options: Any) -> ReaderStage:
        """Read MATLAB .mat files."""
        return ReaderStage("readers.matlab", filename=filename, **options)

    @staticmethod
    def mbio(filename: str, **options: Any) -> ReaderStage:
        """Read MB-System (marine bathymetry) format."""
        return ReaderStage("readers.mbio", filename=filename, **options)

    @staticmethod
    def memoryview(filename: str | None = None, **options: Any) -> ReaderStage:
        """Read from Python memory view."""
        return ReaderStage("readers.memoryview", filename=filename, **options)

    @staticmethod
    def nitf(filename: str, **options: Any) -> ReaderStage:
        """Read NITF (National Imagery Transmission Format) files."""
        return ReaderStage("readers.nitf", filename=filename, **options)

    @staticmethod
    def numpy(filename: str | None = None, **options: Any) -> ReaderStage:
        """Read from NumPy array."""
        return ReaderStage("readers.numpy", filename=filename, **options)

    @staticmethod
    def obj(filename: str, **options: Any) -> ReaderStage:
        """Read OBJ (Wavefront) mesh format."""
        return ReaderStage("readers.obj", filename=filename, **options)

    @staticmethod
    def optech(filename: str, **options: Any) -> ReaderStage:
        """Read Optech CSD format."""
        return ReaderStage("readers.optech", filename=filename, **options)

    @staticmethod
    def pcd(filename: str, **options: Any) -> ReaderStage:
        """Read PCL Point Cloud Data (PCD) format."""
        return ReaderStage("readers.pcd", filename=filename, **options)

    @staticmethod
    def pgpointcloud(**options: Any) -> ReaderStage:
        """Read from PostgreSQL PointCloud database."""
        return ReaderStage("readers.pgpointcloud", **options)

    @staticmethod
    def ply(filename: str, **options: Any) -> ReaderStage:
        """Read PLY (Polygon File Format) files."""
        return ReaderStage("readers.ply", filename=filename, **options)

    @staticmethod
    def pts(filename: str, **options: Any) -> ReaderStage:
        """Read PTS format (ASCII point cloud)."""
        return ReaderStage("readers.pts", filename=filename, **options)

    @staticmethod
    def ptx(filename: str, **options: Any) -> ReaderStage:
        """Read PTX (Leica) format."""
        return ReaderStage("readers.ptx", filename=filename, **options)

    @staticmethod
    def qfit(filename: str, **options: Any) -> ReaderStage:
        """Read QFIT format."""
        return ReaderStage("readers.qfit", filename=filename, **options)

    @staticmethod
    def rdb(filename: str, **options: Any) -> ReaderStage:
        """Read Riegl RDB format."""
        return ReaderStage("readers.rdb", filename=filename, **options)

    @staticmethod
    def rxp(filename: str, **options: Any) -> ReaderStage:
        """Read Riegl RXP format."""
        return ReaderStage("readers.rxp", filename=filename, **options)

    @staticmethod
    def sbet(filename: str, **options: Any) -> ReaderStage:
        """Read SBET (Smoothed Best Estimate Trajectory) format."""
        return ReaderStage("readers.sbet", filename=filename, **options)

    @staticmethod
    def slpk(filename: str, **options: Any) -> ReaderStage:
        """Read SLPK (Scene Layer Package) format."""
        return ReaderStage("readers.slpk", filename=filename, **options)

    @staticmethod
    def smrmsg(filename: str, **options: Any) -> ReaderStage:
        """Read SMR message format."""
        return ReaderStage("readers.smrmsg", filename=filename, **options)

    @staticmethod
    def stac(filename: str, **options: Any) -> ReaderStage:
        """Read STAC (SpatioTemporal Asset Catalog) items."""
        return ReaderStage("readers.stac", filename=filename, **options)

    @staticmethod
    def terrasolid(filename: str, **options: Any) -> ReaderStage:
        """Read TerraSolid .bin format."""
        return ReaderStage("readers.terrasolid", filename=filename, **options)

    @staticmethod
    def text(filename: str, **options: Any) -> ReaderStage:
        """Read ASCII text files."""
        return ReaderStage("readers.text", filename=filename, **options)

    @staticmethod
    def tiledb(filename: str, **options: Any) -> ReaderStage:
        """Read TileDB arrays."""
        return ReaderStage("readers.tiledb", filename=filename, **options)

    @staticmethod
    def tindex(filename: str, **options: Any) -> ReaderStage:
        """Read from tile index."""
        return ReaderStage("readers.tindex", filename=filename, **options)


# Convenience aliases
def read_las(filename: str, **options: Any) -> ReaderStage:
    """Read ASPRS LAS/LAZ format.

    Args:
        filename: Input LAS/LAZ file path
        **options: Reader options

    Returns:
        Reader stage
    """
    return Reader.las(filename, **options)


def read_copc(filename: str, **options: Any) -> ReaderStage:
    """Read Cloud Optimized Point Cloud (COPC) files.

    Args:
        filename: Input COPC file path
        **options: Reader options

    Returns:
        Reader stage
    """
    return Reader.copc(filename, **options)


def read_text(filename: str, **options: Any) -> ReaderStage:
    """Read ASCII text files.

    Args:
        filename: Input text file path
        **options: Reader options

    Returns:
        Reader stage
    """
    return Reader.text(filename, **options)
