"""Configuration management for exeqpdal."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Final

from exeqpdal.exceptions import ConfigurationError, PDALNotFoundError

logger = logging.getLogger(__name__)


class Config:
    """Global configuration for exeqpdal."""

    def __init__(self) -> None:
        self._pdal_path: Path | None = None
        self._qgis_root: Path | None = None
        self._verbose: bool = False

    @property
    def pdal_path(self) -> Path:
        """Get path to PDAL executable.

        Returns:
            Path to PDAL executable

        Raises:
            PDALNotFoundError: If PDAL executable cannot be found
        """
        if self._pdal_path is None:
            self._pdal_path = self._find_pdal_executable()
        return self._pdal_path

    def set_pdal_path(self, path: str | Path) -> None:
        """Set custom PDAL executable path.

        Args:
            path: Path to PDAL executable

        Raises:
            ConfigurationError: If path is invalid or not executable
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise ConfigurationError(f"PDAL executable not found at: {path}")
        if not path_obj.is_file():
            raise ConfigurationError(f"PDAL path is not a file: {path}")

        # Check if executable (Unix-like systems)
        if platform.system() != "Windows" and not os.access(path_obj, os.X_OK):
            raise ConfigurationError(f"PDAL binary is not executable: {path}")

        self._pdal_path = path_obj
        logger.info(f"PDAL path set to: {path_obj}")

    @property
    def verbose(self) -> bool:
        """Get verbose output setting."""
        return self._verbose

    def set_verbose(self, verbose: bool) -> None:
        """Set verbose output mode.

        Args:
            verbose: Enable verbose PDAL output
        """
        self._verbose = verbose
        logger.info(f"Verbose mode: {verbose}")

    def _find_pdal_executable(self) -> Path:
        """Find PDAL executable in system.

        Returns:
            Path to PDAL executable

        Raises:
            PDALNotFoundError: If PDAL cannot be found
        """
        # Check environment variable first
        env_path = os.environ.get("PDAL_EXECUTABLE")
        if env_path:
            path = Path(env_path)
            if path.exists() and path.is_file():
                logger.info(f"Found PDAL from PDAL_EXECUTABLE: {path}")
                return path
            logger.warning(f"PDAL_EXECUTABLE points to invalid path: {env_path}")

        # Try system PATH
        system_pdal = self._find_in_path()
        if system_pdal:
            logger.info(f"Found PDAL in system PATH: {system_pdal}")
            return system_pdal

        # Try QGIS installation (Windows)
        if platform.system() == "Windows":
            qgis_pdal = self._find_in_qgis()
            if qgis_pdal:
                logger.info(f"Found PDAL in QGIS installation: {qgis_pdal}")
                return qgis_pdal

        raise PDALNotFoundError(
            "PDAL executable not found. Please install PDAL or set PDAL_EXECUTABLE environment variable."
        )

    def _find_in_path(self) -> Path | None:
        """Find PDAL in system PATH.

        Returns:
            Path to PDAL if found, None otherwise
        """
        pdal_name = "pdal.exe" if platform.system() == "Windows" else "pdal"

        # Use shutil.which for cross-platform search
        which_result = shutil.which(pdal_name)
        if which_result:
            return Path(which_result)

        # On Unix-like systems, also try 'which' command
        if platform.system() != "Windows":
            try:
                result = subprocess.run(
                    ["which", "pdal"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return Path(result.stdout.strip())
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        return None

    def _find_in_qgis(self) -> Path | None:
        """Find PDAL in QGIS installation (Windows only).

        Returns:
            Path to PDAL if found, None otherwise
        """
        if platform.system() != "Windows":
            return None

        # Common QGIS installation paths
        qgis_paths = [
            Path(os.environ.get("QGIS_PREFIX_PATH", "")),
            Path("C:/Program Files/QGIS 3.40"),
            Path("C:/Program Files/QGIS 3.42"),
            Path("C:/Program Files/QGIS 3.44"),
            Path("C:/OSGeo4W64"),
            Path("C:/OSGeo4W"),
        ]

        # Add QGIS paths from environment
        osgeo_root = os.environ.get("OSGEO4W_ROOT")
        if osgeo_root:
            qgis_paths.insert(0, Path(osgeo_root))

        for qgis_root in qgis_paths:
            if not qgis_root.exists():
                continue

            # Try common locations within QGIS
            possible_paths = [
                qgis_root / "bin" / "pdal.exe",
                qgis_root / "apps" / "pdal" / "bin" / "pdal.exe",
                qgis_root / "apps" / "bin" / "pdal.exe",
            ]

            for path in possible_paths:
                if path.exists() and path.is_file():
                    self._qgis_root = qgis_root
                    return path

        return None

    def get_pdal_version(self) -> str:
        """Get PDAL version string.

        Returns:
            PDAL version string

        Raises:
            PDALNotFoundError: If PDAL cannot be found or executed
        """
        try:
            result = subprocess.run(
                [str(self.pdal_path), "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            version_output = result.stdout.strip()
            logger.debug(f"PDAL version: {version_output}")
            return version_output
        except subprocess.CalledProcessError as e:
            raise PDALNotFoundError(f"Failed to get PDAL version: {e}") from e
        except FileNotFoundError as e:
            raise PDALNotFoundError(f"PDAL executable not found: {e}") from e

    def validate_pdal(self) -> bool:
        """Validate that PDAL is properly installed and accessible.

        Returns:
            True if PDAL is valid

        Raises:
            PDALNotFoundError: If PDAL cannot be found or validated
        """
        try:
            version = self.get_pdal_version()
            logger.info(f"PDAL validation successful: {version}")
            return True
        except Exception as e:
            raise PDALNotFoundError(f"PDAL validation failed: {e}") from e


# Global configuration instance
config: Final[Config] = Config()


def set_pdal_path(path: str | Path) -> None:
    """Set custom PDAL executable path.

    Args:
        path: Path to PDAL executable
    """
    config.set_pdal_path(path)


def get_pdal_path() -> Path:
    """Get path to PDAL executable.

    Returns:
        Path to PDAL executable
    """
    return config.pdal_path


def set_verbose(verbose: bool) -> None:
    """Set verbose output mode.

    Args:
        verbose: Enable verbose PDAL output
    """
    config.set_verbose(verbose)


def get_pdal_version() -> str:
    """Get PDAL version string.

    Returns:
        PDAL version string
    """
    return config.get_pdal_version()


def validate_pdal() -> bool:
    """Validate that PDAL is properly installed and accessible.

    Returns:
        True if PDAL is valid
    """
    return config.validate_pdal()
