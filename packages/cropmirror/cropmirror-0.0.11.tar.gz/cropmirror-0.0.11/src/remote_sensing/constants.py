"""Constants and configuration for process module."""
from enum import Enum


class ClusterMode(Enum):
    """Clustering mode for data processing."""
    DEFAULT = 0          # Default processing
    PRESERVE_ZERO = 1    # Preserve zero values
    NDNI_SPECIAL = 2     # Special processing for NDNI


# Band indices for PSScene 8-band imagery
BAND_COASTAL = 0
BAND_BLUE = 1
BAND_GREEN_I = 2
BAND_GREEN = 3
BAND_YELLOW = 4
BAND_RED = 5
BAND_RED_EDGE = 6
BAND_NIR = 7

# Band names
BAND_NAMES = ['Coastal', 'Blue', 'Green1', 'Green', 'Yellow', 'Red', 'RedEdge', 'NIR']

# NDVI thresholds
NDVI_LOW_THRESHOLD = 0.15   # Lower threshold for initial growth detection
NDVI_HIGH_THRESHOLD = 0.3   # Higher threshold for healthy growth
NDVI_MIN_VALUE = 0.2        # Minimum NDVI for FVC calculation
NDVI_MAX_VALUE = 0.98       # Maximum NDVI for FVC calculation

# Cloud cover thresholds
CLOUD_COVER_MAX = 0.1

# Clustering parameters
DEFAULT_N_CLUSTERS = 6
MIN_REGION_SIZE = 2000      # Minimum region size for segmentation
MIN_AREA_RATIO = 0.01       # Minimum area ratio for clustering

# Temperature and precipitation parameters
BASE_TEMPERATURE = 17.22    # Base temperature for accumulated temperature
PRECIPITATION_FACTOR = 25.4  # Factor to convert precipitation units

# ET calculation parameters
PRIESTLEY_TAYLOR_ALPHA = 1.26
NET_RADIATION = 15          # MJ/m²/day
SOIL_HEAT_FLUX = 2          # MJ/m²/day
ET_MAX = 8                  # Maximum ET in mm/day

# Yield calculation parameters
YIELD_MAX = 120000          # Maximum yield
YIELD_COEFFICIENTS = {
    'a': 150000,
    'b': -180000,
    'c': 120000,
    'd': -5000
}

# Inversion topics configuration
INVERSION_TOPICS = {
    "NDVI": {
        "description": "植被长势",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "NDDI": {
        "description": "干旱指数",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "NDNI": {
        "description": "叶氮含量",
        "mode": "NDNI_SPECIAL",
        "invertible": False,
    },
    "Yield": {
        "description": "单位面积产量",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "FPAR": {
        "description": "光合有效辐射",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "ET": {
        "description": "蒸散量",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "FVC": {
        "description": "出苗率",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "Tillering": {
        "description": "有效分蘖",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "Irrigation": {
        "description": "灌溉优先级",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "Fertilization": {
        "description": "施肥优先级",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "AirTemperature": {
        "description": "气温",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "AccumulatedRainfall": {
        "description": "累计降水量",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
    "AccumulatedTemperature": {
        "description": "累计温度",
        "mode": "PRESERVE_ZERO",
        "invertible": False,
    },
}

# Crop types for shapefile attributes
CROP_FILES = [
    "vigor_level",
    "drought_level",
    "leaf_nitrogen_content",
    "evapotranspiration",
    "photosynthetically_active_radiation",
    "yield_per_unit_area",
    "germination_rate",
    "effective_tillering",
]

# Color mappings for visualization
VIGOR_LEVEL_COLORS = {
    1: (3, 103, 36),      # 长势极好
    2: (115, 204, 20),    # 长势良好
    3: (221, 247, 8),     # 长势中等
    4: (225, 165, 21),    # 长势较差
    5: (178, 28, 9),      # 长势极差
}

DROUGHT_LEVEL_COLORS = {
    1: (27, 63, 102),     # 中度湿润
    2: (9, 87, 177),      # 水淹湿润
    3: (37, 198, 80),     # 轻度湿润
    4: (241, 241, 80),    # 轻度干旱
    5: (241, 190, 30),    # 中度干旱
    6: (241, 241, 80),    # 重度干旱
}

