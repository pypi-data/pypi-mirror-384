"""Remote sensing processor for satellite image processing.

This module provides the main entry point for processing satellite imagery
from various sources (Planet, Sentinel, etc.) and extracting agricultural
monitoring indicators.
"""
import json
import sys
import logging
import os
import copy
from datetime import datetime
from osgeo import gdal, osr
from shapely.geometry import Point
# Handle both relative and absolute imports
try:
    from .idw import do_idw
    from .processor import inverse
    from .masking import gener_mask
    from .shapefile_processor import shpvaluedGeoJson
    from .constants import INVERSION_TOPICS
    from ..planet.planet_preprocessor import PlanetPreprocessor
    from ..utils.tif2geojson import tif2geometry,tif2geojson
    from ..utils.getcoordinates import get_coordinates
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    from remote_sensing.idw import do_idw
    from remote_sensing.processor import inverse
    from remote_sensing.masking import gener_mask
    from remote_sensing.shapefile_processor import shpvaluedGeoJson
    from remote_sensing.constants import INVERSION_TOPICS
    from planet.planet_preprocessor import PlanetPreprocessor
    from utils.tif2geojson import tif2geometry,tif2geojson
    from utils.getcoordinates import get_coordinates
class RemoteSensingProcessor(object):
    """Main remote sensing processor for complete satellite image processing pipeline.
    
    This class handles the entire workflow from preprocessed satellite imagery to
    processed agricultural indicators including NDVI, drought index, nitrogen
    content, yield prediction, and management prescriptions.
    
    For Planet imagery, use PlanetPreprocessor first to extract the tiffile,
    or pass the tiffile directly if already extracted.
          
    """
    def __init__(
        self,
        tiffile: str,
        savepath: str,
        detection_function: list = ['vigor_level','irrigation_order','drought_level','leaf_nitrogen_content','yield_per_unit_area','photosynthetically_active_radiation','evapotranspiration','germination_rate','effective_tillering','fertilization_order'],
        acquired_time: str = None, #  获取影像的时间 格式为：YYYY-MM-DD HH:MM:SS
    ) -> None:
        """Initialize the remote sensing processor.
        
        Args:
            tiffile: Path to the GeoTIFF file to process.
            savepath: Directory to save output files.
            acquired_time: Task creation time (format: "YYYY-MM-DD HH:MM:SS").
            detection_function: 检测的专题 列表 默认值为 ['vigor_level','irrigation_order','drought_level','leaf_nitrogen_content','yield_per_unit_area','photosynthetically_active_radiation','evapotranspiration','germination_rate','effective_tillering','fertilization_order']
              vigor_level: 活力水平
              irrigation_order: 灌溉顺序
              drought_level: 干旱水平
              leaf_nitrogen_content: 叶氮含量
              yield_per_unit_area: 单位面积产量
              photosynthetically_active_radiation: 光合有效辐射
              evapotranspiration: 蒸腾作用
              germination_rate: 发芽率
              effective_tillering: 有效分蘖
        """
        self._tiffile = tiffile
       
        # 从tif文件读取中心坐标
        self.longitude, self.latitude = get_coordinates(tiffile)

        # 获取tif文件的geometry和crs
        self._geometry,self._crs = tif2geometry(tiffile)
        
        
        if acquired_time is not None:
            self.acquired_time = acquired_time
        else:
            self.acquired_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Setup output directories
        self._suffix = self.acquired_time.replace(":", "").replace(" ", "_")
        self.inversion_topics_dict = copy.deepcopy(INVERSION_TOPICS)
        self.detection_function = detection_function
        
        self.mask_dir = os.path.join(savepath, "mask")
        self.mask_file = os.path.join(self.mask_dir, f"mask-{self._suffix}.tif")
        
        self.shp_dir = os.path.join(savepath, "shps")
        self.weather_dir = os.path.join(savepath, "weather")
        self.reclassify_file = os.path.join(savepath, f"reclassify-{self._suffix}.tif")
        self.valued_dir = os.path.join(savepath, "valued")
        self.geojson_dir = os.path.join(savepath, "geojson")
        self.thumbnail_dir = os.path.join(savepath, "thumbnail")

    def run(self) -> bool:
        # try:
            self.has_valid_fields = self.do_mask()
            print(f"Run方法中 - 有效地块面积比例是否大于阈值: {self.has_valid_fields}")
            self.inverse_sign = self.inverse_sign_generation()

            self.do_inverse()

            shpvaluedGeoJson(
                self.shp_dir,
                self.valued_dir,
                self.geojson_dir,
                self.thumbnail_dir,
                geometry=self._geometry,
                acquired_time=self.acquired_time,
            )

        # except Exception as e:
        #     logging.error(str(e))
        #     return False
        # return True

    def inverse_sign_generation(self):
        """生成判断目前专题是否适宜进行反演的sign_dict"""
        # 获取当前时间
        # current_date = datetime.strptime(self.task_create_time, '%Y-%m-%d').date()
        current_date = datetime.strptime(self.acquired_time, "%Y-%m-%d %H:%M:%S")

        # 循环遍历所有专题
        for topic, info in self.inversion_topics_dict.items():
            # 判断时间在2.1到11.30 之间
            if current_date.month >= 2 and current_date.month <= 11:
                    self.inversion_topics_dict[topic]["invertible"] = True
            else:
                self.inversion_topics_dict[topic]["invertible"] = False

        # 1. 获取当前需要进行反演的专题；self.
        # 2. 获取当前shp的中心点；self.longitude 以及 self.latitude

        # 3. 循环判断当前shp的中心点，是否每个专题可以反演；要内置一个shp；判断处于哪个省；
        # CHN_adm1_shp_path = r"D://cropmirror//bytev//src//core//process//data//boundary//CHN_adm1.shp"

        # 目前是任何一个省，都不做限制

        # 4. 循环判断当前时间，是否每个专题可以反演；根据 self.task_create_time

        # 只有 2.1 - 11.30 期间，才可以进行专题反演；

        # 5. 返回一个 inverse_sign 的 dict；

    def do_mask(self):
        """生成掩膜文件"""
        if not os.path.exists(self.mask_dir):
            os.makedirs(self.mask_dir)
        self.has_valid_fields = gener_mask(self._tiffile, self.mask_file, self._geometry)
        return self.has_valid_fields

    def do_weather(self):
        """Process weather data using IDW interpolation.
        
        Note: This method requires Weather class which should be imported separately.
        """
        if not os.path.exists(self.weather_dir):
            os.makedirs(self.weather_dir, exist_ok=True)
        
        # Weather class should be imported from external weather module
        try:
            from src.weather.weather import Weather
            weather = Weather()
            weather_data = weather.get_data_by_point(
                latitude=self.latitude, longitude=self.longitude
            )
        except ImportError:
            logging.warning("Weather module not available, skipping weather data processing")
            return
        
        if not weather_data:
            logging.warning("No weather data available")
            return
        
        do_idw(
                lon=weather_data["longitude"],
                lat=weather_data["latitude"],
                sum_tem=weather_data["tem_sum"],
                sum_rain=weather_data["rain_sum"],
                qiwen=weather_data["tem"],
                savepath=self.weather_dir,
                tif=self._tiffile,
                suffix=self._suffix,
            )

    def do_inverse(self):
        """反演指标"""
        if not os.path.exists(self.weather_dir):
            os.makedirs(self.weather_dir, exist_ok=True)
        if not os.path.exists(self.shp_dir):
            os.makedirs(self.shp_dir)
        # 根据has_valid_fields决定是否进行聚类
        return inverse(
            imgf=self._tiffile,
            mask=self.mask_file,
            weatherpath=self.weather_dir,
            savepath=self.shp_dir,
            suffix=self._suffix,
            do_clustering=self.has_valid_fields,  # 传递是否进行聚类的标志
            do_invertion=self.inversion_topics_dict,  # 传递是否进行反演的标志
            detection_function=self.detection_function # 是否进行检测
        )
    


