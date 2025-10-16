# Publishing `exeqpdal`

This project ships releases to PyPI through GitHub Actions using PyPI's Trusted Publisher feature.
Follow this checklist to cut and ship a new version.

## 1. One-time setup

1. Create the `exeqpdal` project on PyPI using the account that owns the repository.
2. In the PyPI UI, open **Publishing → Add a new publisher** and register:
   - Repository: `elgorrion/exeqpdal`
   - Workflow name: `publish.yml`
   - Environment: `pypi`
3. (Optional) Mirror the same configuration on TestPyPI if you want to run rehearsal uploads.

Once the publisher is created, no API tokens are required—GitHub Actions will authenticate with
OIDC when the `publish` workflow runs.

## 2. Prepare the release

1. Update `pyproject.toml` with the new version (use PEP 440-compliant tags—`0.1.0a2`, etc.).
2. Move the relevant entries in `CHANGELOG.md` from `Unreleased` to a dated release section.
3. Ensure `README.md` reflects the current installation instructions.
4. Commit these changes with a Conventional Commit message such as
   `chore: prepare release 0.1.0a2`.

## 3. Validate locally

```bash
ruff format .
ruff check .
mypy exeqpdal
pytest -m "not integration" tests/
# Optional: run full suite when PDAL + data are available
pytest tests/

python -m build
twine check dist/*
```

Remove the `dist/` directory before rebuilding to avoid stale artifacts.

Smoke-test the freshly built wheel and sdist in a temporary virtual environment if possible.

## 4. Tag and publish

1. Create an annotated tag that matches the version (for example,
   `git tag -a v0.1.0a2 -m "v0.1.0a2"`).
2. Push the tag: `git push origin v0.1.0a2`.
3. Draft a GitHub Release pointing at the tag. Once you click **Publish release**, the
   `publish.yml` workflow will:
   - Re-run the validation checks
   - Build the wheel and sdist
   - Publish the artifacts to PyPI using the Trusted Publisher binding
4. Wait for the workflow to report success before announcing the release.

The publish job targets the `pypi` environment, so you can require manual approval or additional
reviewers directly from the repository settings if desired.

## 5. Post-release

1. Verify the package is visible on PyPI and installable:

   ```bash
   pip install --pre exeqpdal
   ```

2. Close or update any tracking issues.
3. Start a new `[Unreleased]` section in `CHANGELOG.md` for ongoing work.
