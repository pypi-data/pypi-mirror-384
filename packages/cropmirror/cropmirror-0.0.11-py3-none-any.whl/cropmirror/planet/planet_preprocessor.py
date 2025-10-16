"""Planet satellite image preprocessor.

This module handles the preprocessing of Planet satellite imagery zip files,
including extraction, metadata parsing, and file organization.
"""
import json
import logging
import os
from zipfile import ZipFile
from typing import Dict, Optional, Tuple
from osgeo import gdal


class PlanetPreprocessor:
    """Preprocessor for Planet satellite imagery.
    
    This class handles the extraction and preprocessing of Planet satellite
    image zip files, extracting the GeoTIFF file and metadata.
    
    Attributes:
        zipfile: Path to the Planet satellite image zip file
        output_dir: Directory where files will be extracted
        tiffile: Path to extracted GeoTIFF file
        geometry: GeoJSON geometry from metadata
        properties: Image properties from metadata
        meta: Full manifest metadata
    """
    
    def __init__(self, zipfile: str):
        """Initialize the Planet preprocessor.
        
        Args:
            zipfile: Path to the Planet satellite image zip file.
        """
        self.zipfile = zipfile
        self.output_dir = os.path.dirname(zipfile)
        self.tiffile: Optional[str] = None
        self.geometry: Dict = {}
        self.properties: Dict = {}
        self.meta: Optional[Dict] = None
        
    def process(self) -> Tuple[str, Dict, Dict]:
        """Process the Planet zip file and extract necessary information.
        
        Returns:
            Tuple of (tiffile_path, geometry, properties)
            
        Raises:
            FileNotFoundError: If zip file doesn't exist
            ValueError: If required files are not found in the zip
        """
        if not os.path.exists(self.zipfile):
            raise FileNotFoundError(f"Zip file not found: {self.zipfile}")
        
        logging.info(f"Processing Planet zip file: {self.zipfile}")
        
        # Extract zip file
        self._extract_zip()
        
        # Load manifest and find files
        self._load_manifest()
        
        # Extract tif file and metadata
        self._extract_tif_and_metadata()
        
        if not self.tiffile:
            raise ValueError("No GeoTIFF file found in the zip archive")
        
        logging.info(f"Successfully processed Planet data. TIF file: {self.tiffile}")
        
        return self.tiffile, self.geometry, self.properties
    
    def _extract_zip(self) -> None:
        """Extract the zip file to output directory."""
        logging.info(f"Extracting zip file to: {self.output_dir}")
        with ZipFile(self.zipfile, "r") as zip_obj:
            zip_obj.extractall(path=self.output_dir)
        logging.info("Zip file extracted successfully")
    
    def _load_manifest(self) -> None:
        """Load the manifest.json file."""
        manifest_path = os.path.join(self.output_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        
        with open(manifest_path, 'r') as f:
            self.meta = json.load(f)
        logging.info("Manifest loaded successfully")
    
    def _extract_tif_and_metadata(self) -> None:
        """Extract GeoTIFF file path and metadata from manifest."""
        if not self.meta or "files" not in self.meta:
            raise ValueError("Invalid manifest structure")
        
        for file_info in self.meta["files"]:
            fm = ManifestFile(**file_info)
            
            # Find the GeoTIFF file
            if "planet/asset_type" in fm.annotations:
                if fm.annotations["planet/asset_type"] == "ortho_analytic_8b_sr":
                    self.tiffile = os.path.join(self.output_dir, fm.path)
                    logging.info(f"Found GeoTIFF file: {self.tiffile}")
            
            # Find the metadata JSON file
            elif fm.path.endswith("_metadata.json"):
                metadata_path = os.path.join(self.output_dir, fm.path)
                self._load_image_metadata(metadata_path)
    
    def _load_image_metadata(self, metadata_path: str) -> None:
        """Load image metadata from metadata JSON file.
        
        Args:
            metadata_path: Path to the metadata JSON file.
        """
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
        
        metadata = MetadataFile(**meta)
        
        # geometry string to dict
        self.geometry = metadata.geometry
        
        self.properties = metadata.properties
        
        if self.properties:
            acquired_time = self.properties.get('acquired', 'Unknown')
            logging.info(f"Image acquired at: {acquired_time}")
    
    def get_image_info(self) -> Dict:
        """Get comprehensive image information.
        
        Returns:
            Dictionary containing image information.
        """
        info = {
            "tiffile": self.tiffile,
            "geometry": self.geometry,
            "properties": self.properties,
            "zipfile": self.zipfile,
            "output_dir": self.output_dir,
        }
        
        # Add image dimensions if tiffile exists
        if self.tiffile and os.path.exists(self.tiffile):
            try:
                dataset = gdal.Open(self.tiffile)
                if dataset:
                    info["width"] = dataset.RasterXSize
                    info["height"] = dataset.RasterYSize
                    info["bands"] = dataset.RasterCount
                    info["projection"] = dataset.GetProjection()
                    info["geotransform"] = dataset.GetGeoTransform()
                    dataset = None
            except Exception as e:
                logging.warning(f"Failed to read image info: {e}")
        
        return info


class ManifestFile:
    """Represents a file entry in the Planet manifest.
    
    Attributes:
        path: File path
        media_type: MIME type
        size: File size in bytes
        annotations: Additional metadata
    """
    
    def __init__(self, path: str, media_type: str, size: int, 
                 annotations: dict, digests: Optional[dict] = None) -> None:
        self.path = path
        self.media_type = media_type
        self.size = size
        self.annotations = annotations
        self.digests = digests


class MetadataFile:
    """Represents Planet image metadata.
    
    Attributes:
        id: Image ID
        type: Feature type
        geometry: GeoJSON geometry
        properties: Image properties
    """
    
    def __init__(self, id: str, type: str, 
                 geometry: Optional[dict] = None, 
                 properties: Optional[dict] = None) -> None:
        self.id = id
        self.type = type
        self.geometry = geometry or {}
        self.properties = properties or {}


def preprocess_planet_image(zipfile: str) -> Tuple[str, Dict, Dict]:
    """Convenience function to preprocess a Planet image.
    
    Args:
        zipfile: Path to Planet satellite image zip file.
        
    Returns:
        Tuple of (tiffile_path, geometry, properties)
        
    Example:
        >>> tiffile, geometry, properties = preprocess_planet_image("image.zip")
        >>> print(f"TIF file: {tiffile}")
    """
    preprocessor = PlanetPreprocessor(zipfile)
    return preprocessor.process()

