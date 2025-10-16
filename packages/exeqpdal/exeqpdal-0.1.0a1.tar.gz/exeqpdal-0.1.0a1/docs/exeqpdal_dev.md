# exeqpdal Development Guide

**Audience**: core maintainers and contributors preparing the `0.1.0a` alpha series for publication  
**Last updated**: 2025-10-14 (UTC)

This guide captures the current, real state of the codebase so contributors can implement features,
debug issues, and ship a professional-quality package without relying on stale assumptions.

---

## 1. Purpose & Scope

- Document the runtime architecture (`core`, `stages`, `apps`, `types`, `exceptions`).
- Explain how the PDAL CLI is discovered, validated, and invoked.
- Summarise the development toolchain and verification commands.
- Highlight gaps that must be addressed before or shortly after the first PyPI release.

---

## 2. Environment

### 2.1 Requirements

- **Python**: 3.12 (tested under `pyproject.toml`)
- **PDAL CLI**: 2.5+ recommended. Integration tests use stages such as `filters.smrf`,
  `filters.python`, COPC readers/writers, and GDAL raster outputs.
- **Operating systems**: Linux, macOS, Windows (QGIS bundle support implemented for Windows).
- **Optional**: QGIS 3.40–3.44 on Windows for automatic PDAL discovery.

### 2.2 Installation

```bash
# Install development dependencies (recommended)
uv pip install -e ".[dev]"

# Fallback without uv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2.3 Command Reference

```bash
# Format before linting
ruff format .
ruff check .

# Strict typing
mypy exeqpdal

# Tests – run full suite when PDAL + test datasets are available
pytest tests/

# Skip integrations if PDAL or test datasets are unavailable
pytest tests/ -m "not integration"
```

---

## 3. Repository Layout

```
exeqpdal/
├── __init__.py        # Public API surface
├── exceptions.py     # Exception hierarchy
├── core/             # Configuration, executor, pipeline orchestration
├── stages/           # Reader/Filter/Writer factories and Stage base types
├── apps/             # Wrappers around PDAL CLI applications
└── types/            # Dimension helpers and enumerations

