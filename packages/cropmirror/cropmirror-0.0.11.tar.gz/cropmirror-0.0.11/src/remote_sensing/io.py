"""Input/Output operations for GeoTIFF and raster data."""
from typing import Tuple, Optional
import numpy as np
from osgeo import gdal, ogr, osr
import logging


def read_tiff(imgfile: str) -> Tuple[np.ndarray, int, int, tuple, str]:
    """Read GeoTIFF file and return data and metadata.
    
    Args:
        imgfile: Path to GeoTIFF file.
        
    Returns:
        Tuple of (dataset, width, height, geotransform, projection).
    """
    data = gdal.Open(imgfile)
    if data is None:
        raise FileNotFoundError(f"Cannot open file: {imgfile}")
    
    dataset = data.ReadAsArray()
    im_width = data.RasterXSize
    im_height = data.RasterYSize
    im_geotrans = data.GetGeoTransform()
    im_proj = data.GetProjection()
    
    data = None  # Close file
    return dataset, im_width, im_height, im_geotrans, im_proj


def save_tiff(
    savename: str,
    saveshp: str,
    im_width: int,
    im_height: int,
    im_geotrans: tuple,
    im_proj: str,
    datai: np.ndarray,
    mask: np.ndarray,
    do_clustering: bool = True,
    apply_mask_2: bool = True
) -> None:
    """Save processed data to GeoTIFF and shapefile.
    
    Args:
        savename: Output GeoTIFF file path.
        saveshp: Output shapefile path.
        im_width: Image width.
        im_height: Image height.
        im_geotrans: GeoTransform tuple.
        im_proj: Projection string.
        datai: Data array to save.
        mask: Mask array.
        do_clustering: Whether clustering was performed.
        apply_mask_2: Whether to apply mask==2 filter.
    """
    logging.info(f"Saving GeoTIFF to {savename}")
    
    # Check if clustering is needed
    valid_data = datai[~np.isnan(datai)]
    unique_values = np.unique(valid_data)
    should_cluster = do_clustering and len(unique_values) > 1
    
    cluster_centers = None
    label_to_center = {}
    
    # Perform clustering if needed
    if should_cluster:
        logging.info("Performing clustering for output")
        from sklearn.cluster import KMeans
        
        kmeans = KMeans(n_clusters=min(5, len(unique_values)), random_state=42)
        valid_data_reshaped = datai[~np.isnan(datai)].reshape(-1, 1)
        
        if len(valid_data_reshaped) > 0:
            kmeans.fit(valid_data_reshaped)
            labels = kmeans.labels_
            cluster_centers = kmeans.cluster_centers_.flatten()
            
            # Map cluster labels to data
            clustered_data = np.full_like(datai, np.nan)
            clustered_data[~np.isnan(datai)] = labels + 1
            datai = clustered_data
            
            # Create label to center mapping
            label_to_center = {label + 1: center for label, center in enumerate(cluster_centers)}
    else:
        logging.info("Skipping clustering")
        label_to_center = {1: np.mean(valid_data)} if len(valid_data) > 0 else {1: 0}
    
    # Apply mask filter
    if apply_mask_2:
        datai = np.where(mask == 2, datai, np.nan)
    else:
        datai = np.where(mask != 0, datai, np.nan)
    
    # Save GeoTIFF
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(savename, im_width, im_height, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform(im_geotrans)
    dataset.SetProjection(im_proj)
    dataset.GetRasterBand(1).SetNoDataValue(np.nan)
    dataset.GetRasterBand(1).WriteArray(datai)
    
    # Create shapefile
    _create_shapefile(
        saveshp, im_proj, dataset, datai, 
        im_width, im_height, im_geotrans, label_to_center
    )
    
    dataset = None  # Close file
    logging.info(f"Successfully saved {savename}")


def _create_shapefile(
    saveshp: str,
    im_proj: str,
    dataset: gdal.Dataset,
    datai: np.ndarray,
    im_width: int,
    im_height: int,
    im_geotrans: tuple,
    label_to_center: dict
) -> None:
    """Create shapefile from raster data.
    
    Args:
        saveshp: Output shapefile path.
        im_proj: Projection string.
        dataset: GDAL dataset.
        datai: Data array.
        im_width: Image width.
        im_height: Image height.
        im_geotrans: GeoTransform tuple.
        label_to_center: Mapping from labels to cluster centers.
    """
    import os
    
    drv = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(saveshp):
        drv.DeleteDataSource(saveshp)
    
    polygon = drv.CreateDataSource(saveshp)
    proj_raster = osr.SpatialReference()
    proj_raster.ImportFromWkt(im_proj)
    poly_layer = polygon.CreateLayer("shp", srs=proj_raster, geom_type=ogr.wkbMultiPolygon)
    
    # Add value field
    value_field = ogr.FieldDefn("value", ogr.OFTReal)
    poly_layer.CreateField(value_field)
    
    # Create mask for valid data
    mask_array = np.where(~np.isnan(datai), 1, 0)
    driver = gdal.GetDriverByName("GTiff")
    mask_dataset = driver.Create('/vsimem/mask.tif', im_width, im_height, 1, gdal.GDT_Byte)
    mask_dataset.SetGeoTransform(im_geotrans)
    mask_dataset.SetProjection(im_proj)
    mask_dataset.GetRasterBand(1).WriteArray(mask_array)
    
    # Polygonize
    gdal.FPolygonize(dataset.GetRasterBand(1), mask_dataset.GetRasterBand(1), poly_layer, 0)
    
    # Update feature values with cluster centers
    for feature in poly_layer:
        label = feature.GetField(0)
        if label is not None and label in label_to_center:
            center_value = label_to_center[label]
            feature.SetField("value", float(center_value))
            poly_layer.SetFeature(feature)
    
    # Cleanup
    mask_dataset = None
    gdal.Unlink('/vsimem/mask.tif')
    polygon.SyncToDisk()
    polygon = None


def read_img(filename: str) -> Tuple[str, tuple, np.ndarray, int, int, int]:
    """Read image file with GDAL.
    
    Args:
        filename: Path to image file.
        
    Returns:
        Tuple of (projection, geotransform, data, width, height, band_count).
    """
    dataset = gdal.Open(filename)
    if dataset is None:
        raise FileNotFoundError(f"Cannot find/open {filename}")
    
    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_band = dataset.RasterCount
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)
    
    dataset = None
    return im_proj, im_geotrans, im_data, im_width, im_height, im_band


