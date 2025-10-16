"""Mask generation for roads, buildings, and field boundaries."""
from osgeo import gdal
import numpy as np
import os
import logging
import json
import rasterio
from rasterio.mask import mask as rasterio_mask
from pyproj import Transformer
from scipy.ndimage import gaussian_filter
from skimage.filters import threshold_local
from skimage.morphology import binary_dilation, binary_closing, skeletonize
from skimage.feature import hessian_matrix, hessian_matrix_eigvals
from skimage.measure import label, regionprops
from typing import Optional

def read_tiff(imgfile):
    data = gdal.Open(imgfile)
    dataset = data.ReadAsArray()
    im_width = data.RasterXSize
    im_height = data.RasterYSize
    im_geotrans = data.GetGeoTransform()
    im_proj = data.GetProjection()
    return dataset, im_width, im_height, im_geotrans, im_proj

def detect_linear_features(image, sigma=2):
    """检测线性特征（道路和田埂），强化连通性和闭合性"""
    # 使用局部自适应阈值处理NDVI值的空间变化
    block_size = 25  # 局部窗口大小
    local_thresh = threshold_local(image, block_size, offset=0.02)
    binary = image < local_thresh  # 道路和田埂通常NDVI值低于周围区域
    
    # 计算Hessian矩阵的特征值
    H_elems = hessian_matrix(image, sigma=sigma, use_gaussian_derivatives=False)
    eigvals = hessian_matrix_eigvals(H_elems)
    
    # 使用特征值比例识别线性结构
    linear_features = np.abs(eigvals[0]) > 2 * np.abs(eigvals[1])
    
    # 结合局部阈值和线性特征
    combined = binary & linear_features
    
    # 简化处理：直接进行基本的形态学操作
    # 1. 先进行骨架化提取主要线条
    skeleton = skeletonize(combined)
    
    # 2. 移除孤立点和小区域
    labeled = label(skeleton)
    regions = regionprops(labeled)
    
    # 创建有效区域掩码
    valid_regions = np.zeros_like(skeleton, dtype=bool)
    for region in regions:
        # 获取区域掩码
        region_mask = labeled == region.label
        
        # 检查区域大小
        if region.area < 10:  # 小区域
            # 简化：直接跳过小区域，不进行复杂的邻近检查
            continue
        
        # 检查线性特征
        if region.area >= 10 or region.eccentricity > 0.8:  # 较大区域或明显的线性特征
            valid_regions[region_mask] = True
    
    # 3. 使用较小的结构元素进行连接（减少计算量）
    extended = binary_dilation(valid_regions, footprint=np.ones((3, 3)))  # 从5x5改为3x3
    
    # 4. 简化：只进行基本的闭合操作
    extended = binary_closing(extended, footprint=np.ones((3, 3)))  # 从7x7改为3x3
    
    # 5. 再次进行骨架化，保持线条的细节
    skeleton_final = skeletonize(extended)
    
    # 6. 最后进行适度膨胀，使线条更容易看见
    final = binary_dilation(skeleton_final, footprint=np.ones((2, 2)))  # 从3x3改为2x2
    
    # 7. 确保闭合性
    final = binary_closing(final, footprint=np.ones((3, 3)))  # 从5x5改为3x3
    
    # 8. 最后一次移除孤立点
    labeled_final = label(final)
    regions_final = regionprops(labeled_final)
    for region in regions_final:
        if region.area < 15:  # 最终的小区域阈值
            final[labeled_final == region.label] = False
    
    return final

def generate_geometry_mask(geometry, image_path):
    """
    将plot数据转换为掩码
    """

    # 获取图像的坐标系统
    with rasterio.open(image_path) as src:
        image_crs = src.crs
        bounds = src.bounds
        logging.info(f"Image CRS: {image_crs}")
        logging.info(f"Image bounds: {bounds}")
        
        # 使用rasterio创建掩码
        plot_mask, transform = rasterio_mask(src,[geometry], crop=False)
        plot_mask = plot_mask[0]
        logging.info(f"Created mask with shape: {plot_mask.shape}")
        logging.info(f"Mask contains non-zero values: {np.any(plot_mask != 0)}")
        return plot_mask != 0
            


