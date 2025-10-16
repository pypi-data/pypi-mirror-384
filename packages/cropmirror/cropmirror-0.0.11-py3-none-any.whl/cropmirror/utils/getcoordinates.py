from osgeo import gdal, osr

def get_coordinates(tiffile) -> tuple[float, float]:
    """
    获取tif文件的中心点坐标
    
    Args:
        tiffile: tif文件路径
    Returns:
        tuple[float, float]: 中心点坐标
    """
    dataset = gdal.Open(tiffile)
    if dataset:
        geotransform = dataset.GetGeoTransform()
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        # 计算中心像元坐标
        center_x = geotransform[0] + geotransform[1] * (width / 2) + geotransform[2] * (height / 2)
        center_y = geotransform[3] + geotransform[4] * (width / 2) + geotransform[5] * (height / 2)
        
        # 获取原始坐标系信息
        srs = osr.SpatialReference(wkt=dataset.GetProjection())
        
        # 如果是投影坐标系，需要转换为地理坐标系
        if srs.IsProjected():
            # 创建坐标转换
            target_srs = srs.CloneGeogCS()  # 获取对应的地理坐标系
            transform = osr.CoordinateTransformation(srs, target_srs)
            # 执行转换
            lat, lon, _ = transform.TransformPoint(center_x, center_y)
        else:
            # 如果已经是地理坐标系，直接使用
            lat, lon = center_x, center_y
        dataset = None
        return lon, lat
    else:
        raise ValueError("Failed to open tiff file")