"""Clustering and segmentation functions for agricultural data."""
import numpy as np
from sklearn.cluster import KMeans
from scipy.ndimage import gaussian_filter, binary_closing, binary_opening
from skimage.morphology import remove_small_objects, remove_small_holes
from skimage.segmentation import watershed
from skimage.morphology import closing, disk
from scipy import ndimage
from typing import Union

from .constants import ClusterMode, DEFAULT_N_CLUSTERS, MIN_AREA_RATIO, MIN_REGION_SIZE


def cluster_data(
    data: np.ndarray,
    n_clusters: int = DEFAULT_N_CLUSTERS,
    mode: Union[ClusterMode, str] = ClusterMode.DEFAULT
) -> np.ndarray:
    """Cluster data and post-process to remove edge effects and small regions.
    
    Args:
        data: Input data matrix.
        n_clusters: Number of clusters.
        mode: Clustering mode (ClusterMode enum or string).
        
    Returns:
        Clustered data matrix.
    """
    # Convert string mode to enum if needed
    if isinstance(mode, str):
        mode_map = {
            "DEFAULT": ClusterMode.DEFAULT,
            "PRESERVE_ZERO": ClusterMode.PRESERVE_ZERO,
            "NDNI_SPECIAL": ClusterMode.NDNI_SPECIAL,
        }
        mode = mode_map.get(mode, ClusterMode.DEFAULT)
    
    data = data.copy()
    data[data == -9999] = np.nan
    
    # Get original valid region mask
    original_valid_mask = ~np.isnan(data)
    if not np.any(original_valid_mask):
        return data
    
    data_min = np.nanmin(data)
    data_max = np.nanmax(data)
    
    # Special handling for NDNI mode
    if mode == ClusterMode.NDNI_SPECIAL:
        data[original_valid_mask & (data > 4)] = np.nan
        original_valid_mask = ~np.isnan(data)
        
    if not np.any(original_valid_mask):
        return data
    
    # Gaussian smoothing to reduce noise
    data_smooth = gaussian_filter(np.nan_to_num(data, nan=np.nanmean(data)), sigma=1)
    data_smooth[~original_valid_mask] = np.nan
    
    # Perform KMeans clustering
    valid_data = data_smooth[original_valid_mask].reshape(-1, 1)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(valid_data)
    
    # Create initial clustering result
    datai = np.full_like(data, np.nan)
    datai[original_valid_mask] = kmeans.cluster_centers_[clusters].flatten()
    
    # Morphological processing for each cluster region
    for i in range(len(kmeans.cluster_centers_)):
        cluster_mask = (datai == kmeans.cluster_centers_[i])
        
        # Perform morphological closing to fill small holes
        cluster_mask = binary_closing(cluster_mask, structure=np.ones((3,3)))
        
        # Remove regions smaller than 1% of total area
        total_area = np.sum(original_valid_mask)
        min_area = int(total_area * MIN_AREA_RATIO)
        cluster_mask = remove_small_objects(cluster_mask, min_size=min_area, connectivity=2)
        
        # Fill remaining small holes
        cluster_mask = remove_small_holes(cluster_mask, area_threshold=min_area, connectivity=2)
        
        # Update result
        datai[cluster_mask] = kmeans.cluster_centers_[i]
    
    # Ensure boundary integrity
    datai[~original_valid_mask] = np.nan
    
    # Handle special modes
    if mode == ClusterMode.PRESERVE_ZERO or mode == ClusterMode.NDNI_SPECIAL:
        datai[data == 0] = 0
    
    # Final smoothing for continuity
    valid_mask = ~np.isnan(datai)
    if np.any(valid_mask):
        smoothed = gaussian_filter(np.nan_to_num(datai, nan=np.nanmean(datai)), sigma=0.5)
        datai[valid_mask] = smoothed[valid_mask]
    
    return datai


def segment_fields(
    ndvi: np.ndarray,
    mask: np.ndarray,
    has_valid_fields: bool = True
) -> np.ndarray:
    """Intelligently segment fields using mask information and NDVI similarity.
    
    Mask values:
    - 1: Roads and field boundaries
    - 2: Valid farmland areas
    - Other: Invalid areas
    
    Args:
        ndvi: NDVI array.
        mask: Mask array.
        has_valid_fields: Whether valid fields exist.
        
    Returns:
        Segmented field array with unique labels for each field.
    """
    if not has_valid_fields:
        return mask
    
    # Use mask information
    road_boundary = (mask == 1)
    valid_area = (mask == 2)
    
    # Morphological processing for roads and boundaries
    road_boundary = closing(road_boundary, disk(2))
    
    # Distance transform to find potential field centers
    distance = ndimage.distance_transform_edt(~road_boundary)
    distance[~valid_area] = 0
    
    # Find local maxima as markers
    local_max = ndimage.maximum_filter(distance, size=25) == distance
    local_max[distance < 5] = 0
    
    # Label different regions
    markers, num_features = ndimage.label(local_max)
    
    # Use watershed algorithm for segmentation
    segments = watershed(-distance, markers, mask=valid_area)
    
    # Post-processing: merge small regions considering NDVI similarity
    unique_labels = np.unique(segments[segments > 0])
    region_ndvi = {}
    
    for label in unique_labels:
        region_mask = segments == label
        if np.any(region_mask):
            region_ndvi[label] = np.nanmean(ndvi[region_mask])
    
    # Process small regions
    for label in unique_labels:
        region_mask = segments == label
        region_size = np.sum(region_mask)
        
        if region_size < MIN_REGION_SIZE:
            # Find adjacent larger regions
            dilated = ndimage.binary_dilation(region_mask, iterations=3)
            neighbor_labels = segments[dilated & ~region_mask]
            neighbor_labels = neighbor_labels[neighbor_labels > 0]
            
            if len(neighbor_labels) > 0:
                # Find most similar adjacent region by NDVI
                best_neighbor = None
                min_diff = float('inf')
                current_ndvi = region_ndvi.get(label, 0)
                
                for neighbor in np.unique(neighbor_labels):
                    if neighbor in region_ndvi:
                        diff = abs(current_ndvi - region_ndvi[neighbor])
                        if diff < min_diff:
                            min_diff = diff
                            best_neighbor = neighbor
                
                # Merge if suitable neighbor found
                if best_neighbor is not None:
                    segments[region_mask] = best_neighbor
    
    # Ensure continuous labels
    unique_labels = np.unique(segments)
    unique_labels = unique_labels[unique_labels != 0]
    new_segments = np.zeros_like(segments)
    for i, label in enumerate(unique_labels, 1):
        new_segments[segments == label] = i
    
    # Mark roads and non-farmland areas as 0
    new_segments[road_boundary] = 0
    new_segments[~valid_area] = 0
    
    return new_segments