docs/                 # Markdown documentation (no runtime code)
tests/                # Pytest suite (unit + integration)
dist/                 # Local build artefacts (not committed upstream)
```

---

## 4. Core Modules

### 4.1 `exeqpdal.core.config`

- `Config` lazily discovers the PDAL executable via:
  1. `PDAL_EXECUTABLE` environment variable.
  2. `PATH` lookup (`shutil.which` / `which`).
  3. QGIS installation paths on Windows (`C:\Program Files\QGIS 3.4x\bin\pdal.exe`, `OSGEO4W` roots).
- Public helpers: `set_pdal_path`, `get_pdal_path`, `get_pdal_version`, `validate_pdal`,
  `set_verbose`.
- Raises `PDALNotFoundError` or `ConfigurationError` when discovery fails or the path is invalid.

### 4.2 `exeqpdal.core.executor`

- Provides a single `Executor` instance (`executor`).
- `execute_pipeline` writes pipeline JSON to a temp file, calls `pdal pipeline`, optionally collects
  metadata, and cleans up files. Raises `PDALExecutionError` on non-zero return codes.
- `execute_application` wraps invocations such as `pdal info` or `pdal translate`.
- `validate_pipeline` runs `pdal pipeline --validate`.
- `get_driver_info` queries `pdal info --drivers`.

### 4.3 `exeqpdal.core.pipeline.Pipeline`

- Accepts JSON, dict, list, or a terminal `Stage` instance.
- `execute()` returns the processed point count (best-effort) and raises `PipelineError` on failure.
- `validate()` returns `True` if the PDAL CLI reports success; stores streamability metadata.
- `.metadata`, `.log`, and `.arrays` properties require a successful `.execute()` call.
- `.arrays` is a planned feature and currently returns an empty list (see §11).

### 4.4 `exeqpdal.stages`

- `Stage` base class plus concrete `ReaderStage`, `FilterStage`, `WriterStage`.
- Factory classes for stage creation:
  - `Reader`: ~40 static constructors (e.g., `Reader.las`, `Reader.ept`, `Reader.copc`).
  - `Filter`: 80+ static constructors (ground classification, sampling, clustering, reprojection,
    rasterisation, scripting, etc.).
  - `Writer`: 25 static constructors (LAS/LAZ, COPC, GDAL, E57, TileDB, text, GLTF, etc.).
- Convenience helpers (`read_las`, `write_las`, etc.) wrap a subset of the factories.
- Factories return lightweight stage objects with keyword options forwarded verbatim to PDAL.

### 4.5 `exeqpdal.apps`

- `info.py`: typed wrapper around `pdal info` with helpers (`get_count`, `get_bounds`, `get_stats`…).
- `translate.py`: `translate`/`convert` helper for format conversion.
- `pipeline_apps.py`: wrappers for `merge`, `split`, `tile`, `tindex`, and `pipeline`.

### 4.6 `exeqpdal.types`

- Enumerations and helper classes for PDAL dimensions (`Dimension`, `DataType`, `Classification`).
- `DIMENSION_TYPES` maps enumeration values to PDAL CLI descriptors.

### 4.7 `exeqpdal.exceptions`

- Root `PDALError` plus specialised subclasses:
  - `PDALNotFoundError`, `ConfigurationError`
  - `PDALExecutionError`, `PipelineError`, `StageError`
  - `ValidationError`, `MetadataError`, `DimensionError`
- `Pipeline` wraps underlying `PDALExecutionError` instances in `PipelineError`.

---

## 5. Pipeline Execution Flow

1. User constructs a pipeline either by:
   - Chaining stages (`Reader.las(...) | Filter.range(...) | Writer.las(...)`), or
   - Providing a JSON string/dict/list of stage dictionaries.
2. `Pipeline` walks backwards through the chained stages to assemble PDAL JSON.
3. `Executor.execute_pipeline` writes JSON to disk, forms the CLI call, and captures stdout/stderr.
4. Metadata (if produced) is parsed to derive the point count; stdout fallback is best-effort.
5. `Pipeline` stores execution state (`_executed`, `_metadata`, `_log`).

**Important behaviours**

- Exceptions from the executor surface as `PipelineError`.
- `Pipeline.validate()` does not mutate execution state; it reuses the same JSON.
- `Pipeline.arrays` is a stub – the design allows future NumPy array extraction.
- `Pipeline.is_streamable` defers to `validate()` when necessary.

---

## 6. Stage Factory Usage & Extension

```python
import exeqpdal as pdal

terrain = (
    pdal.Reader.las("input.las", default_srs="EPSG:3949")
    | pdal.Filter.smrf(slope=0.1, sensitivity=1.2)
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.gdal(filename="dtm.tif", resolution=1.0, output_type="min")
)

count = terrain.execute()
```

- Factories accept keyword arguments that map directly to PDAL options (underscores become dots in
  CLI contexts such as `translate`).
- Missing drivers can be issued manually:

  ```python
  from exeqpdal.stages.base import Stage

  custom_stage = Stage("filters.mystage", foo="bar")
  pipeline = pdal.Pipeline(custom_stage | pdal.Writer.null())
  ```

- Use `executor.get_driver_info("filters.outlier")` to inspect available options in a given PDAL
  installation (raises `PDALExecutionError` if PDAL lacks the driver).

---

## 7. Application Wrappers

High-level helpers live in `exeqpdal.apps` and mirror PDAL CLI semantics.

| Function          | Underlying command                 | Notes |
|-------------------|------------------------------------|-------|
| `info`            | `pdal info`                        | Returns parsed JSON as `dict[str, Any]`. |
| `translate`/`convert` | `pdal translate`               | Accepts `filters`, `reader`, `writer`, and stage-prefixed keyword options. |
| `merge`           | `pdal merge`                       | Merges source files to a single output. |
| `split`           | `pdal split`                       | Supports length/capacity options. |
| `tile`            | `pdal tile`                        | Handles length/origin/buffer arguments. |
| `tindex`          | `pdal tindex create`               | Produces GeoJSON tile indexes. |
| `pipeline_app`    | `pdal pipeline`                    | Executes or validates pipelines stored on disk. |

All wrappers raise `PDALExecutionError` if PDAL exits with a non-zero status.

---

## 8. Configuration & Discovery Patterns

```python
import exeqpdal as pdal