def write_img(filename: str, im_proj: str, im_geotrans: tuple, im_data: np.ndarray) -> None:
    """Write image to file with GDAL.
    
    Args:
        filename: Output file path.
        im_proj: Projection string.
        im_geotrans: GeoTransform tuple.
        im_data: Image data array.
    """
    import pathlib
    
    # Determine data type
    dtype_to_gdal = {
        "uint8": gdal.GDT_Byte,
        "uint16": gdal.GDT_UInt16,
        "int16": gdal.GDT_Int16,
        "uint32": gdal.GDT_UInt32,
        "int32": gdal.GDT_Int32,
        "float32": gdal.GDT_Float32,
        "float64": gdal.GDT_Float64,
    }
    
    datatype = dtype_to_gdal.get(im_data.dtype.name, gdal.GDT_Float32)
    
    # Get dimensions
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
    
    # Create directory if needed
    pathlib.Path(filename).parent.mkdir(parents=True, exist_ok=True)
    
    # Create dataset
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(filename, im_width, im_height, im_bands, datatype)
    dataset.SetGeoTransform(im_geotrans)
    dataset.SetProjection(im_proj)
    
    # Write data
    if im_bands == 1:
        dataset.GetRasterBand(1).WriteArray(im_data)
    else:
        for i in range(im_bands):
            dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
    
    dataset = None


def write_tiff(lonn: np.ndarray, latt: np.ndarray, savename: str, data: np.ndarray) -> None:
    """Write GeoTIFF file with WGS84 projection.
    
    Args:
        lonn: Longitude array.
        latt: Latitude array.
        savename: Output file path.
        data: Data array to save.
    """
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(savename, len(lonn), len(latt), 1, gdal.GDT_Float32)
    
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(4326)
    dataset.SetProjection(spatial_ref.ExportToWkt())
    dataset.SetGeoTransform(
        (lonn[0], lonn[1] - lonn[0], 0, latt[-1], 0, latt[-2] - latt[-1])
    )
    dataset.GetRasterBand(1).WriteArray(data)
    dataset = None

