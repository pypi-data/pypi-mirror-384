# Examples

This page contains a collection of examples that demonstrate how to use the `exeqpdal` library to perform common point cloud processing tasks. All snippets assume the PDAL CLI is installed and discoverable (via `PATH`, `PDAL_EXECUTABLE`, or `pdal.set_pdal_path()`).

## Ground Classification

### Classify ground points

```python
import exeqpdal as pdal

# Use SMRF (Simple Morphological Filter) to classify ground points
pipeline = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.smrf()
    | pdal.Writer.las("classified.las")
)
pipeline.execute()
```

### Extract only ground points

```python
import exeqpdal as pdal

# After classification, extract just the ground points
pipeline = pdal.Pipeline(
    pdal.Reader.las("classified.las")
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.las("ground_only.las")
)
pipeline.execute()
```

### Create a DTM raster

```python
import exeqpdal as pdal

# Classify and immediately create a DTM raster in one pipeline
pipeline = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.smrf()
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.gdal(
        filename="dtm.tif",
        resolution=1.0,
        output_type="mean"
    )
)
pipeline.execute()
```

## Point Cloud Processing

### Remove outliers (noise reduction)

```python
import exeqpdal as pdal

# Statistical outlier removal
pipeline = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.outlier(
        method="statistical",
        mean_k=12,
        multiplier=2.0
    )
    | pdal.Filter.range(limits="Classification![7:7]")
    | pdal.Writer.las("clean.las")
)
pipeline.execute()
```

### Calculate height above ground

```python
import exeqpdal as pdal

# Add "height above ground" dimension to each point
pipeline = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.hag_nn()
    | pdal.Writer.las(
        "with_heights.las",
        extra_dims="HeightAboveGround=float32",
    )
)
pipeline.execute()
```

### Reduce point density (decimation)

```python
import exeqpdal as pdal

# Reduce file size by keeping only one point per cubic meter
pipeline = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.voxeldownsize(cell=1.0)
    | pdal.Writer.las("decimated.las")
)
pipeline.execute()
```

## Format Conversion

### Simple format conversion

```python
import exeqpdal as pdal

pdal.translate("input.las", "output.laz")
```

### Merge multiple files

```python
from exeqpdal import merge

merge(["tile1.las", "tile2.las", "tile3.las"], "merged.las")
```

## Advanced Pipelines

### Building detection workflow

```python
import exeqpdal as pdal

# Detect buildings by finding clusters of non-ground points above 2m
pipeline = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.smrf()
    | pdal.Filter.hag_nn()
    | pdal.Filter.range(limits="HeightAboveGround[2:50]")
    | pdal.Filter.cluster(min_points=100, tolerance=2.0)
    | pdal.Writer.las("buildings.las")
)
pipeline.execute()
```

### Create DTM and DSM rasters

```python
import exeqpdal as pdal

# DTM (Digital Terrain Model) - ground surface only
dtm = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.smrf()
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.gdal(
        filename="dtm.tif",
        resolution=1.0,
        output_type="min"
    )
)
dtm.execute()

# DSM (Digital Surface Model) - top of everything (trees, buildings, etc.)
dsm = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Writer.gdal(
        filename="dsm.tif",
        resolution=1.0,
        output_type="max"
    )
)
dsm.execute()
```
