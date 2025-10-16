"""Main processor for agricultural data inversion."""
import os
import logging
import numpy as np
from scipy.interpolate import interp2d
from typing import Dict, Optional, Any, List

from .io import read_tiff, save_tiff
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
    mat_nan_generation,
)
from .clustering import cluster_data, segment_fields
from .constants import ClusterMode, BAND_RED, BAND_GREEN, BAND_NIR, BAND_RED_EDGE


class AgricultureProcessor:
    """Main processor for agricultural data inversion and analysis."""
    
    def __init__(self, imgf: str, mask: str, weatherpath: str):
        """Initialize the processor.
        
        Args:
            imgf: Path to input GeoTIFF file.
            mask: Path to mask file.
            weatherpath: Path to weather data directory.
        """
        self.imgf = imgf
        self.mask_file = mask
        self.weatherpath = weatherpath
        
        # Load data
        self.data, self.width, self.height, self.geotrans, self.proj = read_tiff(imgf)
        self.data = self.data.astype(np.float32)
        self.mask, _, _, _, _ = read_tiff(mask)
        
        # Extract bands
        self.red_band = self.data[BAND_RED, :, :]
        self.green_band = self.data[BAND_GREEN, :, :]
        self.nir_band = self.data[BAND_NIR, :, :]
        self.red_edge = self.data[BAND_RED_EDGE, :, :]
    
    def inverse(
        self,
        savepath: str,
        suffix: str,
        do_clustering: bool = True,
        do_invertion: Optional[Dict[str, Dict[str, Any]]] = None,
        detection_function: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Perform agricultural data inversion and save results.
        
        Args:
            savepath: Output directory path.
            suffix: File suffix for output files.
            do_clustering: Whether to perform clustering.
            do_invertion: Dictionary controlling which inversions to perform.
            detection_function: List of specific functions to run (None = all).
            
        Returns:
            Dictionary containing visualization results.
        """
        logging.info(f"Starting inversion process with clustering={do_clustering}")
        
        # Calculate NDVI
        denominator = self.nir_band + self.red_band
        ndvi = np.zeros_like(denominator, dtype=np.float32)
        valid_mask = denominator != 0
        
        if do_clustering:
            ndvi[valid_mask] = (
                (self.nir_band[valid_mask] - self.red_band[valid_mask]) / 
                denominator[valid_mask]
            )
        else:
            ndvi[valid_mask] = 1
        
        ndvi = np.where(self.mask != 0, ndvi, np.nan)
        
        # Check vegetation status
        vegetation_mask = check_vegetation_status(ndvi, self.mask)
        
        # Process each indicator
        results = self._process_indicators(
            ndvi, vegetation_mask, do_clustering, do_invertion
        )
        
        # Save results
        self._save_results(
            results, savepath, suffix, do_clustering, detection_function
        )
        
        # Process weather data
        self._process_weather_data(
            savepath, suffix, do_clustering, detection_function
        )
        
        # Prepare visualization results
        return self._prepare_visualization_results(results, ndvi)
    
    def _process_indicators(
        self,
        ndvi: np.ndarray,
        vegetation_mask: np.ndarray,
        do_clustering: bool,
        do_invertion: Optional[Dict[str, Dict[str, Any]]]
    ) -> Dict[str, np.ndarray]:
        """Process all agricultural indicators.
        
        Args:
            ndvi: NDVI array.
            vegetation_mask: Vegetation status mask.
            do_clustering: Whether to perform clustering.
            do_invertion: Inversion control dictionary.
            
        Returns:
            Dictionary of processed indicator arrays.
        """
        results = {}
        
        # NDVI
        if do_clustering:
            if do_invertion and do_invertion.get('NDVI', {}).get('invertible'):
                results['ndvi'] = cluster_data(ndvi, mode=ClusterMode.PRESERVE_ZERO)
            else:
                results['ndvi'] = mat_nan_generation(
                    self.green_band, self.mask, do_clustering
                )
        else:
            results['ndvi'] = ndvi
        
        # NDDI (Drought Index)
        if do_invertion and do_invertion.get('NDDI', {}).get('invertible'):
            nddi = cal_nddi(
                self.green_band, self.red_band, self.nir_band, 
                self.mask, has_valid_fields=do_clustering
            )
            mask_area = (self.mask != 0)
            nddi[mask_area & (np.isnan(nddi) | ~vegetation_mask)] = 5
            nddi[~mask_area] = np.nan
            results['nddi'] = cluster_data(nddi, mode=ClusterMode.PRESERVE_ZERO) if do_clustering else nddi
        else:
            results['nddi'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        # NDNI (Nitrogen Content)
        if do_invertion and do_invertion.get('NDNI', {}).get('invertible'):
            ndni = cal_ndni(self.red_edge, self.mask, has_valid_fields=do_clustering)
            mask_area = (self.mask != 0)
            ndni[mask_area & (np.isnan(ndni) | ~vegetation_mask)] = 1
            ndni[~mask_area] = np.nan
            results['ndni'] = cluster_data(ndni, mode=ClusterMode.NDNI_SPECIAL) if do_clustering else ndni
        else:
            results['ndni'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        # Yield
        if do_invertion and do_invertion.get('Yield', {}).get('invertible'):
            chanliang = cal_chanliang(ndvi, self.mask, has_valid_fields=do_clustering)
            results['yield'] = cluster_data(chanliang, mode=ClusterMode.PRESERVE_ZERO) if do_clustering else chanliang
        else:
            results['yield'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        # FPAR
        if do_invertion and do_invertion.get('FPAR', {}).get('invertible'):
            fpar = cal_fpar(
                ndvi, self.red_band, self.nir_band, 
                self.mask, has_valid_fields=do_clustering
            )
            results['fpar'] = cluster_data(fpar, mode=ClusterMode.PRESERVE_ZERO) if do_clustering else fpar
        else:
            results['fpar'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        # ET
        if do_invertion and do_invertion.get('ET', {}).get('invertible'):
            et = cal_et(ndvi, self.mask, has_valid_fields=do_clustering)
            results['et'] = cluster_data(et, mode=ClusterMode.PRESERVE_ZERO) if do_clustering else et
        else:
            results['et'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        # FVC
        if do_invertion and do_invertion.get('FVC', {}).get('invertible'):
            fvc = cal_fvc(ndvi, self.mask, has_valid_fields=do_clustering)
            results['fvc'] = cluster_data(fvc, mode=ClusterMode.PRESERVE_ZERO) if do_clustering else fvc
        else:
            results['fvc'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        # Tillering
        if do_invertion and do_invertion.get('Tillering', {}).get('invertible'):
            tillering = cal_fenlie(ndvi, self.mask, has_valid_fields=do_clustering)
            results['tillering'] = cluster_data(tillering, mode=ClusterMode.PRESERVE_ZERO) if do_clustering else tillering
        else:
            results['tillering'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        # Irrigation Order
        if do_invertion and do_invertion.get('Irrigation', {}).get('invertible'):
            irrigation = calculate_irrigation_order(
                self.mask, results['nddi'], results['ndvi'], 
                has_valid_fields=do_clustering
            )
            results['irrigation'] = cluster_data(irrigation, mode=ClusterMode.PRESERVE_ZERO) if do_clustering else irrigation
        else:
            results['irrigation'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        # Fertilization Order
        if do_invertion and do_invertion.get('Fertilization', {}).get('invertible'):
            fertilization = calculate_fertilization_order(
                self.mask, results['ndni'], results['ndvi'],
                has_valid_fields=do_clustering
            )
            results['fertilization'] = cluster_data(fertilization, mode=ClusterMode.PRESERVE_ZERO) if do_clustering else fertilization
        else:
            results['fertilization'] = mat_nan_generation(
                self.green_band, self.mask, do_clustering
            )
        
        return results
    
    def _save_results(
        self,
        results: Dict[str, np.ndarray],
        savepath: str,
        suffix: str,
        do_clustering: bool,
        detection_function: Optional[List[str]]
    ) -> None:
        """Save processing results to files.
        
        Args:
            results: Dictionary of result arrays.
            savepath: Output directory.
            suffix: File suffix.
            do_clustering: Whether clustering was performed.
            detection_function: List of specific functions to save (None = all).
        """
        # Create output directory
        os.makedirs(savepath, exist_ok=True)
        
        # Define output structure
        struct_data = {
            "vigor_level": {"apply_mask_2": True, "datai": results['ndvi']},
            "irrigation_order": {"apply_mask_2": False, "datai": results['irrigation']},
            "drought_level": {"apply_mask_2": True, "datai": results['nddi']},
            "leaf_nitrogen_content": {"apply_mask_2": True, "datai": results['ndni']},
            "yield_per_unit_area": {"apply_mask_2": True, "datai": results['yield']},
            "photosynthetically_active_radiation": {"apply_mask_2": True, "datai": results['fpar']},
            "evapotranspiration": {"apply_mask_2": True, "datai": results['et']},
            "germination_rate": {"apply_mask_2": True, "datai": results['fvc']},
            "effective_tillering": {"apply_mask_2": True, "datai": results['tillering']},
            "fertilization_order": {"apply_mask_2": False, "datai": results['fertilization']},
        }
        
        # Save each output
        for key, value in struct_data.items():
            if not detection_function or key in detection_function:
                save_tiff(
                    os.path.join(savepath, f"{key}-{suffix}.tif"),
                    os.path.join(savepath, f"{key}-{suffix}.shp"),
                    self.width, self.height, self.geotrans, self.proj,
                    value["datai"], self.mask,
                    do_clustering=do_clustering,
                    apply_mask_2=value["apply_mask_2"]
                )
    
    def _process_weather_data(
        self,
        savepath: str,
        suffix: str,
        do_clustering: bool,
        detection_function: Optional[List[str]]
    ) -> None:
        """Process weather data if available.
        
        Args:
            savepath: Output directory.
            suffix: File suffix.
            do_clustering: Whether to perform clustering.
            detection_function: List of specific functions to process (None = all).
        """
        lon1 = np.linspace(
            self.geotrans[0],
            self.geotrans[0] + self.width * self.geotrans[1],
            self.width
        )
        lat1 = np.linspace(
            self.geotrans[3],
            self.geotrans[3] + self.width * self.geotrans[-1],
            self.height
        )
        
        for name in ["air_temperature", "accumulated_rainfall", "accumulated_temperature"]:
            if not detection_function or name in detection_function:
                imgfile1 = os.path.join(self.weatherpath, f"Idw_{name}-{suffix}.tif")
                if os.path.exists(imgfile1):
                    data1, width1, height1, geotrans1, proj1 = read_tiff(imgfile1)
                    lon2 = np.linspace(
                        geotrans1[0],
                        geotrans1[0] + width1 * geotrans1[1],
                        width1
                    )
                    lat2 = np.linspace(
                        geotrans1[3],
                        geotrans1[3] + width1 * geotrans1[-1],
                        height1
                    )
                    f = interp2d(lon2, lat2, data1, kind="linear")
                    dd = f(lon1, lat1)
                    dd = np.where(self.mask == 2, dd[::-1, :], np.nan)
                    dd_clustered = cluster_data(dd, mode=ClusterMode.PRESERVE_ZERO)
                    save_tiff(
                        os.path.join(savepath, f"{name}-{suffix}.tif"),
                        os.path.join(savepath, f"{name}-{suffix}.shp"),
                        self.width, self.height, self.geotrans, self.proj,
                        dd_clustered, self.mask, do_clustering=do_clustering
                    )
    
    def _prepare_visualization_results(
        self,
        results: Dict[str, np.ndarray],
        ndvi: np.ndarray
    ) -> Dict[str, Any]:
        """Prepare visualization results.
        
        Args:
            results: Processed results dictionary.
            ndvi: NDVI array.
            
        Returns:
            Dictionary containing visualization data.
        """
        from .constants import BAND_NAMES
        
        return {
            'original_bands': (self.data, BAND_NAMES),
            'mask': (self.mask, 'Land Cover Mask'),
            'raw_indices': {
                'NDVI': (ndvi, '植被长势'),
                'NDDI': (results['nddi'], '干旱指数'),
                'NDNI': (results['ndni'], '叶氮含量'),
                'Yield': (results['yield'], '单位面积产量'),
                'PAR': (results['fpar'], '光合有效辐射'),
                'ET': (results['et'], '蒸散量'),
                'FVC': (results['fvc'], '出苗率'),
                'Tillering': (results['tillering'], '有效分蘖'),
                'Irrigation': (results['irrigation'], '灌溉优先级'),
                'Fertilization': (results['fertilization'], '施肥优先级')
            },
            'clustered_indices': {
                'NDVI': (results['ndvi'], '植被长势(聚类)'),
                'NDDI': (results['nddi'], '干旱指数(聚类)'),
                'NDNI': (results['ndni'], '叶氮含量(聚类)'),
                'Yield': (results['yield'], '单位面积产量(聚类)'),
                'PAR': (results['fpar'], '光合有效辐射(聚类)'),
                'ET': (results['et'], '蒸散量(聚类)'),
                'FVC': (results['fvc'], '出苗率(聚类)'),
                'Tillering': (results['tillering'], '有效分蘖(聚类)'),
                'Irrigation': (results['irrigation'], '灌溉优先级(聚类)'),
                'Fertilization': (results['fertilization'], '施肥优先级(聚类)')
            }
        }


def inverse(
    imgf: str,
    mask: str,
    weatherpath: str,
    savepath: str,
    suffix: str,
    do_clustering: bool = True,
    do_invertion: Optional[Dict[str, Dict[str, Any]]] = None,
    detection_function: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Perform agricultural data inversion (convenience function).
    
    Args:
        imgf: Path to input GeoTIFF file.
        mask: Path to mask file.
        weatherpath: Path to weather data directory.
        savepath: Output directory path.
        suffix: File suffix for output files.
        do_clustering: Whether to perform clustering.
        do_invertion: Dictionary controlling which inversions to perform.
        detection_function: List of specific functions to run (None = all).
        
    Returns:
        Dictionary containing visualization results.
    """
    processor = AgricultureProcessor(imgf, mask, weatherpath)
    return processor.inverse(
        savepath, suffix, do_clustering, do_invertion, detection_function
    )

