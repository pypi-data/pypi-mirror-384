"""PDAL CLI execution engine."""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

from exeqpdal.core.config import config
from exeqpdal.exceptions import PDALExecutionError

logger = logging.getLogger(__name__)


class Executor:
    """Execute PDAL CLI commands."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize executor.

        Args:
            verbose: Enable verbose PDAL output
        """
        self.verbose = verbose or config.verbose

    def execute_pipeline(
        self,
        pipeline_json: str | dict[str, Any],
        stream_mode: bool | None = None,
        metadata: bool = True,
    ) -> tuple[str, str, int, dict[str, Any] | None]:
        """Execute PDAL pipeline.

        Args:
            pipeline_json: Pipeline JSON string or dict
            stream_mode: Force stream mode (True), standard mode (False), or auto (None)
            metadata: Include metadata in output

        Returns:
            Tuple of (stdout, stderr, returncode, metadata_dict)

        Raises:
            PDALExecutionError: If pipeline execution fails
        """
        # Convert dict to JSON string if needed
        if isinstance(pipeline_json, dict):
            pipeline_json = json.dumps(pipeline_json, indent=2)

        # Write pipeline to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(pipeline_json)
            pipeline_file = Path(f.name)

        try:
            # Build command
            cmd = [str(config.pdal_path), "pipeline", str(pipeline_file)]

            # Add stream mode flags
            if stream_mode is True:
                cmd.append("--stream")
            elif stream_mode is False:
                cmd.append("--nostream")

            # Add metadata output
            metadata_file: Path | None = None
            if metadata:
                metadata_file = pipeline_file.with_suffix(".metadata.json")
                cmd.extend(["--metadata", str(metadata_file)])

            # Add verbose flag
            if self.verbose:
                cmd.append("--verbose")
                cmd.append("8")

            logger.debug(f"Executing PDAL command: {' '.join(cmd)}")

            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            # Read metadata if generated
            metadata_dict: dict[str, Any] | None = None
            if metadata_file and metadata_file.exists():
                try:
                    with metadata_file.open(encoding="utf-8") as f:
                        metadata_dict = json.load(f)
                        logger.debug(f"Metadata loaded: {len(str(metadata_dict))} bytes")
                except Exception as e:
                    logger.warning(f"Failed to read metadata: {e}")

            # Check for errors
            if result.returncode != 0:
                raise PDALExecutionError(
                    "PDAL pipeline execution failed",
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    command=cmd,
                )

            logger.info(f"Pipeline executed successfully (return code: {result.returncode})")
            return result.stdout, result.stderr, result.returncode, metadata_dict

        finally:
            # Cleanup temporary files
            try:
                if pipeline_file.exists():
                    pipeline_file.unlink()
                if metadata_file and metadata_file.exists():
                    metadata_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary files: {e}")

    def execute_application(
        self,
        app_name: str,
        args: list[str],
        input_file: str | Path | None = None,
    ) -> tuple[str, str, int]:
        """Execute PDAL application.

        Args:
            app_name: Application name (e.g., 'info', 'translate')
            args: Application arguments
            input_file: Optional input file path

        Returns:
            Tuple of (stdout, stderr, returncode)

        Raises:
            PDALExecutionError: If application execution fails
        """
        # Build command
        cmd = [str(config.pdal_path), app_name]

        # Add input file if provided
        if input_file:
            cmd.append(str(input_file))

        # Add arguments
        cmd.extend(args)

        # Add verbose flag
        if self.verbose:
            cmd.append("--verbose")
            cmd.append("8")

        logger.debug(f"Executing PDAL command: {' '.join(cmd)}")

        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        # Check for errors
        if result.returncode != 0:
            raise PDALExecutionError(
                f"PDAL {app_name} execution failed",
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=cmd,
            )

        logger.info(f"Application '{app_name}' executed successfully")
        return result.stdout, result.stderr, result.returncode

    def validate_pipeline(self, pipeline_json: str | dict[str, Any]) -> tuple[bool, bool, str]:
        """Validate pipeline without executing.

        Args:
            pipeline_json: Pipeline JSON string or dict

        Returns:
            Tuple of (is_valid, is_streamable, message)

        Raises:
            PDALExecutionError: If validation command fails
        """
        # Convert dict to JSON string if needed
        if isinstance(pipeline_json, dict):
            pipeline_json = json.dumps(pipeline_json, indent=2)

        # Write pipeline to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(pipeline_json)
            pipeline_file = Path(f.name)

        try:
            # Build validation command
            cmd = [
                str(config.pdal_path),
                "pipeline",
                str(pipeline_file),
                "--validate",
            ]

            logger.debug(f"Validating pipeline: {' '.join(cmd)}")

            # Execute validation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            is_valid = result.returncode == 0
            is_streamable = "streamable" in result.stdout.lower()

            message = result.stdout if is_valid else result.stderr

            logger.info(f"Pipeline validation: valid={is_valid}, streamable={is_streamable}")
            return is_valid, is_streamable, message

        finally:
            # Cleanup
            try:
                if pipeline_file.exists():
                    pipeline_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup validation file: {e}")

    def get_driver_info(self, driver_name: str) -> dict[str, Any]:
        """Get information about a PDAL driver.

        Args:
            driver_name: Driver name (e.g., 'readers.las', 'filters.range')

        Returns:
            Driver information dictionary

        Raises:
            PDALExecutionError: If command fails
        """
        cmd = [str(config.pdal_path), "info", "--drivers", driver_name]

        logger.debug(f"Getting driver info: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise PDALExecutionError(
                f"Failed to get driver info for {driver_name}",
                returncode=result.returncode,
                stderr=result.stderr,
                command=cmd,
            )

        try:
            return cast("dict[str, Any]", json.loads(result.stdout))
        except json.JSONDecodeError as e:
            raise PDALExecutionError(
                f"Failed to parse driver info: {e}",
                stdout=result.stdout,
                command=cmd,
            ) from e


# Global executor instance
executor = Executor()
