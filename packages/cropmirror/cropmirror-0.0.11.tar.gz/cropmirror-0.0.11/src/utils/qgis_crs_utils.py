"""QGIS-compatible CRS utilities for shapefile processing."""

import os
import logging
from typing import Optional, Union


def create_qgis_compatible_prj(filepath: str, crs: Union[str, object, None]) -> bool:
    """
    创建QGIS兼容的.prj文件。
    使用QGIS偏好的WKT格式和命名约定。
    """
    if not filepath.endswith('.shp'):
        filepath = filepath.replace('.shp', '.shp')
    
    prj_path = os.path.splitext(filepath)[0] + ".prj"
    
    try:
        if crs is not None:
            prj_wkt = _get_qgis_crs_wkt(crs)
        else:
            prj_wkt = _get_qgis_wgs84_wkt()
        
        # 确保格式正确，移除换行符
        prj_wkt = prj_wkt.replace('\n', '').replace('\r', '').strip()
        
        # 写入文件，使用UTF-8编码
        with open(prj_path, 'w', encoding='utf-8') as f:
            f.write(prj_wkt)
        
        logging.info(f"Created QGIS-compatible .prj file: {prj_path}")
        logging.info(f"CRS: {prj_wkt[:100]}...")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create QGIS-compatible .prj file: {e}")
        return False


def _get_qgis_crs_wkt(crs: Union[str, object]) -> str:
    """获取QGIS兼容的CRS WKT格式。"""
    try:
        if isinstance(crs, str):
            if crs.upper().startswith('EPSG:'):
                return _qgis_epsg_to_wkt(crs)
            return crs
        
        # 对于CRS对象，尝试获取WKT并转换为QGIS格式
        if hasattr(crs, 'to_string'):
            
            return _qgis_epsg_to_wkt( crs.to_string())
        elif hasattr(crs, 'to_wkt'): # to_wkt 生成的内容，qgis不支持，python也读取不到
            wkt = crs.to_wkt()
            return _convert_to_qgis_wkt(wkt)
        else:
            return str(crs)
            
    except Exception as e:
        logging.warning(f"Failed to convert CRS to QGIS WKT: {e}")
        return _get_qgis_wgs84_wkt()


def _qgis_epsg_to_wkt(epsg_code: str) -> str:
    """将EPSG代码转换为QGIS兼容的WKT格式。"""
    epsg_code = epsg_code.upper()
    
    # QGIS 兼容的 WKT 格式
    qgis_wkt_map = {
        'EPSG:4326': _get_qgis_wgs84_wkt(),
        'EPSG:3857': _get_qgis_web_mercator_wkt(),
        'EPSG:32649': _get_qgis_utm_49n_wkt(),
        'EPSG:32650': _get_qgis_utm_50n_wkt(),
        'EPSG:32651': _get_qgis_utm_51n_wkt(),
    }
    
    if epsg_code in qgis_wkt_map:
        return qgis_wkt_map[epsg_code]
    
    logging.warning(f"Unknown EPSG code: {epsg_code}, using QGIS WGS84")
    return _get_qgis_wgs84_wkt()


def _get_qgis_wgs84_wkt() -> str:
    """获取QGIS兼容的WGS84 WKT。"""
    return 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]]'


def _get_qgis_web_mercator_wkt() -> str:
    """获取QGIS兼容的Web Mercator WKT。"""
    return 'PROJCS["WGS_84_Pseudo_Mercator",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],PARAMETER["Standard_Parallel_1",0],UNIT["Meter",1]]'


def _get_qgis_utm_49n_wkt() -> str:
    """获取QGIS兼容的UTM Zone 49N WKT。"""
    return 'PROJCS["WGS_84_UTM_Zone_49N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",111],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0],UNIT["Meter",1]]'


def _get_qgis_utm_50n_wkt() -> str:
    """获取QGIS兼容的UTM Zone 50N WKT。"""
    return 'PROJCS["WGS_84_UTM_Zone_50N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",117],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0],UNIT["Meter",1]]'


def _get_qgis_utm_51n_wkt() -> str:
    """获取QGIS兼容的UTM Zone 51N WKT。"""
    return 'PROJCS["WGS_84_UTM_Zone_51N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",123],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0],UNIT["Meter",1]]'


def _convert_to_qgis_wkt(wkt: str) -> str:
    """将标准WKT转换为QGIS兼容的格式。"""
    # QGIS 偏好的命名约定
    qgis_replacements = {
        '"WGS 84"': '"GCS_WGS_1984"',
        '"WGS_1984"': '"D_WGS_1984"',
        '"WGS 84"': '"WGS_1984"',
        '"degree"': '"Degree"',
        '"metre"': '"Meter"',
        '"Greenwich"': '"Greenwich"',
        # 投影参数命名
        '"false_easting"': '"False_Easting"',
        '"false_northing"': '"False_Northing"',
        '"central_meridian"': '"Central_Meridian"',
        '"scale_factor"': '"Scale_Factor"',
        '"latitude_of_origin"': '"Latitude_Of_Origin"',
        '"standard_parallel_1"': '"Standard_Parallel_1"',
        # 投影名称
        '"Transverse_Mercator"': '"Transverse_Mercator"',
        '"Mercator_1SP"': '"Mercator"',
    }
    
    # 应用替换
    for old, new in qgis_replacements.items():
        wkt = wkt.replace(old, new)
    
    return wkt


def fix_existing_prj_for_qgis(filepath: str) -> bool:
    """
    修复现有.prj文件，使其与QGIS兼容。
    """
    if not filepath.endswith('.shp'):
        filepath = filepath.replace('.shp', '.shp')
    
    prj_path = os.path.splitext(filepath)[0] + ".prj"
    
    if not os.path.exists(prj_path):
        logging.warning(f".prj file not found: {prj_path}")
        return False
    
    try:
        # 读取现有内容
        with open(prj_path, 'r', encoding='utf-8') as f:
            original_wkt = f.read().strip()
        
        # 转换为QGIS兼容格式
        qgis_wkt = _convert_to_qgis_wkt(original_wkt)
        
        # 如果内容有变化，写入新文件
        if qgis_wkt != original_wkt:
            with open(prj_path, 'w', encoding='utf-8') as f:
                f.write(qgis_wkt)
            logging.info(f"Fixed .prj file for QGIS compatibility: {prj_path}")
            return True
        else:
            logging.info(f".prj file already QGIS compatible: {prj_path}")
            return True
            
    except Exception as e:
        logging.error(f"Failed to fix .prj file for QGIS: {e}")
        return False
