"""Unit tests for Filter factory wrappers."""

from __future__ import annotations

import exeqpdal as pdal


class TestFilterFactory:
    """Smoke tests for representative filter factories."""

    def test_filter_range(self) -> None:
        filter_stage = pdal.Filter.range(limits="Classification[2:2]")
        assert filter_stage.stage_type == "filters.range"
        assert filter_stage.options["limits"] == "Classification[2:2]"

    def test_filter_outlier(self) -> None:
        filter_stage = pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
        assert filter_stage.stage_type == "filters.outlier"
        assert filter_stage.options["method"] == "statistical"

    def test_filter_smrf(self) -> None:
        filter_stage = pdal.Filter.smrf()
        assert filter_stage.stage_type == "filters.smrf"

    def test_filter_reprojection(self) -> None:
        filter_stage = pdal.Filter.reprojection(
            in_srs="EPSG:4326",
            out_srs="EPSG:3857",
        )
        assert filter_stage.stage_type == "filters.reprojection"

    def test_filter_streamcallback(self) -> None:
        filter_stage = pdal.Filter.streamcallback(where="Classification[2:2]")
        assert filter_stage.stage_type == "filters.streamcallback"
        assert filter_stage.options["where"] == "Classification[2:2]"
