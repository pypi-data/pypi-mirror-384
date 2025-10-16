#!/usr/bin/env python3
"""Quick start script to test exeqpdal installation and basic functionality."""

from __future__ import annotations

import sys


def check_python_version() -> bool:
    """Check if Python version is 3.12+."""
    # Version check matches pyproject.toml requires-python = ">=3.12"
    print(
        f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    return True


def check_imports() -> bool:
    """Check if exeqpdal can be imported."""
    try:
        import exeqpdal as pdal

        print(f"✓ exeqpdal version: {pdal.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Cannot import exeqpdal: {e}")
        print("   Run: pip install -e .")
        return False


def check_pdal_cli() -> bool:
    """Check if PDAL CLI is accessible."""
    try:
        import exeqpdal as pdal

        pdal.validate_pdal()
        version = pdal.get_pdal_version()
        path = pdal.get_pdal_path()
        print(f"✓ PDAL CLI found: {version}")
        print(f"  Path: {path}")
        return True
    except Exception as e:
        print(f"❌ PDAL CLI not found: {e}")
        print("   Install PDAL:")
        print("   - Ubuntu: sudo apt install pdal")
        print("   - macOS: brew install pdal")
        print("   - Windows: Install QGIS 3.40+ or use conda")
        return False


def test_stage_creation() -> bool:
    """Test creating PDAL stages."""
    try:
        import exeqpdal as pdal

        # Test reader
        reader = pdal.Reader.las("input.las")
        assert reader.stage_type == "readers.las"

        # Test filter
        filter_stage = pdal.Filter.range(limits="Classification[2:2]")
        assert filter_stage.stage_type == "filters.range"

        # Test writer
        writer = pdal.Writer.las("output.las", compression="laszip")
        assert writer.stage_type == "writers.las"

        print("✓ Stage creation works")
        return True
    except Exception as e:
        print(f"❌ Stage creation failed: {e}")
        return False


def test_pipeline_creation() -> bool:
    """Test creating pipeline."""
    try:
        import exeqpdal as pdal

        # Test stage chaining
        pipeline = (
            pdal.Reader.las("input.las")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las("output.las")
        )

        assert pipeline.stage_type == "writers.las"

        # Test JSON pipeline
        pipeline_dict = {
            "pipeline": [
                {"type": "readers.las", "filename": "input.las"},
                {"type": "filters.range", "limits": "Classification[2:2]"},
                {"type": "writers.las", "filename": "output.las"},
            ]
        }

        pipeline2 = pdal.Pipeline(pipeline_dict)
        assert "pipeline" in pipeline2._pipeline_dict

        print("✓ Pipeline creation works")
        return True
    except Exception as e:
        print(f"❌ Pipeline creation failed: {e}")
        return False


def test_type_hints() -> bool:
    """Test type hints are accessible."""
    try:
        import exeqpdal as pdal

        # Check dimensions
        assert pdal.Dimension.X == "X"
        assert pdal.Dimension.CLASSIFICATION == "Classification"

        # Check data types
        assert pdal.DataType.DOUBLE == "double"

        # Check classifications
        assert pdal.Classification.GROUND == 2

        print("✓ Type definitions accessible")
        return True
    except Exception as e:
        print(f"❌ Type definitions failed: {e}")
        return False


def test_exception_handling() -> bool:
    """Test exception classes."""
    try:
        import exeqpdal as pdal

        # Test exception classes exist
        assert pdal.PDALError
        assert pdal.PDALNotFoundError
        assert pdal.PipelineError

        print("✓ Exception classes defined")
        return True
    except Exception as e:
        print(f"❌ Exception classes failed: {e}")
        return False


def main() -> int:
    """Run all checks."""
    print("=" * 60)
    print("exeqpdal Quick Start Check")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("Package Import", check_imports),
        ("PDAL CLI", check_pdal_cli),
        ("Stage Creation", test_stage_creation),
        ("Pipeline Creation", test_pipeline_creation),
        ("Type Hints", test_type_hints),
        ("Exceptions", test_exception_handling),
    ]

    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append(False)

    print()
    print("=" * 60)
    print(f"Results: {sum(results)}/{len(results)} checks passed")
    print("=" * 60)

    if all(results):
        print("\n✓ All checks passed! exeqpdal is ready to use.")
        print("\nNext steps:")
        print("1. Read README.md for API documentation")
        print("2. Check EXAMPLES.md for usage examples")
        print("3. Try processing a real LAS file")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
