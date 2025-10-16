import geopandas as gpd
from math import sqrt
from shapely import wkt
from shapely.geometry import mapping
import geojson
import json
from shapely.geometry import Point, Polygon, MultiPolygon, GeometryCollection
from shapely.geometry import shape
import pandas as pd
from shapely.geometry import box
from geopy.distance import geodesic

def generate_polygon(center_lat, center_lon, distance=805, cap_style="round"):
    gs = gpd.GeoSeries(wkt.loads(f"POINT ({center_lon} {center_lat})"))
    gdf = gpd.GeoDataFrame(geometry=gs)
    gdf.crs = "EPSG:4326"
    gdf = gdf.to_crs("EPSG:3857")
    res = gdf.buffer(
        distance=distance,
        cap_style=cap_style,
    )
    geojson_string = geojson.dumps(
        mapping(wkt.loads(res.to_crs("EPSG:4326").iloc[0].wkt))
    )

    
    geojson_dict = json.loads(geojson_string)
    
    polygon = shape(geojson_dict)
    gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[polygon])
    area = gdf.to_crs(32649).area.iloc[0] /1000000
    print(area)
    return geojson_dict

def generate_rectangle(center_lat, center_lon, width_m, height_m):
    # 计算矩形宽度和高度对应的纬度和经度变化量
    half_width_delta = geodesic(meters=width_m / 2).destination((center_lat, center_lon), bearing=90).longitude - center_lon
    half_height_delta = geodesic(meters=height_m / 2).destination((center_lat, center_lon), bearing=0).latitude - center_lat

    # 计算矩形的边界坐标
    minx = center_lon - half_width_delta
    maxx = center_lon + half_width_delta
    miny = center_lat - half_height_delta
    maxy = center_lat + half_height_delta

    # 使用 box 函数生成矩形
    rectangle = box(minx, miny, maxx, maxy)
    
    # 将 Polygon 对象转换为 GeoJSON 格式
    rectangle_geojson = {
        "type": "Polygon",
        "coordinates": [list(rectangle.exterior.coords)]
    }
    
    return rectangle_geojson


# 不好用
def clip_shp_with_geometry(input_shp, clip_geometry, output_shp):

    to_be_clipped = gpd.read_file(input_shp)

    # 兼容clip_geometry为Polygon或MultiPolygon类型
    if clip_geometry["type"] == 'MultiPolygon':
        # 对每个polygon分别裁剪再合并
        clipped_list = []
        for polygon_list in clip_geometry["coordinates"]:
            for polygon in polygon_list:
                result = to_be_clipped.clip(shape(Polygon(polygon)))
                clipped_list.append(result)
        clipped = gpd.GeoDataFrame(pd.concat(clipped_list, ignore_index=True))
    elif clip_geometry["type"] == 'Polygon':
        clipped = to_be_clipped.clip(shape(Polygon(clip_geometry["coordinates"][0])))
    clipped.set_crs(to_be_clipped.crs, inplace=True)
    clipped.to_file(output_shp, driver='ESRI Shapefile')

def clip_shp_by_polygon(input_shp, clip_polygon_json, output_shp):
    # 读取待裁剪的shp文件
    to_be_clipped = gpd.read_file(input_shp)

    
    # 定义裁剪用的多边形
    if clip_polygon_json["type"] == "Polygon":
        polygon_coords = clip_polygon_json["coordinates"][0]
        clipping_polygon = Polygon(polygon_coords)
    elif clip_polygon_json["type"] == "MultiPolygon":
        polygon_coords = clip_polygon_json["coordinates"]
        clipping_polygon = MultiPolygon(polygon_coords)
    

    # 确保多边形和shp文件在同一坐标参考系统（CRS）
    # 如果CRS不同，需要进行转换

    clipping_polygon = gpd.GeoSeries([clipping_polygon],crs=clip_polygon_json['crs'])
    clipping_polygon = clipping_polygon.to_crs(to_be_clipped.crs).iloc[0]

    # 裁剪操作
    clipped = to_be_clipped.clip(clipping_polygon)

    # 处理不同的几何类型
    valid_geometries = []
    valid_records = []

    for idx, geom in enumerate(clipped.geometry):
        if geom.geom_type == "Polygon":
            valid_geometries.append(geom)
            valid_records.append(clipped.iloc[idx])
        elif geom.geom_type == "MultiPolygon":
            # 使用 .geoms 属性来遍历 MultiPolygon 中的每个 Polygon
            for poly in geom.geoms:
                valid_geometries.append(poly)
                valid_records.append(clipped.iloc[idx])
        elif geom.geom_type == "GeometryCollection":
            # 从 GeometryCollection 中提取多边形
            for sub_geom in geom.geoms:
                if sub_geom.geom_type == "Polygon":
                    valid_geometries.append(sub_geom)
                    valid_records.append(clipped.iloc[idx])

    # 使用有效的几何和属性构建新的 GeoDataFrame
    valid_df = gpd.GeoDataFrame(valid_records, geometry=valid_geometries, crs=to_be_clipped.crs)

    # 检查是否为空，避免保存空文件
    if valid_df.empty:
        print("The clipped result is empty. No output file will be created.")
    else:
        # 保存裁剪后的shp文件
        valid_df.to_file(output_shp)
    
def clip_shp_by_shp(input_shp, clip_shp, output_shp):
    """
    使用一个 shp 文件裁剪另一个 shp 文件

    参数:
    input_shp (str): 输入的 shp 文件路径
    clip_shp (str): 用来裁剪的 shp 文件路径
    output_shp (str): 输出的裁剪后的 shp 文件路径
    """
    # 读取输入的 shp 文件和用来裁剪的 shp 文件
    input_gdf = gpd.read_file(input_shp)

    clip_gdf = gpd.read_file(clip_shp)

    # 进行空间裁剪
    clipped_gdf = gpd.overlay(input_gdf, clip_gdf, how="intersection")

    # 将裁剪后的结果保存为新的 shp 文件
    clipped_gdf.to_file(output_shp)
    

if __name__ == "__main__":
    from tif2geojson import tif2geometry
    
    # multipolygon
    geometry,crs = tif2geometry("E:\\GitHub\\cropmirror\\cropmirror-utils\\src\\test\\planet\\PSScene\\20250824_031308_11_2504_3B_AnalyticMS_SR_8b_clip.tif")
    
    clip_shp_with_geometry("E:\\GitHub\\cropmirror\\cropmirror-utils\\output\\valued\\drought_level-2025-08-24_031308.shp", 
                        geometry, "E:\\GitHub\\cropmirror\\cropmirror-utils\\output\\valued\\drought_level-2025-08-24_031308_clip.shp")
    
    # polygon