# ManifestFile and MetadataFile have been moved to planet_preprocessor.py

__filemeta = {
    "path": "PSScene/20240909_021318_75_24ee_3B_AnalyticMS_SR_8b_clip.tif",
    "media_type": "image/tiff",
    "size": 83470,
    "digests": {
        "md5": "889710783e3d9cb23da30a66b0169ca4",
        "sha256": "05f234406c8bb97df3ad364a2ec72db34af1e018c278d1af0423ead7a5138384",
    },
    "annotations": {
        "planet/asset_type": "ortho_analytic_8b_sr",
        "planet/bundle_type": "analytic_8b_sr_udm2",
        "planet/item_id": "20240909_021318_75_24ee",
        "planet/item_type": "PSScene",
    },
}



if __name__ == "__main__":
    # Example usage for direct execution
    print("Remote Sensing Processor - Direct Execution Example")
    print("=" * 50)
    
    # Check if test data exists
    # test_zip = "E:\\GitHub\\cropmirror\\cropmirror-utils\\src\\test\\planet\\1917043877528084482_psscene_ortho_analytic_8b_sr.zip"
    test_zip = "E:\\GitHub\\cropmirror\\cropmirror-utils\\src\\test\\planet\\1916003270454067201_psscene_ortho_analytic_8b_sr.zip"
    
    if os.path.exists(test_zip):

        # Step 1: Preprocess Planet image
        print("Step 1: Preprocessing Planet image...")
        preprocessor = PlanetPreprocessor(test_zip)
        tiffile, geometry, properties = preprocessor.process()
        print(f"  ✓ Extracted TIF file: {tiffile}")
        
        # Step 2: Process remote sensing data
        print("Step 2: Processing remote sensing data...")
        processor = RemoteSensingProcessor(
            tiffile=tiffile,
            savepath="output/",
            acquired_time= datetime.strptime(properties["acquired"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
            )
        processor.run()
    else:
        print(f"Test data not found: {test_zip}")
        print("Please provide a valid Planet zip file path.")
        print("\nUsage example:")
        print("  python pipeline.py")
        print("  # Or import and use:")
        print("  from remote_sensing.pipeline import RemoteSensingProcessor")
