"""Custom exceptions for exeqpdal package."""

from __future__ import annotations


class PDALError(Exception):
    """Base exception for all PDAL-related errors."""

    pass


class PDALNotFoundError(PDALError):
    """Raised when PDAL binary cannot be found in system."""

    def __init__(
        self, message: str = "PDAL executable not found in PATH or QGIS installation"
    ) -> None:
        super().__init__(message)
        self.message = message


class PDALExecutionError(PDALError):
    """Raised when PDAL command execution fails."""

    def __init__(
        self,
        message: str,
        returncode: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        command: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.command = command

    def __str__(self) -> str:
        parts = [self.message]
        if self.returncode is not None:
            parts.append(f"Return code: {self.returncode}")
        if self.stderr:
            parts.append(f"STDERR: {self.stderr}")
        return "\n".join(parts)


class PipelineError(PDALError):
    """Raised when pipeline configuration or validation fails."""

    pass


class StageError(PDALError):
    """Raised when stage configuration is invalid."""

    pass


class ValidationError(PDALError):
    """Raised when pipeline validation fails."""

    pass


class DimensionError(PDALError):
    """Raised when dimension access or configuration fails."""

    pass


class MetadataError(PDALError):
    """Raised when metadata parsing or access fails."""

    pass


class ConfigurationError(PDALError):
    """Raised when configuration is invalid."""

    pass