def gener_mask(imgf, outfile, geometry=None):
    """
    生成掩码
    0: 不感兴趣区域（nan区域）
    1: 道路和田埂区域
    2: 有效农田区域
    
    参数:
    imgf: 遥感影像路径
    outfile: 输出掩码文件路径
    plot: GeoJSON格式的地块边界数据
    
    返回值: 
    False 如果有效地块面积比例小于阈值（可能是积雪覆盖）
    True 如果有效地块面积比例大于阈值（正常情况）
    """

    
    # 读取数据
    data, width, height, geotrans, proj = read_tiff(imgf)
    data = data.astype(np.float32)
    
    # 计算NDVI
    red_band = data[5, :, :]
    nir_band = data[7, :, :]
    
    # 标记不感兴趣区域（包括原始数据中的nan和无效值）
    not_interested = np.isnan(red_band) | np.isnan(nir_band) | (red_band <= 0) | (nir_band <= 0)
    interested_area = ~not_interested
    
    # 如果提供了plot数据，创建plot掩码并与interested_area取交集
    if geometry:
        plot_mask = generate_geometry_mask(geometry, imgf)
        if plot_mask is not None:
            interested_area = interested_area & plot_mask
            not_interested = ~interested_area
    
    # 计算NDVI（只在感兴趣区域内计算）
    ndvi = np.zeros_like(red_band)
    ndvi[interested_area] = (nir_band[interested_area] - red_band[interested_area]) / (nir_band[interested_area] + red_band[interested_area])
    
    # 使用NDVI阈值识别地块
    field_mask = (ndvi > 0.03) & interested_area
    
    # 计算有效地块面积比例（相对于感兴趣区域）
    total_interested_area = np.sum(interested_area)
    valid_field_area = np.sum(field_mask)
    field_ratio = valid_field_area / total_interested_area if total_interested_area > 0 else 0
    
    # 创建最终掩码
    final_mask = np.zeros_like(ndvi, dtype=np.float32)
    
    # 不感兴趣区域始终标记为0
    final_mask[not_interested] = 0
    
    # 根据地块识别情况处理感兴趣区域
    if field_ratio < 0.5:  # 阈值可以调整
        logging.warning(f"检测到可能的积雪覆盖情况 (有效地块比例: {field_ratio:.2%})")
        # 将所有感兴趣区域标记为地块，不感兴趣区域保持为0
        final_mask[interested_area] = 2
        has_valid_fields = False
    else:
        # 检测线性特征（道路和田埂）
        linear_features = detect_linear_features(ndvi)
        # 在感兴趣区域内标记道路和地块
        final_mask[linear_features & interested_area] = 2  # 道路和田埂
        final_mask[field_mask & ~linear_features] = 2      # 地块
        has_valid_fields = True
    
    # 最后再次确保不感兴趣区域为0
    final_mask[not_interested] = 0
    
    # 保存结果
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(outfile, width, height, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.GetRasterBand(1).WriteArray(final_mask)
    dataset = None
    
    return has_valid_fields

if __name__ == "__main__":
    # 测试用例
    filname = 'C:\\Users\\Pepsi\\Downloads\\1916003043034710018_psscene_ortho_analytic_8b_sr (2)\\PSScene\\20250416_033110_17_24b4_3B_AnalyticMS_SR_8b_clip.tif'
    outpath = 'C:\\Users\\Pepsi\\Downloads\\1916003043034710018_psscene_ortho_analytic_8b_sr (2)\\20240920_012645_95_24c4_3B_AnalyticMS_SR_8b_clip_mask.dat'
    mask = gener_mask(filname, outpath)