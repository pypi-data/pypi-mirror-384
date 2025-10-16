"""Shapefile processing and value assignment for agricultural data."""
import logging
import os
import glob
import numpy as np
import shapefile
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from math import radians, cos, sin, atan2, sqrt, pi
from PIL import Image
from typing import Dict, Optional

# Try to import from utils module
try:
    from ..utils.polygon import clip_shp_with_geometry
    from ..utils.shp2geojson import shp2geojson
    from ..utils.qgis_crs_utils import create_qgis_compatible_prj
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.polygon import clip_shp_with_geometry
    from utils.shp2geojson import shp2geojson
    from utils.qgis_crs_utils import create_qgis_compatible_prj

from .constants import CROP_FILES


# 计算多边形面积的辅助函数
def calculate_polygon_area(points):
    area = 0
    lnglats = list(zip(*points))
    for i in range(len(lnglats[0]) - 1):
        area += (lnglats[0][i] + lnglats[0][i + 1]) * (
            lnglats[1][i + 1] - lnglats[1][i]
        )
    return abs(area / 2.0)


# 计算点的经纬度之间的距离
def haversine(point1, point2):
    R = 6371000  # 地球半径，单位米
    lat1, lng1 = point1
    lat2, lng2 = point2

    phi1 = radians(lat1)
    phi2 = radians(lat2)
    lam1 = radians(lng1)
    lam2 = radians(lng2)

    d_phi = radians(lat2 - lat1)
    d_lam = radians(lng2 - lng1)

    a = sin(d_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(d_lam / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def shpprocess(shpfile, acquired_time, savefilename):
    # import geopandas as gpd
    gdf = gpd.read_file(shpfile)
    crs = gdf.crs
    r = shapefile.Reader(shpfile)  #'/Volumes/DISK/长势.shp'
    w = shapefile.Writer(savefilename, shapeType=r.shapeType)
    

    # 创建QGIS兼容的.prj文件
    success = create_qgis_compatible_prj(savefilename, crs)
    if not success:
        logging.warning(f"Failed to create QGIS-compatible .prj file for {savefilename}")
    basename = os.path.basename(shpfile).split("-")[0]  #
    
    w.fields = list(r.fields)
    if basename in CROP_FILES:
        w.field("level", "N", 8, 0)
        w.field("crop_type", "C", 40)
        w.field("pyenology", "C", 40)
        w.field("date", "C", 40)
        w.field("Shape_Leng", "F", 8, 5)
        w.field("Shape_Area", "F", 8, 5)
        w.field("Id", "N", 8, 0)
    else:
        w.field("level", "N", 8, 0)
        w.field("date", "C", 40)
        w.field("Shape_Leng", "F", 8, 5)
        w.field("Shape_Area", "F", 8, 5)
        w.field("Id", "N", 8, 0)
    
    # 收集所有有效值
    ll = []
    for rec in r.iterShapeRecords():
        ls = rec.record
        ls.extend([ls[0]])
        if ls[0] is None or np.isnan(ls[0]):
            continue
        else:
            ll.append(float(ls[0]))
    
    # 获取唯一值并排序
    lt = list(set(ll))
    lt.sort()
    
    # 如果列表为空或只包含nan值，添加0作为默认值
    if not lt:
        lt = [0]
    
    logging.info(f"Unique values in shapefile: {lt}")
    
    i = 0
    for rec in r.iterShapeRecords():
        ls = rec.record
        points = rec.shape.points
        parts = rec.shape.parts
        part_points = points
        area = calculate_polygon_area(part_points)
        
        # 计算周长
        length = 0
        for j in range(len(part_points) - 1):
            x1, y1 = part_points[j][0], part_points[j][1]
            x2, y2 = part_points[j + 1][0], part_points[j + 1][1]
            length += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        # 跳过无效值
        if ls is None or ls[0] is None or np.isnan(ls[0]):
            continue
        
        # 获取值的索引，对于0值特殊处理
        value = float(ls[0])
        if value == 0:
            level = 1  # 0值对应level为1
        else:
            try:
                level = lt.index(value) + 1
            except ValueError:
                continue  # 如果值不在列表中，跳过
        
        # 添加属性
        if basename in CROP_FILES:
            ls.extend(
                [
                    level,
                    "paddy",
                    "pustulation-period",
                    acquired_time,
                    length,
                    area,
                    i + 1,
                ]
            )
        else:
            ls.extend([level, acquired_time, length, area, i + 1])
        
        # 写入记录
        w.record(*ls)
        w.shape(rec.shape)
        i = i + 1
    
    w.close()
    



def shp2thumbnail(input_shp_file, output_thumbnail_file, figsize=(1.29, 0.78), dpi=100, cmap='viridis'):
    """
    根据shapefile生成缩略图，并根据 level 字段赋色，保存为指定大小

    参数:
    input_shp_file: str, 输入的shapefile文件路径
    output_thumbnail_file: str, 缩略图的保存路径（推荐WEBP格式）
    figsize: tuple, 图像的尺寸大小（英寸），默认是129x78像素 (1.29x0.78)
    dpi: int, 每英寸的像素数，默认是100
    cmap: str, 色彩映射（colormap），默认是 'viridis'
    """
    # 读取shapefile
    gdf = gpd.read_file(input_shp_file)

    # 检查是否有 'level' 字段
    if 'level' not in gdf.columns:
        raise ValueError("Shapefile doesn't contain 'level' column for coloring")

    # 创建图形和坐标轴
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # 绘制shapefile数据，按 'level' 字段赋色
    gdf.plot(column='level', ax=ax, cmap=cmap)
    # , legend=True, legend_kwds={'label': "Level", 'orientation': "vertical"})

    # 移除坐标轴
    ax.set_axis_off()

    # 保存缩略图为WEBP
    plt.savefig(output_thumbnail_file, format='webp', dpi = dpi, bbox_inches='tight', pad_inches=0.1)

    # 关闭图形窗口，释放内存
    plt.close()

# # 使用示例
# # shp2thumbnail('/path/to/accumulated_rainfall.shp', '/path/to/thumbnail_accumulated_rainfall.webp', cmap='copper')
# # shp2thumbnail('/path/to/accumulated_temperature.shp', '/path/to/thumbnail_accumulated_temperature.webp', cmap='viridis')


def shp2thumbnail2(input_shp_file, output_thumbnail_file, width=129, height=78, dpi=100):
    """
    根据shapefile生成缩略图，并根据 level 字段按照标准RGB配色，保存为指定像素大小（129x78像素）

    参数:
    input_shp_file: str, 输入的shapefile文件路径
    output_thumbnail_file: str, 缩略图的保存路径
    width: int, 缩略图宽度，单位像素，默认129
    height: int, 缩略图高度，单位像素，默认78
    dpi: int, 每英寸的像素数，默认是100
    """

    # 定义所有配色映射
    vigor_level_mapping = {
        "长势极好": (3, 103, 36),
        "长势良好": (115, 204, 20),
        "长势中等": (221, 247, 8),
        "长势较差": (225, 165, 21),
        "长势极差": (178, 28, 9),
    }

    drought_level_mapping = {
        "中度湿润": (27, 63, 102),
        "水淹湿润": (9, 87, 177),
        "轻度湿润": (37, 198, 80),
        "轻度干旱": (241, 241, 80),
        "中度干旱": (241, 190, 30),
        "重度干旱": (241, 241, 80),
    }

    leaf_nitrogen_mapping = {
        "氮过量": (3, 103, 36),
        "富氮": (31, 160, 72),
        "氮含量适中": (69, 228, 29),
        "轻度缺氮": (202, 255, 51),
        "缺氮": (251, 255, 40),
        "严重缺氮": (224, 153, 0),
    }

    yield_mapping = {
        "产量极高": (3, 103, 36),
        "高产量": (115, 204, 20),
        "产量中等": (221, 247, 8),
        "产量较低": (225, 165, 21),
        "产量极低": (178, 28, 9),
    }

    photosynthetically_active_radiation_mapping = {
        "极强": (3, 103, 36),
        "强": (69, 228, 29),
        "中等": (241, 255, 29),
        "较弱": (241, 241, 80),
        "弱": (241, 190, 30),
        "极弱": (208, 203, 105),
    }

    evapotranspiration_mapping = {
        "高": (178, 28, 9),
        "中等偏高": (232, 183, 50),
        "中等": (221, 247, 8),
        "中等偏低": (64, 160, 69),
        "低": (64, 146, 122),
        "极低": (124, 182, 246),
    }

    germination_rate_mapping = {
        "优秀": (3, 103, 36),
        "良好": (31, 160, 72),
        "中等": (69, 228, 29),
        "较差": (195, 233, 16),
        "差": (241, 241, 67),
    }

    # 判断文件名，选择对应的配色映射
    filename = os.path.basename(input_shp_file)

    if "vigor_level" in filename or "effective_tillering" in filename:
        color_mapping = vigor_level_mapping
    elif "drought_level" in filename:
        color_mapping = drought_level_mapping
    elif "leaf_nitrogen_content" in filename:
        color_mapping = leaf_nitrogen_mapping
    elif "yield_per_unit_area" in filename:
        color_mapping = yield_mapping
    elif "photosynthetically_active_radiation" in filename:
        color_mapping = photosynthetically_active_radiation_mapping
    elif "evapotranspiration" in filename:
        color_mapping = evapotranspiration_mapping
    elif "germination_rate" in filename:
        color_mapping = germination_rate_mapping
    else:
        logging.error(f"无法识别的文件名，未匹配到任何配色方案 {filename}")
        raise ValueError(f"无法识别的文件名，未匹配到任何配色方案 {filename}")

    # 读取shapefile
    gdf = gpd.read_file(input_shp_file)

    # 创建图形和坐标轴，先生成接近大小的图像
    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)

    # 将 level 转换为颜色
    gdf["color"] = gdf["level"].map(
        lambda x: color_mapping.get(x, (255, 255, 255))
    )  # 默认白色

    # 绘制时直接使用颜色
    gdf.plot(
        ax=ax,
        color=gdf["color"].apply(lambda rgb: f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"),
    )

    # 移除坐标轴
    ax.set_axis_off()

    # 先生成一个接近大小的临时图片
    temp_image_path = output_thumbnail_file.replace(".webp", "_temp.png")
    plt.savefig(temp_image_path, format="png", dpi=dpi)
    plt.close()  # 关闭图形窗口

    # 使用Pillow打开图像并调整为确切的129x78大小
    img = Image.open(temp_image_path)
    img = img.resize((width, height), Image.Resampling.LANCZOS)

    # 保存为最终的缩略图
    img.save(output_thumbnail_file, format="webp")

    # 删除临时图片
    os.remove(temp_image_path)


# def shp2thumbnail(input_shp_file, output_thumbnail_file, width=129, height=78, dpi=100, cmap='viridis'):
#     """
#     根据shapefile生成缩略图，并根据 level 字段赋色，保存为指定像素大小（129x78像素）

#     参数:
#     input_shp_file: str, 输入的shapefile文件路径
#     output_thumbnail_file: str, 缩略图的保存路径
#     width: int, 缩略图宽度，单位像素，默认129
#     height: int, 缩略图高度，单位像素，默认78
#     dpi: int, 每英寸的像素数，默认是100
#     cmap: str, 色彩映射（colormap），默认是 'viridis'
#     """
#     # 读取shapefile
#     gdf = gpd.read_file(input_shp_file)

#     # 创建图形和坐标轴，先生成接近大小的图像
#     fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)

#     # 绘制shapefile数据，按 'level' 字段赋色
#     gdf.plot(column='level', ax=ax, cmap=cmap)

#     # 移除坐标轴
#     ax.set_axis_off()

#     # 先生成一个接近大小的临时图片
#     temp_image_path = output_thumbnail_file.replace('.webp', '_temp.png')
#     plt.savefig(temp_image_path, format='png', dpi=dpi)
#     plt.close()  # 关闭图形窗口

#     # 使用Pillow打开图像并调整为确切的129x78大小
#     img = Image.open(temp_image_path)
#     img = img.resize((width, height), Image.Resampling.LANCZOS)

#     # 保存为最终的缩略图
#     img.save(output_thumbnail_file, format='webp')

#     # 删除临时图片
#     os.remove(temp_image_path)

# 使用示例
# shp2thumbnail('/path/to/accumulated_rainfall.shp', '/path/to/thumbnail_accumulated_rainfall.webp', width=129, height=78, dpi=100)


def shpvaluedGeoJson(
    shppath,
    valued_save_path,
    geojson_save_path,
    thumbnail_save_path,
    geometry,
    acquired_time,
):
    shps = glob.glob(os.path.join(shppath, "*.shp"))
    if not os.path.exists(valued_save_path):
        os.makedirs(valued_save_path, exist_ok=True)
    if not os.path.exists(geojson_save_path):
        os.makedirs(geojson_save_path, exist_ok=True)
    if not os.path.exists(thumbnail_save_path):
        os.makedirs(thumbnail_save_path, exist_ok=True)

    for shp in shps:
        # logging.info(shp)
        basename = os.path.basename(shp)
        valued_filepath = os.path.join(valued_save_path, basename)
        clip_filepath = os.path.join(
            valued_save_path, basename.split(".")[0] + "_clip.shp"
        )
        geojson_filepath = os.path.join(
            geojson_save_path, basename.split(".")[0] + ".geojson"
        )
        thumbnail_filepath = os.path.join(
            thumbnail_save_path, basename.split(".")[0] + ".webp"
        )
        shpprocess(shp, acquired_time, savefilename=valued_filepath)
        clip_shp_with_geometry(valued_filepath, geometry, clip_filepath)
        shp2geojson(input_shp_file=clip_filepath, output_geojson_file=geojson_filepath)
        
        # 记录shapefile处理完成
        logging.info(f"Processed shapefile: {clip_filepath}")
        
        # 基于shp生成缩略图
        shp2thumbnail(
            input_shp_file=clip_filepath, output_thumbnail_file=thumbnail_filepath
        )


if __name__ == "__main__":
    # 结果tif路径
    pathh = "data/20240909/geotiff"
    shppath = glob.glob(pathh + "/*.shp")
    date = pathh.split("/")[-2]
    # 保存路径
    savepath = "/Users/zhoupeng/Desktop/代码20240911/结果/" + str(date) + "/shp"
    if os.path.exists(savepath):
        pass
    else:
        os.makedirs(savepath)
    for shpf in shppath:
        print(shpf)
        shpprocess(shpf, date, savepath + "/" + shpf.split("/")[-1])
