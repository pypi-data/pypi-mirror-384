# Contributing to exeqpdal

Thank you for your interest in contributing to `exeqpdal`! All contributions are welcome, from bug reports to new features.

## Development Setup

1.  Fork and clone the repository:

    ```bash
    git clone https://github.com/YOUR-USERNAME/exeqpdal.git
    cd exeqpdal
    ```

2.  Create a virtual environment and install dependencies. We recommend
    [`uv`](https://github.com/astral-sh/uv):

    ```bash
    uv pip install -e ".[dev]"
    ```

    When `uv` is not available, fall back to standard tooling:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    ```

3.  Verify the toolchain by running the default formatting, linting, typing, and test commands:

    ```bash
    ruff format .
    ruff check .
    mypy exeqpdal
    pytest tests/
    ```

    Integration tests require the PDAL CLI and LAZ/COPC test datasets in `tests/test_data_laz/`.
    Tests automatically skip when PDAL or test data are unavailable. Add `-m "not integration"`
    to skip integration tests entirely.

## Development Workflow

-   Create a new branch for your changes.
-   Make your changes and add tests for them.
-   Make sure all tests pass, including the linters and type checkers:

    ```bash
    ruff format .
    ruff check .
    mypy exeqpdal
    pytest tests/
    ```

    Use `pytest -m "not integration"` to skip tests requiring PDAL and test datasets. Keep test
    outputs (especially under `tests/laz_to_writers/outputs/`) out of commits.

-   Commit your changes using the existing Conventional Commit prefixes (for example,
    `fix: handle PDAL path lookup`) and push them to your fork.
-   Open a pull request that explains the scenario, any data prerequisites, and how you validated the
    change.

## Release Management

Maintainers preparing a PyPI upload should follow the checklist in `docs/publishing.md`. It covers
versioning, changelog updates, local validation (`ruff`, `mypy`, `pytest`, `python -m build`), and
the GitHub Actions workflow that publishes releases through PyPI's Trusted Publisher integration.

## Code Style

This project uses `ruff` for both formatting and linting with the settings defined in
`pyproject.toml`. Four-space indentation, 100-character lines, and double-quoted strings are applied
by `ruff format`.

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
