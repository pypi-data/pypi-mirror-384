"""Agricultural indicators calculation functions."""
import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Optional

from .constants import (
    NDVI_LOW_THRESHOLD,
    NDVI_HIGH_THRESHOLD,
    PRIESTLEY_TAYLOR_ALPHA,
    NET_RADIATION,
    SOIL_HEAT_FLUX,
    ET_MAX,
    YIELD_MAX,
    YIELD_COEFFICIENTS,
    NDVI_MIN_VALUE,
    NDVI_MAX_VALUE,
)


def safe_divide(a: np.ndarray, b: np.ndarray, fill_value: float = np.nan) -> np.ndarray:
    """Safe division handling divide-by-zero cases.
    
    Args:
        a: Numerator array.
        b: Denominator array.
        fill_value: Value to use when b==0.
        
    Returns:
        Result of a/b with safe handling of zeros.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.divide(a, b)
        if isinstance(result, np.ndarray):
            result[b == 0] = fill_value
        elif b == 0:
            result = fill_value
    return result


def mat_nan_generation(
    green_band: np.ndarray,
    mask: Optional[np.ndarray] = None,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Generate NaN matrix based on mask.
    
    Args:
        green_band: Green band array for shape reference.
        mask: Mask array (optional).
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        Array with NaN values outside valid regions.
    """
    if not has_valid_fields:
        result = np.full_like(green_band, np.nan, dtype=np.float32)
        if mask is not None:
            result[mask > 0] = 1
        else:
            valid_mask = ~np.isnan(green_band)
            result[valid_mask] = 1
        return result
    
    valid_mask = green_band != 0
    mat_nan = np.zeros_like(green_band)
    mat_nan[~valid_mask] = np.nan
    return mat_nan


