# exeqpdal

Alpha-stage, typed Python API for driving the PDAL command-line interface (CLI).

`exeqpdal` focuses on being a reliable subprocess wrapper around the PDAL CLI so that Python
projects – including QGIS plugins – can assemble and run PDAL pipelines without shipping
C++ bindings. The current release series is `0.1.0a*` and is still stabilising APIs and
coverage.

## Features

-   **Pythonic pipelines** – build PDAL JSON using `Reader`, `Filter`, and `Writer`
    factories chained with the `|` operator, then execute with `Pipeline`.
-   **CLI-first design** – no native extensions; every operation delegates to the PDAL
    executable via `subprocess.run`.
-   **Strict typing** – the package ships `py.typed`, is developed under `mypy --strict`,
    and exposes typed factory helpers.
-   **Convenience apps** – wrappers for PDAL tools such as `info`, `translate`, `merge`, `split`,
    `tile`, and `tindex`.
-   **Broad stage coverage** – factories currently expose ~40 readers, 80+ filters, and 25 writers.
    Coverage is expanding; unsupported drivers can still be addressed through custom JSON.
-   **QGIS-friendly** – automatic PDAL discovery checks PATH, `PDAL_EXECUTABLE`, and
    common QGIS 3.4x Windows installs.

## Prerequisites

-   Python 3.12+
-   PDAL CLI installed and accessible (system PATH, `PDAL_EXECUTABLE`, or detected in QGIS on
    Windows)

## Installation

The first public alpha will be published to PyPI using GitHub Actions. Once the release is
live, you can install it directly (include `--pre` while the project is in alpha):

```bash
pip install --pre exeqpdal
```

Until the package is uploaded, install from a local clone:

```bash
# From the project root
pip install -e .

# Or install with development extras
uv pip install -e ".[dev]"
```

## Quick Start

### Convert a File

```python
import exeqpdal as pdal

pdal.translate("input.las", "output.laz")
```

### Filter Ground Points

```python
import exeqpdal as pdal

pipeline = (
    pdal.Reader.las("input.las")
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.las("ground_only.las")
)
pipeline.execute()
```

### Get File Information

```python
from exeqpdal import info

info_data = info("input.las", stats=True)
print(info_data)
```

For more examples, see the [examples documentation](docs/examples.md).

## Supported Components

Factory helpers cover the most commonly used PDAL readers, writers, and filters. For the
definitive driver reference, consult the
[PDAL documentation](https://pdal.io/en/stable/stages/stages.html). If a driver is
missing, you can still run it by injecting raw dictionaries into a `Pipeline`.

## Error Handling

`exeqpdal` raises custom exceptions to surface PDAL CLI failures and configuration issues.

```python
import exeqpdal as pdal

try:
    pipeline = pdal.Pipeline(
        pdal.Reader.las("non_existent_file.las") | pdal.Writer.las("output.las")
    )
    pipeline.execute()
except pdal.PipelineError as exc:
    print(f"Pipeline execution failed: {exc}")
```

## Configuration

### Custom PDAL Path

If PDAL is not in your system's PATH, you can set the path to the `pdal` executable manually:

```python
import exeqpdal as pdal

pdal.set_pdal_path("/path/to/your/pdal")
```

### Verbose Output

Enable verbose output to see the PDAL command being executed and its output:

```python
import exeqpdal as pdal

pdal.set_verbose(True)
```

## Project Status & Limitations

-   `Pipeline.arrays` is not yet implemented – it currently returns an empty list even after
    execution.
-   Integration tests use six LAZ/COPC test datasets in `tests/test_data_laz/` covering various
    scenarios (filtered/non-filtered data, small/mid/large sizes, LAS/COPC formats). Tests
    automatically skip when PDAL or test data are unavailable. See `tests/test_data_laz/DATASET.md`
    for dataset details.
-   Stage coverage is broad but incomplete. Missing drivers can be added by extending the factory
    modules or by building custom JSON.

## License

`exeqpdal` is licensed under the MIT License.

This project is a wrapper around the PDAL command-line tool, which is licensed under the
BSD license. When using `exeqpdal`, you are also using PDAL, and you should be aware of
its license.

If you are using `exeqpdal` in a QGIS plugin, you should also be aware of the QGIS license (GPLv2+).
