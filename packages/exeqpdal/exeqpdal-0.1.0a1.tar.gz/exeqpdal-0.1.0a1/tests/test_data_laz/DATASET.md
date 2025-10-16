# Dataset Overview

Generated: 2025-10-15T11:09:49

All files reside in `tests/test_data_laz/` and share the Bavarian projected CRS (EPSG:31468). COPC assets retain their source LAS schema metadata; statistics were gathered with PDAL 2.9.2 and laspy 2.x.

## Spatial Relationships

**All datasets intersect spatially:**
- `mid_laz_original` and `lrg_laz_original` (and their COPC derivatives) cover the **identical** 1km × 1km tile: X 785000–786000, Y 5350000–5351000
- `sml_copc_created` and `sml-mid_copc_created` cover a larger area (X 784900–786100, Y 5349900–5351100), but **cropped into corridor** that **encompasses** the mid/lrg tile
- This spatial overlap makes all datasets suitable for testing data merging, mosaicking, and multi-source processing scenarios

## Noise and Filtering Status

**Non-filtered datasets** (containing unclassified/raw points):
- `lrg_laz_original` and its derivatives (`lrg_copc_translated`, `sml-mid_copc_created`) contain **unclassified points** (class 1 present, classification range 1–31)
- Suitable for noise removal, outlier detection, and denoising filter testing

**Pre-filtered datasets**:
- `mid_laz_original` and `mid_copc_translated` have been pre-classified (classification range 2–20, no class 1 or 7)
- Class 20 (unassigned/other), class 2 (ground), class 6 (building) only
- Suitable for clean pipeline testing and writer verification

## mid_laz_original.laz
- **Format**: LAS 1.2 (point format 1)
- **Size / Points**: ~85 MB, 14,058,590 pts
- **Extent**: X 785 000 – 785 999.998, Y 5 350 000 – 5 350 999.998, Z 352.263 – 422.377 m
- **Intensity / Returns**: mean intensity 191.8; ReturnNumber mean 1.88 (max 7)
- **Classification mix**: class 20 ≈ 52.0 %, class 2 (ground) ≈ 47.4 %, class 6 (building) ≈ 0.6 %
- **Classification**: **Pre-filtered** (classes 2, 6, 20 only)
- **Usage**: Canonical "mid" tile from Bavarian open data. Balanced mix for clean pipeline testing and writer smoke tests.

## mid_copc_translated.copc.laz
- **Format**: COPC (re-tiled from LAS 1.2)
- **Size / Points**: ~95 MB, 14,058,590 pts
- **Extent**: Identical to `mid_laz_original`
- **Classification**: **Pre-filtered** (inherits clean classification from mid_laz_original)
- **Notes**: QGIS COPC export of the mid tile. Ideal for clean COPC streaming reader coverage and index-aware scenarios.

## lrg_laz_original.laz
- **Format**: LAS 1.4 (point format 6)
- **Size / Points**: ~1.07 GB, 115,122,516 pts
- **Extent**: X 785 000 – 785 999.99, Y 5 350 000 – 5 350 999.99, Z −41.85 – 654.98 m
- **Intensity / Returns**: mean intensity 34,959; ReturnNumber mean 1.46; NumberOfReturns mean 1.92
- **Classification mix**: class 20 ≈ 34.6 %, class 16 ≈ 34.0 %, class 10 ≈ 29.0 %, remaining classes (6, 8, 9, 13, 22, 30, 31, …) each <1 %
- **Extra Dimensions**: RIEGL attributes (Amplitude, Pulse width, Reflectance, Deviation), TerraScan attributes (Distance, Group, Normal)
- **Usage**: Engineering-grade survey with **unclassified points**. Ideal for stress/performance tests, **noise filtering/denoising experiments**, and advanced attribute handling.

## lrg_copc_translated.copc.laz
- **Format**: COPC (derived from LAS 1.4)
- **Size / Points**: ~618 MB, 115,122,516 pts
- **Extent**: Matches `lrg_laz_original`
- **Classification**: **Non-filtered** (inherits unclassified points from source)
- **Notes**: COPC conversion preserving the full attribute set including unfiltered classification. Suitable for large streaming, level-of-detail workflows, and denoising tests with COPC format.

## sml_copc_created.copc.laz
- **Format**: COPC (derived from LAS 1.2)
- **Size / Points**: ~13 MB, 1,723,023 pts
- **Extent**: X 784 900.124 – 786 099.812, Y 5 349 900.073 – 5 351 099.901, Z 350.815 – 419.079 m
- **Classification mix**: class 20 ≈ 57.5 %, class 10 ≈ 42.3 %, class 30 ≈ 0.2 %
- **Classification**: **Reclassified** (derived from pre-filtered mid_laz_original with additional processing)
- **Usage**: PDAL/QGIS composite (mid tile + neighbours) with reclassification/cropping. Compact COPC fixture for small workflows and testing custom classification schemes.

## sml-mid_copc_created.copc.laz
- **Format**: COPC (derived from LAS 1.4)
- **Size / Points**: ~64 MB, 8,025,186 pts
- **Extent**: X 784 900.06 – 786 099.94, Y 5 349 900.03 – 5 351 099.96, Z 124.36 – 643.29 m
- **Classification mix**: class 20 ≈ 41.3 %, class 16 ≈ 31.6 %, class 10 ≈ 25.2 %, minor classes (8, 9, 13, 22, 31, …) each <1 %
- **Classification**: **Non-filtered** (inherits unclassified points from lrg_laz_original)
- **Usage**: Cropped subset of the large survey without reclassification. Bridges between mid-size and large COPC workloads. Suitable for **denoising tests** with moderate-sized datasets.
