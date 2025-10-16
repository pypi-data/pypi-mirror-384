import rasterio
from rasterio import features
import shapely.geometry
import shapely.ops


def tif2geometry(tif_file):
    # 通过tif文件生成geojson，支持MultiPolygon

    with rasterio.open(tif_file) as src:
        mask = None
        if src.count > 0:
            # 尝试获取主波段的非nodata区域掩膜
            data = src.read(1)
            nodata = src.nodata
            if nodata is not None:
                mask = data != nodata
            else:
                # 若无nodata，所有非零像元作为有效区
                mask = data != 0
        else:
            mask = None

        # 使用rasterio.features.shapes生成栅格中有效区域的多边形
        results = []
        if mask is not None:
            shapes = features.shapes(data, mask=mask, transform=src.transform)
            for geom, value in shapes:
                shape = shapely.geometry.shape(geom)
                if shape.is_valid and not shape.is_empty:
                    results.append(shape)
        else:
            # fallback: 仅用影像四至生成单一矩形
            bounds = src.bounds
            shape = shapely.geometry.box(*bounds)
            results.append(shape)

        # 合并并精简多边形
        # merge所有多边形为MultiPolygon或Polygon
        mp = shapely.ops.unary_union(results)
        if isinstance(mp, shapely.geometry.Polygon):
            geometry = {
                "type": "Polygon",
                "coordinates": 
                    list(mp.exterior.coords) and [list(mp.exterior.coords)]
                ,
            }
        elif isinstance(mp, shapely.geometry.MultiPolygon):
            geometry = {
                "type": "MultiPolygon",
                "coordinates": [
                    [list(poly.exterior.coords) for poly in mp.geoms and mp.geoms]
                ],
            }
        else:
            # fallback: 外包矩形
            bounds = src.bounds
            box_poly = shapely.geometry.box(*bounds)
            geometry = {
                "type": "Polygon",
                "coordinates": [list(box_poly.exterior.coords)],
            }
        return geometry,src.crs


def tif2geojson(tif_file):
    # 通过tif文件生成geojson，支持MultiPolygon

    import geojson

    geometry, crs = tif2geometry(tif_file)

    # 转换geometry为geojson格式
    geometry_geojson = geojson.Feature(geometry=geometry)

    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": crs.to_string()}},
        "features": [geometry_geojson],
    }
