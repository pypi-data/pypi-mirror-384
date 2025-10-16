"""Base classes for PDAL stages."""

from __future__ import annotations

from abc import ABC
from typing import Any

from exeqpdal.exceptions import StageError


class Stage(ABC):  # noqa: B024 - Concrete base class with ABC for semantic grouping
    """Base class for all PDAL stages."""

    def __init__(
        self,
        stage_type: str,
        filename: str | None = None,
        tag: str | None = None,
        inputs: list[str | Stage] | None = None,
        **options: Any,
    ) -> None:
        """Initialize stage.

        Args:
            stage_type: PDAL stage type (e.g., 'readers.las', 'filters.range')
            filename: Input/output filename (for readers/writers)
            tag: Stage tag for referencing
            inputs: Input stages or tags
            **options: Stage-specific options
        """
        self.stage_type = stage_type
        self.filename = filename
        self.tag = tag
        self.inputs = inputs or []
        self.options = options

    def to_dict(self) -> dict[str, Any]:
        """Convert stage to pipeline dictionary.

        Returns:
            Stage dictionary for pipeline JSON
        """
        stage_dict: dict[str, Any] = {"type": self.stage_type}

        if self.filename:
            stage_dict["filename"] = self.filename

        if self.tag:
            stage_dict["tag"] = self.tag

        if self.inputs:
            # Convert Stage objects to tags
            input_tags = []
            for inp in self.inputs:
                if isinstance(inp, Stage):
                    if inp.tag:
                        input_tags.append(inp.tag)
                    else:
                        raise StageError(
                            f"Input stage {inp.stage_type} must have a tag when used as input"
                        )
                else:
                    input_tags.append(inp)
            stage_dict["inputs"] = input_tags

        # Add all options
        stage_dict.update(self.options)

        return stage_dict

    def __or__(self, other: Stage) -> Stage:
        """Pipe operator for chaining stages.

        Args:
            other: Next stage in pipeline

        Returns:
            The other stage with this stage as input
        """
        if not isinstance(other, Stage):
            raise StageError(f"Cannot pipe to {type(other)}, must be a Stage")

        # Set self as input to other
        if not other.inputs:
            other.inputs = []

        # Auto-generate tag if needed
        if not self.tag:
            self.tag = f"stage_{id(self)}"

        other.inputs.append(self)
        return other

    def __repr__(self) -> str:
        """String representation of stage."""
        parts = [self.stage_type]
        if self.filename:
            parts.append(f"filename={self.filename}")
        if self.tag:
            parts.append(f"tag={self.tag}")
        return f"{self.__class__.__name__}({', '.join(parts)})"


class ReaderStage(Stage):
    """Base class for reader stages."""

    def __init__(
        self,
        reader_type: str,
        filename: str | None = None,
        tag: str | None = None,
        **options: Any,
    ) -> None:
        """Initialize reader stage.

        Args:
            reader_type: Reader type (e.g., 'readers.las')
            filename: Input filename
            tag: Stage tag
            **options: Reader-specific options
        """
        super().__init__(
            stage_type=reader_type,
            filename=filename,
            tag=tag,
            inputs=None,
            **options,
        )


class FilterStage(Stage):
    """Base class for filter stages."""

    def __init__(
        self,
        filter_type: str,
        tag: str | None = None,
        inputs: list[str | Stage] | None = None,
        **options: Any,
    ) -> None:
        """Initialize filter stage.

        Args:
            filter_type: Filter type (e.g., 'filters.range')
            tag: Stage tag
            inputs: Input stages or tags
            **options: Filter-specific options
        """
        super().__init__(
            stage_type=filter_type,
            filename=None,
            tag=tag,
            inputs=inputs,
            **options,
        )


class WriterStage(Stage):
    """Base class for writer stages."""

    def __init__(
        self,
        writer_type: str,
        filename: str | None = None,
        tag: str | None = None,
        inputs: list[str | Stage] | None = None,
        **options: Any,
    ) -> None:
        """Initialize writer stage.

        Args:
            writer_type: Writer type (e.g., 'writers.las')
            filename: Output filename
            tag: Stage tag
            inputs: Input stages or tags
            **options: Writer-specific options
        """
        super().__init__(
            stage_type=writer_type,
            filename=filename,
            tag=tag,
            inputs=inputs,
            **options,
        )