# Validate availability early
pdal.validate_pdal()
print(pdal.get_pdal_version())

# Override path when bundles are not on PATH
pdal.set_pdal_path("/Applications/QGIS.app/Contents/MacOS/bin/pdal")
```

Detection order:

1. `PDAL_EXECUTABLE` environment variable.
2. `PATH` search (`shutil.which`).
3. Windows-specific QGIS roots (`QGIS_PREFIX_PATH`, `OSGEO4W_ROOT`, or common install directories).

Verbose mode (`set_verbose(True)`) appends `--verbose 8` to every CLI invocation for debugging.

---

## 9. Exception Handling Guidelines

- Prefer catching `PipelineError` around `Pipeline.execute()` and `ValidationError` around
  `Pipeline.validate()`.
- Application helper failures propagate `PDALExecutionError`.
- `PDALNotFoundError` signals discovery issues – surfaced by `get_pdal_path`, `get_pdal_version`,
  and `validate_pdal`.
- Distinguish between configuration missteps (`ConfigurationError`) and runtime CLI failures
  (`PDALExecutionError`) when surfacing errors to callers.

Example:

```python
import exeqpdal as pdal

try:
    pipeline = pdal.Pipeline(
        pdal.Reader.las("input.las") | pdal.Writer.las("output.las")
    )
    pipeline.execute()
except pdal.PipelineError as exc:
    raise RuntimeError(f"PDAL pipeline failed: {exc}") from exc
```

---

## 10. Testing & Quality Assurance

- Unit tests live under `tests/` and are enabled by default.
- Integration tests are marked with `@pytest.mark.integration` and require:
  - PDAL CLI available on the test runner.
  - Six LAZ/COPC test datasets in `tests/test_data_laz/` (see `DATASET.md` for details).
  - Tests automatically skip when PDAL or test data are unavailable.
- Writer tests store artefacts under `tests/laz_to_writers/outputs/`; this directory is gitignored and
  should remain untracked.
- Continuous verification sequence (minimum before a PR):

  ```bash
  ruff format .
  ruff check .
  mypy exeqpdal
  pytest tests/ -m "not integration"
  ```

  Run the full test suite (without the marker filter) before tagging a release.

---

## 11. Known Gaps & Next Steps

- **Array harvesting**: `Pipeline.arrays` is a placeholder. Options include reading PDAL-generated
  numpy output, exposing PDAL’s pipeline writers, or removing the property until implemented.
- **Stage coverage**: Factories cover the majority of core PDAL drivers but some niche readers,
  filters, and writers are missing. The recommended addition path is to extend the relevant factory
  module and add regression tests.
- **Metadata parsing**: Point counts are derived from metadata when present. Additional parsing may
  be required for complex pipelines or when PDAL emits counts only in stdout.
- **Error messages**: Surface more of `PDALExecutionError.stdout/stderr` through `PipelineError` to
  aid troubleshooting.
- **Packaging**: The upload workflow (e.g., `twine`) has not yet been scripted; manual verification
  is required (`python -m build`, `twine check dist/*`).

---

## 12. Release Preparation Checklist

1. Ensure documentation is current (`README.md`, `docs/*.md`, `CHANGELOG.md`).
2. Run the full quality suite, including integration tests with real PDAL and test datasets.
3. Build artefacts and validate them:

   ```bash
   python -m build
   twine check dist/*
   ```

4. Tag the release (e.g., `git tag v0.1.0a1`) and push the tag.
5. Upload to PyPI once the tag is verified (pending finalisation of credentials and workflow).

---

## 13. Support & Further Reading

- PDAL documentation: https://pdal.io/en/stable/index.html
- QGIS download portal (for bundled PDAL on Windows): https://qgis.org/download/
- Project issue tracker: https://github.com/elgorrion/exeqpdal/issues

This guide should evolve alongside the codebase. Update it whenever behaviour changes or new
features/limitations are discovered.
