"""Unit tests for exeqpdal configuration helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import exeqpdal as pdal
from exeqpdal.core.config import Config
from exeqpdal.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pathlib import Path


class TestConfig:
    """Validate configuration plumbing without invoking PDAL."""

    def test_config_singleton(self) -> None:
        """The public config object should behave as a singleton alias."""
        assert pdal.config is pdal.config

    def test_set_pdal_path_valid(self, tmp_path: Path) -> None:
        """Setting pdal executable path accepts existing executables."""
        pdal_exe = tmp_path / "pdal"
        pdal_exe.touch()
        pdal_exe.chmod(0o755)

        config = Config()
        config.set_pdal_path(pdal_exe)
        assert config._pdal_path == pdal_exe

    def test_set_pdal_path_nonexistent(self) -> None:
        """Non-existent PDAL path raises ConfigurationError."""
        config = Config()
        with pytest.raises(ConfigurationError, match="not found"):
            config.set_pdal_path("/nonexistent/path/to/pdal")

    def test_verbose_setting(self) -> None:
        """Config toggles verbose flag."""
        config = Config()

        config.set_verbose(True)
        assert config.verbose

        config.set_verbose(False)
        assert not config.verbose
