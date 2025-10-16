"""PDAL Filter stages - Part 1."""

from __future__ import annotations

from typing import Any

from exeqpdal.stages.base import FilterStage


class Filter:
    """Factory class for creating filter stages."""

    # Ground classification filters
    @staticmethod
    def csf(**options: Any) -> FilterStage:
        """Cloth Simulation Filter for ground classification."""
        return FilterStage("filters.csf", **options)

    @staticmethod
    def pmf(**options: Any) -> FilterStage:
        """Progressive Morphological Filter for ground classification."""
        return FilterStage("filters.pmf", **options)

    @staticmethod
    def skewnessbalancing(**options: Any) -> FilterStage:
        """Skewness balancing filter for ground classification."""
        return FilterStage("filters.skewnessbalancing", **options)

    @staticmethod
    def smrf(**options: Any) -> FilterStage:
        """Simple Morphological Filter for ground classification."""
        return FilterStage("filters.smrf", **options)

    @staticmethod
    def sparsesurface(**options: Any) -> FilterStage:
        """Sparse surface filter."""
        return FilterStage("filters.sparsesurface", **options)

    @staticmethod
    def trajectory(**options: Any) -> FilterStage:
        """Trajectory filter."""
        return FilterStage("filters.trajectory", **options)

    # Outlier removal filters
    @staticmethod
    def elm(**options: Any) -> FilterStage:
        """Extended Local Minimum filter for outlier removal."""
        return FilterStage("filters.elm", **options)

    @staticmethod
    def outlier(**options: Any) -> FilterStage:
        """Statistical outlier removal filter."""
        return FilterStage("filters.outlier", **options)

    @staticmethod
    def neighborclassifier(**options: Any) -> FilterStage:
        """Neighbor-based classification filter."""
        return FilterStage("filters.neighborclassifier", **options)

    # Height above ground filters
    @staticmethod
    def hag_delaunay(**options: Any) -> FilterStage:
        """Height Above Ground using Delaunay triangulation."""
        return FilterStage("filters.hag_delaunay", **options)

    @staticmethod
    def hag_dem(**options: Any) -> FilterStage:
        """Height Above Ground using DEM."""
        return FilterStage("filters.hag_dem", **options)

    @staticmethod
    def hag_nn(**options: Any) -> FilterStage:
        """Height Above Ground using nearest neighbor."""
        return FilterStage("filters.hag_nn", **options)

    # Color filters
    @staticmethod
    def colorinterp(**options: Any) -> FilterStage:
        """Color interpolation filter."""
        return FilterStage("filters.colorinterp", **options)

    @staticmethod
    def colorization(**options: Any) -> FilterStage:
        """Colorization filter from raster."""
        return FilterStage("filters.colorization", **options)

    # Clustering filters
    @staticmethod
    def cluster(**options: Any) -> FilterStage:
        """Clustering filter."""
        return FilterStage("filters.cluster", **options)

    @staticmethod
    def dbscan(**options: Any) -> FilterStage:
        """DBSCAN clustering filter."""
        return FilterStage("filters.dbscan", **options)

    @staticmethod
    def litree(**options: Any) -> FilterStage:
        """Li et al. tree segmentation filter."""
        return FilterStage("filters.litree", **options)

    @staticmethod
    def lloydkmeans(**options: Any) -> FilterStage:
        """Lloyd's k-means clustering filter."""
        return FilterStage("filters.lloydkmeans", **options)

    # Feature extraction filters
    @staticmethod
    def approximatecoplanar(**options: Any) -> FilterStage:
        """Approximate coplanarity filter."""
        return FilterStage("filters.approximatecoplanar", **options)

    @staticmethod
    def covariancefeatures(**options: Any) -> FilterStage:
        """Covariance features filter."""
        return FilterStage("filters.covariancefeatures", **options)

    @staticmethod
    def eigenvalues(**options: Any) -> FilterStage:
        """Eigenvalues computation filter."""
        return FilterStage("filters.eigenvalues", **options)

    @staticmethod
    def estimaterank(**options: Any) -> FilterStage:
        """Estimate rank filter."""
        return FilterStage("filters.estimaterank", **options)

    @staticmethod
    def label_duplicates(**options: Any) -> FilterStage:
        """Label duplicate points filter."""
        return FilterStage("filters.label_duplicates", **options)

    @staticmethod
    def lof(**options: Any) -> FilterStage:
        """Local Outlier Factor filter."""
        return FilterStage("filters.lof", **options)

    @staticmethod
    def miniball(**options: Any) -> FilterStage:
        """Minimum bounding ball filter."""
        return FilterStage("filters.miniball", **options)

    @staticmethod
    def nndistance(**options: Any) -> FilterStage:
        """Nearest neighbor distance filter."""
        return FilterStage("filters.nndistance", **options)

    @staticmethod
    def normal(**options: Any) -> FilterStage:
        """Normal vector computation filter."""
        return FilterStage("filters.normal", **options)

    @staticmethod
    def optimalneighborhood(**options: Any) -> FilterStage:
        """Optimal neighborhood size filter."""
        return FilterStage("filters.optimalneighborhood", **options)

    @staticmethod
    def planefit(**options: Any) -> FilterStage:
        """Plane fitting filter."""
        return FilterStage("filters.planefit", **options)

    @staticmethod
    def radiusassign(**options: Any) -> FilterStage:
        """Radius assignment filter."""
        return FilterStage("filters.radiusassign", **options)

    @staticmethod
    def radialdensity(**options: Any) -> FilterStage:
        """Radial density filter."""
        return FilterStage("filters.radialdensity", **options)

    @staticmethod
    def reciprocity(**options: Any) -> FilterStage:
        """Reciprocity filter."""
        return FilterStage("filters.reciprocity", **options)

    @staticmethod
    def zsmooth(**options: Any) -> FilterStage:
        """Z-coordinate smoothing filter."""
        return FilterStage("filters.zsmooth", **options)

    # Decimation filters
    @staticmethod
    def griddecimation(**options: Any) -> FilterStage:
        """Grid-based decimation filter."""
        return FilterStage("filters.griddecimation", **options)

    # Attribute manipulation filters
    @staticmethod
    def assign(**options: Any) -> FilterStage:
        """Assign values to dimensions filter."""
        return FilterStage("filters.assign", **options)

    @staticmethod
    def overlay(**options: Any) -> FilterStage:
        """Overlay dimensions from another dataset filter."""
        return FilterStage("filters.overlay", **options)

    @staticmethod
    def ferry(**options: Any) -> FilterStage:
        """Copy/rename dimensions filter."""
        return FilterStage("filters.ferry", **options)

    # Ordering filters
    @staticmethod
    def mortonorder(**options: Any) -> FilterStage:
        """Morton (Z-order) ordering filter."""
        return FilterStage("filters.mortonorder", **options)

    @staticmethod
    def randomize(**options: Any) -> FilterStage:
        """Randomize point order filter."""
        return FilterStage("filters.randomize", **options)

    @staticmethod
    def sort(**options: Any) -> FilterStage:
        """Sort points by dimension filter."""
        return FilterStage("filters.sort", **options)

    # Registration filters
    @staticmethod
    def cpd(**options: Any) -> FilterStage:
        """Coherent Point Drift registration filter."""
        return FilterStage("filters.cpd", **options)

    @staticmethod
    def icp(**options: Any) -> FilterStage:
        """Iterative Closest Point registration filter."""
        return FilterStage("filters.icp", **options)

    @staticmethod
    def teaser(**options: Any) -> FilterStage:
        """TEASER++ registration filter."""
        return FilterStage("filters.teaser", **options)

    # Reprojection and transformation filters
    @staticmethod
    def projpipeline(**options: Any) -> FilterStage:
        """PROJ pipeline transformation filter."""
        return FilterStage("filters.projpipeline", **options)

    @staticmethod
    def reprojection(**options: Any) -> FilterStage:
        """Coordinate reprojection filter."""
        return FilterStage("filters.reprojection", **options)

    @staticmethod
    def transformation(**options: Any) -> FilterStage:
        """Affine transformation filter."""
        return FilterStage("filters.transformation", **options)

    @staticmethod
    def straighten(**options: Any) -> FilterStage:
        """Straighten trajectory filter."""
        return FilterStage("filters.straighten", **options)

    @staticmethod
    def georeference(**options: Any) -> FilterStage:
        """Georeference filter."""
        return FilterStage("filters.georeference", **options)

    # Spatial filters
    @staticmethod
    def h3(**options: Any) -> FilterStage:
        """H3 hexagonal spatial indexing filter."""
        return FilterStage("filters.h3", **options)

    @staticmethod
    def crop(**options: Any) -> FilterStage:
        """Crop points to bounds filter."""
        return FilterStage("filters.crop", **options)

    @staticmethod
    def geomdistance(**options: Any) -> FilterStage:
        """Geometric distance filter."""
        return FilterStage("filters.geomdistance", **options)

    # Sampling filters
    @staticmethod
    def decimation(**options: Any) -> FilterStage:
        """Decimation filter (keeps every Nth point)."""
        return FilterStage("filters.decimation", **options)

    @staticmethod
    def fps(**options: Any) -> FilterStage:
        """Farthest Point Sampling filter."""
        return FilterStage("filters.fps", **options)

    @staticmethod
    def relaxationdartthrowing(**options: Any) -> FilterStage:
        """Relaxation dart throwing sampling filter."""
        return FilterStage("filters.relaxationdartthrowing", **options)

    @staticmethod
    def sample(**options: Any) -> FilterStage:
        """Random sampling filter."""
        return FilterStage("filters.sample", **options)

    # Statistical filters
    @staticmethod
    def dem(**options: Any) -> FilterStage:
        """DEM (Digital Elevation Model) generation filter."""
        return FilterStage("filters.dem", **options)

    @staticmethod
    def iqr(**options: Any) -> FilterStage:
        """Interquartile range outlier removal filter."""
        return FilterStage("filters.iqr", **options)

    @staticmethod
    def mad(**options: Any) -> FilterStage:
        """Median Absolute Deviation outlier removal filter."""
        return FilterStage("filters.mad", **options)

    @staticmethod
    def voxelcenternearestneighbor(**options: Any) -> FilterStage:
        """Voxel center nearest neighbor filter."""
        return FilterStage("filters.voxelcenternearestneighbor", **options)

    @staticmethod
    def voxelcentroidnearestneighbor(**options: Any) -> FilterStage:
        """Voxel centroid nearest neighbor filter."""
        return FilterStage("filters.voxelcentroidnearestneighbor", **options)

    @staticmethod
    def voxeldownsize(**options: Any) -> FilterStage:
        """Voxel downsampling filter."""
        return FilterStage("filters.voxeldownsize", **options)

    # Selection filters
    @staticmethod
    def expression(**options: Any) -> FilterStage:
        """Expression-based point selection filter."""
        return FilterStage("filters.expression", **options)

    @staticmethod
    def head(**options: Any) -> FilterStage:
        """Keep first N points filter."""
        return FilterStage("filters.head", **options)

    @staticmethod
    def locate(**options: Any) -> FilterStage:
        """Locate point by ID filter."""
        return FilterStage("filters.locate", **options)

    @staticmethod
    def mongo(**options: Any) -> FilterStage:
        """MongoDB query filter."""
        return FilterStage("filters.mongo", **options)

    @staticmethod
    def range(**options: Any) -> FilterStage:
        """Range-based filtering filter."""
        return FilterStage("filters.range", **options)

    @staticmethod
    def tail(**options: Any) -> FilterStage:
        """Keep last N points filter."""
        return FilterStage("filters.tail", **options)

    # Splitting filters
    @staticmethod
    def chipper(**options: Any) -> FilterStage:
        """Chipper filter for splitting into tiles."""
        return FilterStage("filters.chipper", **options)

    @staticmethod
    def divider(**options: Any) -> FilterStage:
        """Divider filter for splitting into N parts."""
        return FilterStage("filters.divider", **options)

    @staticmethod
    def splitter(**options: Any) -> FilterStage:
        """Splitter filter for splitting by attribute."""
        return FilterStage("filters.splitter", **options)

    # Temporal filters
    @staticmethod
    def gpstimeconvert(**options: Any) -> FilterStage:
        """GPS time conversion filter."""
        return FilterStage("filters.gpstimeconvert", **options)

    @staticmethod
    def groupby(**options: Any) -> FilterStage:
        """Group points by dimension filter."""
        return FilterStage("filters.groupby", **options)

    @staticmethod
    def returns(**options: Any) -> FilterStage:
        """Return number filtering filter."""
        return FilterStage("filters.returns", **options)

    @staticmethod
    def separatescanline(**options: Any) -> FilterStage:
        """Separate scan line filter."""
        return FilterStage("filters.separatescanline", **options)

    # Merging filters
    @staticmethod
    def merge(**options: Any) -> FilterStage:
        """Merge multiple point views filter."""
        return FilterStage("filters.merge", **options)

    # Analysis filters
    @staticmethod
    def hexbin(**options: Any) -> FilterStage:
        """Hexagonal binning filter."""
        return FilterStage("filters.hexbin", **options)

    @staticmethod
    def info(**options: Any) -> FilterStage:
        """Info extraction filter."""
        return FilterStage("filters.info", **options)

    @staticmethod
    def stats(**options: Any) -> FilterStage:
        """Statistics computation filter."""
        return FilterStage("filters.stats", **options)

    @staticmethod
    def expressionstats(**options: Any) -> FilterStage:
        """Expression-based statistics filter."""
        return FilterStage("filters.expressionstats", **options)

    # Mesh generation filters
    @staticmethod
    def delaunay(**options: Any) -> FilterStage:
        """Delaunay triangulation filter."""
        return FilterStage("filters.delaunay", **options)

    @staticmethod
    def greedyprojection(**options: Any) -> FilterStage:
        """Greedy projection triangulation filter."""
        return FilterStage("filters.greedyprojection", **options)

    @staticmethod
    def poisson(**options: Any) -> FilterStage:
        """Poisson surface reconstruction filter."""
        return FilterStage("filters.poisson", **options)

    @staticmethod
    def faceraster(**options: Any) -> FilterStage:
        """Face rasterization filter."""
        return FilterStage("filters.faceraster", **options)

    # Extension filters
    @staticmethod
    def matlab(**options: Any) -> FilterStage:
        """MATLAB script filter."""
        return FilterStage("filters.matlab", **options)

    @staticmethod
    def python(**options: Any) -> FilterStage:
        """Python script filter."""
        return FilterStage("filters.python", **options)

    @staticmethod
    def julia(**options: Any) -> FilterStage:
        """Julia script filter."""
        return FilterStage("filters.julia", **options)

    # Streaming filters
    @staticmethod
    def streamcallback(**options: Any) -> FilterStage:
        """Streaming callback filter."""
        return FilterStage("filters.streamcallback", **options)