def calculate_ndvi(
    red_band: np.ndarray,
    nir_band: np.ndarray,
    mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """Calculate Normalized Difference Vegetation Index (NDVI).
    
    Args:
        red_band: Red band array.
        nir_band: Near-infrared band array.
        mask: Optional mask array.
        
    Returns:
        NDVI array.
    """
    denominator = nir_band + red_band
    ndvi = np.zeros_like(denominator, dtype=np.float32)
    valid_mask = denominator != 0
    ndvi[valid_mask] = (nir_band[valid_mask] - red_band[valid_mask]) / denominator[valid_mask]
    
    if mask is not None:
        ndvi = np.where(mask != 0, ndvi, np.nan)
    
    return ndvi


def cal_nddi(
    green_band: np.ndarray,
    red_band: np.ndarray,
    nir_band: np.ndarray,
    mask: Optional[np.ndarray] = None,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate Normalized Difference Drought Index (NDDI).
    
    Uses NIR and Green band ratio to reflect moisture conditions.
    
    Args:
        green_band: Green band array.
        red_band: Red band array (not used but kept for compatibility).
        nir_band: Near-infrared band array.
        mask: Mask array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        NDDI array (higher values indicate more drought).
    """
    if not has_valid_fields:
        result = np.full_like(green_band, np.nan, dtype=np.float32)
        if mask is not None:
            result[mask > 0] = 1
        else:
            valid_mask = ~np.isnan(green_band)
            result[valid_mask] = 1
        return result
    
    # Calculate moisture sensitive index (NIR/Green ratio)
    moisture_index = np.zeros_like(green_band)
    valid_mask = green_band != 0
    moisture_index[valid_mask] = nir_band[valid_mask] / green_band[valid_mask]
    
    # Normalize to reasonable range
    valid_values = moisture_index[valid_mask]
    if len(valid_values) > 0:
        p5 = np.percentile(valid_values, 5)
        p95 = np.percentile(valid_values, 95)
        moisture_index = np.clip(moisture_index, p5, p95)
        
        # Normalize to [0,1]
        moisture_index = (moisture_index - p5) / (p95 - p5)
        
        # Invert so higher drought has higher value
        drought_index = 1 - moisture_index
        
        # Enhance contrast with power function
        drought_index = np.power(drought_index, 1.5)
    else:
        drought_index = np.zeros_like(moisture_index)
    
    drought_index[~valid_mask] = np.nan
    return drought_index


def cal_ndni(
    red_edge: np.ndarray,
    mask: np.ndarray,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate leaf Nitrogen content (NDNI).
    
    Args:
        red_edge: Red edge band array.
        mask: Mask array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        NDNI array (leaf nitrogen content).
    """
    if not has_valid_fields:
        result = np.full_like(red_edge, np.nan, dtype=np.float32)
        result[mask != 0] = 1
        return result
    
    # Convert red edge to reflectance (0-1 range)
    red_edge = red_edge * 0.0001
    
    # Calculate NDNI
    ndni = np.zeros_like(red_edge)
    valid_mask = (mask != 0) & (red_edge > 0) & (red_edge < 1)
    
    ndni[valid_mask] = 4.135 * np.exp(-12.97 * red_edge[valid_mask])
    
    # Handle invalid values
    ndni[~valid_mask] = np.nan
    ndni = np.clip(ndni, 0, 2)
    
    return ndni


def cal_chanliang(
    ndvi: np.ndarray,
    mask: Optional[np.ndarray] = None,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate yield prediction based on NDVI.
    
    Args:
        ndvi: NDVI array.
        mask: Mask array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        Yield prediction array.
    """
    if not has_valid_fields:
        result = np.full_like(ndvi, np.nan, dtype=np.float32)
        if mask is not None:
            result[mask > 0] = 1
        else:
            valid_mask = ~np.isnan(ndvi)
            result[valid_mask] = 1
        return result
    
    if mask is not None:
        ndvi = np.where(mask != 1, ndvi, np.nan)
    
    valid_ndvi = np.clip(ndvi, 0, 1)
    chanliang = np.zeros_like(ndvi)
    valid_mask = ~np.isnan(ndvi)
    
    # Improved segmented yield prediction model
    def yield_model(x):
        a = YIELD_COEFFICIENTS['a']
        b = YIELD_COEFFICIENTS['b']
        c = YIELD_COEFFICIENTS['c']
        d = YIELD_COEFFICIENTS['d']
        return a * (x**3) + b * (x**2) + c * x + d
    
    chanliang[valid_mask] = np.where(
        valid_ndvi[valid_mask] < 0.2,
        0,
        np.where(
            valid_ndvi[valid_mask] < 0.8,
            yield_model(valid_ndvi[valid_mask]),
            YIELD_MAX
        )
    )
    
    # Handle invalid values
    chanliang[~valid_mask] = np.nan
    chanliang[chanliang < 0] = 0
    chanliang[chanliang > YIELD_MAX] = YIELD_MAX
    
    return chanliang


def cal_fpar(
    ndvi: np.ndarray,
    red_band: Optional[np.ndarray] = None,
    nir_band: Optional[np.ndarray] = None,
    mask: Optional[np.ndarray] = None,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate Fraction of Photosynthetically Active Radiation (FPAR).
    
    Args:
        ndvi: NDVI array.
        red_band: Red band array (optional).
        nir_band: NIR band array (optional).
        mask: Mask array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        FPAR array.
    """
    if not has_valid_fields:
        result = np.full_like(ndvi, np.nan, dtype=np.float32)
        if mask is not None:
            result[mask > 0] = 1
        else:
            valid_mask = ~np.isnan(ndvi)
            result[valid_mask] = 1
        return result
    
    # If no band data provided, use simple NDVI method
    if red_band is None or nir_band is None:
        fpar = np.clip(ndvi, 0, 1)
        fpar = 0.2 + 0.7 * np.power(fpar, 0.7)
        return fpar
    
    # Calculate NIR contribution
    nir_contribution = np.zeros_like(nir_band)
    valid_mask = (nir_band + red_band) != 0
    nir_contribution[valid_mask] = nir_band[valid_mask] / (nir_band[valid_mask] + red_band[valid_mask])
    
    # Normalize NIR contribution
    valid_values = nir_contribution[valid_mask]
    if len(valid_values) > 0:
        p5 = np.percentile(valid_values, 5)
        p95 = np.percentile(valid_values, 95)
        nir_contribution = np.clip(nir_contribution, p5, p95)
        nir_contribution = (nir_contribution - p5) / (p95 - p5)
    
    # Combine NDVI and NIR contribution
    fpar = 0.7 * np.clip(ndvi, 0, 1) + 0.3 * nir_contribution
    
    # Use piecewise function to enhance contrast
    mask_low = fpar < 0.5
    mask_high = ~mask_low
    
    fpar_enhanced = np.zeros_like(fpar)
    fpar_enhanced[mask_low] = 0.4 * np.power(fpar[mask_low] * 2, 1.2)
    fpar_enhanced[mask_high] = 0.4 + 0.6 * np.power((fpar[mask_high] - 0.5) * 2, 0.8)
    
    # Ensure valid range
    fpar_enhanced = np.clip(fpar_enhanced, 0.1, 0.95)
    
    # Apply Gaussian smoothing
    fpar_smooth = gaussian_filter(fpar_enhanced, sigma=0.5)
    
    return fpar_smooth


def cal_et(
    ndvi: np.ndarray,
    mask: Optional[np.ndarray] = None,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate Evapotranspiration (ET).
    
    Args:
        ndvi: NDVI array.
        mask: Mask array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        ET array (mm/day).
    """
    if not has_valid_fields:
        result = np.full_like(ndvi, np.nan, dtype=np.float32)
        if mask is not None:
            result[mask > 0] = 1
        else:
            valid_mask = ~np.isnan(ndvi)
            result[valid_mask] = 1
        return result
    
    if mask is not None:
        ndvi = np.where(mask != 1, ndvi, np.nan)
    
    valid_ndvi = np.clip(ndvi, 0, 1)
    et = np.zeros_like(ndvi)
    valid_mask = ~np.isnan(ndvi)
    
    # Priestley-Taylor simplified equation
    fc = valid_ndvi ** 2  # Vegetation coverage
    
    # Calculate daily ET (mm/day)
    et[valid_mask] = PRIESTLEY_TAYLOR_ALPHA * fc[valid_mask] * (NET_RADIATION - SOIL_HEAT_FLUX) * 0.408
    
    # Handle invalid regions
    et[~valid_mask] = np.nan
    et = np.clip(et, 0, ET_MAX)
    
    return et


def cal_fvc(
    ndvi: np.ndarray,
    mask: Optional[np.ndarray] = None,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate Fractional Vegetation Cover (FVC).
    
    Args:
        ndvi: NDVI array.
        mask: Mask array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        FVC array.
    """
    if not has_valid_fields:
        result = np.full_like(ndvi, np.nan, dtype=np.float32)
        if mask is not None:
            result[mask > 0] = 1
        else:
            valid_mask = ~np.isnan(ndvi)
            result[valid_mask] = 1
        return result
    
    return (ndvi - NDVI_MIN_VALUE) / (NDVI_MAX_VALUE - NDVI_MIN_VALUE)


def cal_fenlie(
    ndvi: np.ndarray,
    mask: Optional[np.ndarray] = None,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate tillering number.
    
    Args:
        ndvi: NDVI array.
        mask: Mask array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        Tillering number array.
    """
    if not has_valid_fields:
        result = np.full_like(ndvi, np.nan, dtype=np.float32)
        if mask is not None:
            result[mask > 0] = 1
        else:
            valid_mask = ~np.isnan(ndvi)
            result[valid_mask] = 1
        return result
    
    return ndvi * 15


def calculate_irrigation_order(
    mask: np.ndarray,
    nddi: np.ndarray,
    ndvi: np.ndarray,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate irrigation priority based on drought index and vegetation status.
    
    Args:
        mask: Mask array (non-zero indicates calculation area).
        nddi: Drought index array.
        ndvi: NDVI array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        Irrigation priority array (1-10, higher priority means more urgent).
    """
    if not has_valid_fields:
        result = np.full_like(mask, np.nan, dtype=np.float32)
        result[mask != 0] = 1
        return result
    
    # Calculate comprehensive score (higher NDDI, lower NDVI = higher priority)
    score = np.full_like(nddi, np.nan)
    valid_mask = (mask != 0) & ~np.isnan(nddi) & ~np.isnan(ndvi)
    score[valid_mask] = 0.7 * nddi[valid_mask] - 0.3 * ndvi[valid_mask]
    
    # Divide scores into 10 levels
    valid_scores = score[valid_mask]
    if len(valid_scores) > 0:
        percentiles = np.percentile(valid_scores, np.linspace(0, 100, 11))
        
        irrigation_order = np.full_like(score, np.nan)
        for i in range(10):
            mask_i = (score >= percentiles[i]) & (score <= percentiles[i+1])
            irrigation_order[mask_i] = 10 - i
        
        return irrigation_order
    else:
        return np.full_like(mask, np.nan)


def calculate_fertilization_order(
    mask: np.ndarray,
    ndni: np.ndarray,
    ndvi: np.ndarray,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Calculate fertilization priority based on nitrogen content and vegetation status.
    
    Args:
        mask: Mask array (non-zero indicates calculation area).
        ndni: Leaf nitrogen content array.
        ndvi: NDVI array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        Fertilization priority array (1-10, higher priority means more urgent).
    """
    if not has_valid_fields:
        result = np.full_like(mask, np.nan, dtype=np.float32)
        result[mask != 0] = 1
        return result
    
    # Calculate comprehensive score (lower NDNI, higher NDVI = higher priority)
    score = np.full_like(ndni, np.nan)
    valid_mask = (mask != 0) & ~np.isnan(ndni) & ~np.isnan(ndvi)
    score[valid_mask] = -0.7 * ndni[valid_mask] + 0.3 * ndvi[valid_mask]
    
    # Divide scores into 10 levels
    valid_scores = score[valid_mask]
    if len(valid_scores) > 0:
        percentiles = np.percentile(valid_scores, np.linspace(0, 100, 11))
        
        fertilization_order = np.full_like(score, np.nan)
        for i in range(10):
            mask_i = (score >= percentiles[i]) & (score <= percentiles[i+1])
            fertilization_order[mask_i] = 10 - i
        
        return fertilization_order
    else:
        return np.full_like(mask, np.nan)


def check_vegetation_status(ndvi: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Check vegetation growth status for each pixel.
    
    Args:
        ndvi: NDVI array.
        mask: Mask array.
        
    Returns:
        Boolean array where True indicates vegetation growth.
    """
    vegetation_mask = np.zeros_like(ndvi, dtype=bool)
    
    # Only check in valid farmland area (mask==2)
    valid_area = (mask == 2) & ~np.isnan(ndvi)
    
    if not np.any(valid_area):
        return vegetation_mask
    
    # Calculate NDVI statistics in valid area
    valid_ndvi = ndvi[valid_area]
    mean_ndvi = np.nanmean(valid_ndvi)
    
    # Adjust threshold dynamically based on mean NDVI
    if mean_ndvi >= NDVI_HIGH_THRESHOLD:
        vegetation_mask[valid_area] = ndvi[valid_area] >= NDVI_HIGH_THRESHOLD
    elif mean_ndvi >= NDVI_LOW_THRESHOLD:
        vegetation_mask[valid_area] = ndvi[valid_area] >= NDVI_LOW_THRESHOLD
    else:
        # Keep top 20% if mean NDVI is very low
        if len(valid_ndvi) > 0:
            threshold = np.percentile(valid_ndvi[~np.isnan(valid_ndvi)], 80)
            vegetation_mask[valid_area] = ndvi[valid_area] >= threshold
    
    return vegetation_mask

