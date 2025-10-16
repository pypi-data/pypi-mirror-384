"""Integration tests that exercise the documented examples in docs/examples.md."""

from __future__ import annotations

from pathlib import Path

import pytest

import exeqpdal as pdal

pytestmark = [pytest.mark.integration, pytest.mark.slow, pytest.mark.usefixtures("skip_if_no_pdal")]

DATA_DIR = Path(__file__).parent / "test_data_laz"
PRIMARY_LAS = DATA_DIR / "mid_laz_original.laz"
SECONDARY_LAS = DATA_DIR / "mid_laz_original.laz"


def _require(path: Path) -> Path:
    if not path.exists():
        pytest.skip(f"Required point cloud not found: {path}")
    return path


def _get_point_count(path: Path) -> int:
    info = pdal.info(str(path), stats=True)
    statistics = info.get("stats", {}).get("statistic", [])
    if statistics:
        return int(statistics[0].get("count", 0))
    return int(info.get("count", 0))


def test_docs_examples_ground_classification(
    tmp_path: Path,
) -> None:
    """Run the ground classification examples end-to-end."""
    input_file = _require(PRIMARY_LAS)

    classified = tmp_path / "classified.las"
    ground_only = tmp_path / "ground_only.las"
    dtm = tmp_path / "dtm.tif"

    classify_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(input_file)) | pdal.Filter.smrf() | pdal.Writer.las(str(classified))
    )
    total_points = classify_pipeline.execute()
    assert total_points > 0
    assert classified.exists()

    ground_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(classified))
        | pdal.Filter.range(limits="Classification[2:2]")
        | pdal.Writer.las(str(ground_only))
    )
    ground_points = ground_pipeline.execute()
    assert ground_points > 0
    assert ground_only.exists()
    assert ground_points <= total_points

    dtm_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(input_file))
        | pdal.Filter.smrf()
        | pdal.Filter.range(limits="Classification[2:2]")
        | pdal.Writer.gdal(
            filename=str(dtm),
            resolution=1.0,
            output_type="mean",
        )
    )
    dtm_points = dtm_pipeline.execute()
    assert dtm_points > 0
    assert dtm.exists()


def test_docs_examples_point_cloud_processing(
    tmp_path: Path,
) -> None:
    """Run the point cloud processing examples from the documentation."""
    input_file = _require(PRIMARY_LAS)

    clean_output = tmp_path / "clean.las"
    clean_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(input_file))
        | pdal.Filter.outlier(method="statistical", mean_k=12, multiplier=2.0)
        | pdal.Filter.range(limits="Classification![7:7]")
        | pdal.Writer.las(str(clean_output))
    )
    clean_count = clean_pipeline.execute()
    assert clean_count > 0
    assert clean_output.exists()

    hag_output = tmp_path / "with_heights.las"
    hag_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(input_file))
        | pdal.Filter.hag_nn()
        | pdal.Writer.las(str(hag_output), extra_dims="HeightAboveGround=float32")
    )
    hag_count = hag_pipeline.execute()
    assert hag_count > 0
    assert hag_output.exists()
    schema = pdal.info(str(hag_output), schema=True)
    dimensions = schema.get("schema", {}).get("dimensions", [])
    dimension_names = [dim.get("name", "") for dim in dimensions]
    assert "HeightAboveGround" in dimension_names

    decimated_output = tmp_path / "decimated.las"
    decimation_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(input_file))
        | pdal.Filter.voxeldownsize(cell=1.0)
        | pdal.Writer.las(str(decimated_output))
    )
    decimated_count = decimation_pipeline.execute()
    assert decimated_count > 0
    assert decimated_output.exists()
    original_count = _get_point_count(input_file)
    decimated_count_again = _get_point_count(decimated_output)
    assert decimated_count_again < original_count


def test_docs_examples_format_conversion(
    tmp_path: Path,
) -> None:
    """Verify the translate and merge examples."""
    input_file = _require(PRIMARY_LAS)
    other_file = _require(SECONDARY_LAS)

    translated = tmp_path / "output.laz"
    pdal.translate(str(input_file), str(translated))
    assert translated.exists()
    assert _get_point_count(translated) > 0

    merged = tmp_path / "merged.las"
    pdal.merge([str(input_file), str(other_file)], str(merged))
    assert merged.exists()
    merged_count = _get_point_count(merged)
    assert merged_count > 0


def test_docs_examples_advanced_pipelines(
    tmp_path: Path,
) -> None:
    """Execute the advanced pipelines from the documentation."""
    input_file = _require(PRIMARY_LAS)

    buildings_output = tmp_path / "buildings.las"
    building_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(input_file))
        | pdal.Filter.smrf()
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits="HeightAboveGround[2:50]")
        | pdal.Filter.cluster(min_points=100, tolerance=2.0)
        | pdal.Writer.las(str(buildings_output))
    )
    building_count = building_pipeline.execute()
    assert building_count >= 0
    assert buildings_output.exists()

    dtm_output = tmp_path / "dtm_adv.tif"
    dsm_output = tmp_path / "dsm.tif"

    dtm_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(input_file))
        | pdal.Filter.smrf()
        | pdal.Filter.range(limits="Classification[2:2]")
        | pdal.Writer.gdal(
            filename=str(dtm_output),
            resolution=1.0,
            output_type="min",
        )
    )
    dtm_points = dtm_pipeline.execute()
    assert dtm_points > 0
    assert dtm_output.exists()

    dsm_pipeline = pdal.Pipeline(
        pdal.Reader.las(str(input_file))
        | pdal.Writer.gdal(
            filename=str(dsm_output),
            resolution=1.0,
            output_type="max",
        )
    )
    dsm_points = dsm_pipeline.execute()
    assert dsm_points > 0
    assert dsm_output.exists()
