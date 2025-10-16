"""Planet API integration module.

This module provides functionality for interacting with the Planet API,
including searching for satellite imagery, creating orders, downloading results,
and preprocessing Planet imagery zip files.
"""

# Planet image preprocessing
from .planet_preprocessor import (
    PlanetPreprocessor,
    ManifestFile,
    MetadataFile,
    preprocess_planet_image
)

__version__ = '1.0.0'

__all__ = [
    'PlanetPreprocessor',
    'ManifestFile',
    'MetadataFile',
    'preprocess_planet_image',
]

