"""Remote Sensing module for agricultural satellite image processing.

This module provides comprehensive tools for processing satellite imagery
and extracting agricultural indicators. It supports multiple remote sensing
monitoring contents including vegetation indices, drought assessment,
nitrogen content analysis, and more.

Main Classes:
    RemoteSensingProcessor: High-level interface for complete processing pipeline
    AgricultureProcessor: Detailed agricultural data inversion processor

Main Functions:
    inverse: Perform agricultural data inversion
    gener_mask: Generate masks for roads and field boundaries
    do_idw: Inverse Distance Weighting interpolation for weather data
    shpvaluedGeoJson: Convert shapefiles to valued GeoJSON
    
Constants:
    ClusterMode: Enum for clustering modes
    INVERSION_TOPICS: Dictionary of available inversion topics
"""

# Main processing classes
from .pipeline import RemoteSensingProcessor

# Import Planet preprocessor from planet module (re-export for convenience)
try:
    from ..planet.planet_preprocessor import (
        PlanetPreprocessor,
        ManifestFile,
        MetadataFile,
        preprocess_planet_image
    )
except ImportError:
    # Fallback import
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from planet.planet_preprocessor import (
        PlanetPreprocessor,
        ManifestFile,
        MetadataFile,
        preprocess_planet_image
    )

# Core processing functions
from .processor import AgricultureProcessor, inverse
from .masking import gener_mask, generate_geometry_mask
from .idw import do_idw, GEOchange
from .shapefile_processor import shpvaluedGeoJson, shpprocess, shp2thumbnail

# Indicators
from .indicators import (
    calculate_ndvi,
    cal_nddi,
    cal_ndni,
    cal_chanliang,
    cal_fpar,
    cal_et,
    cal_fvc,
    cal_fenlie,
    calculate_irrigation_order,
    calculate_fertilization_order,
    check_vegetation_status,
)

# Clustering and segmentation
from .clustering import cluster_data, segment_fields

# IO operations
from .io import read_tiff, save_tiff, read_img, write_img, write_tiff

# Visualization
from .visualization import display_bands, display_results_group, plot_all_indices

# Constants
from .constants import (
    ClusterMode,
    INVERSION_TOPICS,
    BAND_NAMES,
    CROP_FILES,
    VIGOR_LEVEL_COLORS,
    DROUGHT_LEVEL_COLORS,
)

__version__ = '1.0.0'

__all__ = [
    # Classes
    'RemoteSensingProcessor',
    'MainProcess',  # Backward compatibility
    'PlanetPreprocessor',
    'AgricultureProcessor',
    'ManifestFile',
    'MetadataFile',
    'GEOchange',
    
    # Main functions
    'inverse',
    'gener_mask',
    'do_idw',
    'shpvaluedGeoJson',
    'preprocess_planet_image',
    
    # Indicators
    'calculate_ndvi',
    'cal_nddi',
    'cal_ndni',
    'cal_chanliang',
    'cal_fpar',
    'cal_et',
    'cal_fvc',
    'cal_fenlie',
    'calculate_irrigation_order',
    'calculate_fertilization_order',
    'check_vegetation_status',
    
    # Clustering
    'cluster_data',
    'segment_fields',
    
    # IO
    'read_tiff',
    'save_tiff',
    'read_img',
    'write_img',
    'write_tiff',
    
    # Visualization
    'display_bands',
    'display_results_group',
    'plot_all_indices',
    
    # Shapefile utilities
    'shpprocess',
    'shp2thumbnail',
    'generate_geometry_mask',
    
    # Constants
    'ClusterMode',
    'INVERSION_TOPICS',
    'BAND_NAMES',
    'CROP_FILES',
    'VIGOR_LEVEL_COLORS',
    'DROUGHT_LEVEL_COLORS',
]

