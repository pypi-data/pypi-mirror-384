# Remote Sensing Module - Agricultural Satellite Image Processing

农业卫星遥感影像处理模块，提供完整的遥感数据处理和农业指标提取功能。

## 🌟 功能特性

该模块是处理遥感数据的主入口，支持多种遥感监测内容：

- **多源遥感支持**: Planet, Sentinel, Landsat 等多种卫星数据
- **多指标计算**: NDVI, NDDI, NDNI, FPAR, ET, FVC 等农业指标
- **智能聚类**: 基于 KMeans 的数据聚类和分割
- **地块分割**: 自动识别道路和田埂，分割农田地块
- **掩膜生成**: 自动生成道路、建筑物和农田掩膜
- **天气数据处理**: IDW 插值处理气象数据
- **结果可视化**: 丰富的可视化工具
- **Shapefile 生成**: 自动生成带属性的 Shapefile

## 📂 模块结构

```
remote_sensing/
├── __init__.py              # 模块入口和 API 导出
├── constants.py             # 常量和配置
├── io.py                    # 文件读写操作
├── indicators.py            # 农业指标计算
├── clustering.py            # 聚类和分割算法
├── visualization.py         # 可视化工具
├── processor.py             # 主处理器（AgricultureProcessor）
├── pipeline.py              # 高层流水线（RemoteSensingProcessor）
├── masking.py               # 掩膜生成
├── idw.py                   # IDW 插值
├── shapefile_processor.py   # Shapefile 处理
└── README.md                # 本文档

Note: PlanetPreprocessor 已移至 planet 模块（从 remote_sensing 仍可导入）
```

## 🚀 快速开始

### 1. 处理 Planet 影像（推荐方式）

使用 `PlanetPreprocessor` 先提取数据，再用 `RemoteSensingProcessor` 处理：

```python
# 方式 1: 从 planet 模块导入（推荐）
from cropmirror.planet import PlanetPreprocessor
from cropmirror.remote_sensing import RemoteSensingProcessor

# 方式 2: 从 remote_sensing 模块导入（便捷，重新导出）
from cropmirror.remote_sensing import PlanetPreprocessor, RemoteSensingProcessor

# 步骤 1: 预处理 Planet 影像
preprocessor = PlanetPreprocessor("path/to/planet_image.zip")
tiffile, geometry, properties = preprocessor.process()

# 步骤 2: 处理遥感数据
processor = RemoteSensingProcessor(
    tiffile=tiffile,
    savepath="path/to/output/",
    latitude=37.7749,
    longitude=-122.4194,
    task_create_time="2024-01-01 12:00:00",
    geometry=geometry,
    properties=properties,
    plot=None  # 可选: GeoJSON 格式的地块边界
)

# 运行完整处理流程
success = processor.run()
```

### 1b. 使用便捷函数（快捷方式）

```python
from cropmirror.remote_sensing import preprocess_planet_image, RemoteSensingProcessor

# 快速预处理
tiffile, geometry, properties = preprocess_planet_image("planet_image.zip")

# 处理遥感数据
processor = RemoteSensingProcessor(
    tiffile=tiffile,
    savepath="path/to/output/",
    latitude=37.7749,
    longitude=-122.4194,
    task_create_time="2024-01-01 12:00:00",
    geometry=geometry,
    properties=properties
)
success = processor.run()
```

### 2. 中层 API - AgricultureProcessor

适用于已有 GeoTIFF 文件的处理：

```python
from cropmirror.remote_sensing import AgricultureProcessor

# 初始化处理器
processor = AgricultureProcessor(
    imgf="path/to/image.tif",
    mask="path/to/mask.tif",
    weatherpath="path/to/weather/"
)

# 配置反演参数
do_invertion = {
    'NDVI': {'invertible': True},
    'NDDI': {'invertible': True},
    'NDNI': {'invertible': True},
    'Yield': {'invertible': True},
    'FPAR': {'invertible': True},
    'ET': {'invertible': True},
    'FVC': {'invertible': True},
    'Tillering': {'invertible': True},
    'Irrigation': {'invertible': True},
    'Fertilization': {'invertible': True},
}

# 执行反演
results = processor.inverse(
    savepath="path/to/output/",
    suffix="20240101",
    do_clustering=True,
    do_invertion=do_invertion,
    detection_function=None  # None = 处理所有指标
)
```

### 3. 低层 API - 单个功能

```python
from cropmirror.remote_sensing import (
    read_tiff,
    calculate_ndvi,
    cal_nddi,
    cluster_data,
    save_tiff,
    gener_mask
)

# 读取影像
data, width, height, geotrans, proj = read_tiff("image.tif")

# 计算 NDVI
red_band = data[5, :, :]
nir_band = data[7, :, :]
ndvi = calculate_ndvi(red_band, nir_band)

# 聚类处理
from cropmirror.remote_sensing import ClusterMode
ndvi_clustered = cluster_data(ndvi, n_clusters=6, mode=ClusterMode.PRESERVE_ZERO)

# 保存结果
save_tiff(
    "output.tif", "output.shp",
    width, height, geotrans, proj,
    ndvi_clustered, mask,
    do_clustering=True
)
```

## 📊 支持的遥感监测内容

### 植被指数

- **NDVI (Normalized Difference Vegetation Index)**: 归一化植被指数，反映植被生长状况
- **NDDI (Normalized Difference Drought Index)**: 归一化干旱指数，反映水分状况
- **NDNI**: 叶氮含量指数，反映氮营养状况

### 生理参数

- **FPAR (Fraction of Photosynthetically Active Radiation)**: 光合有效辐射吸收比例
- **ET (Evapotranspiration)**: 蒸散量，单位 mm/day
- **FVC (Fractional Vegetation Cover)**: 植被覆盖度/出苗率

### 农艺参数

- **Yield**: 单位面积产量预测
- **Tillering**: 有效分蘖数
- **Irrigation Order**: 灌溉优先级 (1-10)
- **Fertilization Order**: 施肥优先级 (1-10)

### 气象参数

- **Air Temperature**: 气温
- **Accumulated Rainfall**: 累计降水量
- **Accumulated Temperature**: 积温

## 🎯 使用场景

### 场景 1: 多光谱卫星影像处理

```python
from cropmirror.remote_sensing import RemoteSensingProcessor

# 处理 Planet PSScene 8波段影像
processor = RemoteSensingProcessor(
    zipfile="planet_psscene.zip",
    savepath="results/",
    latitude=39.456,
    longitude=116.123,
    task_create_time="2024-03-15 12:00:00"
)
processor.run()
```

### 场景 2: 作物长势监测

```python
from cropmirror.remote_sensing import AgricultureProcessor

processor = AgricultureProcessor(
    imgf="sentinel2_image.tif",
    mask="field_mask.tif",
    weatherpath="weather_data/"
)

# 只监测植被相关指标
detection_function = [
    "vigor_level",
    "drought_level",
    "leaf_nitrogen_content"
]

results = processor.inverse(
    savepath="monitoring/",
    suffix="20240315",
    detection_function=detection_function
)
```

### 场景 3: 精准农业管理

```python
from cropmirror.remote_sensing import RemoteSensingProcessor

# 处理影像并生成管理建议
processor = RemoteSensingProcessor(
    zipfile="field_image.zip",
    savepath="management/",
    latitude=39.456,
    longitude=116.123,
    task_create_time="2024-03-15 12:00:00"
)
processor.run()

# 结果包括：
# - 灌溉优先级图
# - 施肥优先级图
# - 产量预测图
```

## 🔧 配置选项

### 聚类模式

```python
from cropmirror.remote_sensing import ClusterMode

# DEFAULT: 默认处理
# PRESERVE_ZERO: 保持零值不聚类
# NDNI_SPECIAL: NDNI 特殊处理（过滤 >4 的异常值）

data_clustered = cluster_data(data, mode=ClusterMode.PRESERVE_ZERO)
```

### 反演控制

```python
do_invertion = {
    "NDVI": {
        "description": "植被长势",
        "mode": "PRESERVE_ZERO",
        "invertible": True  # 设置为 False 将跳过此指标
    },
    "NDDI": {
        "description": "干旱指数",
        "mode": "PRESERVE_ZERO",
        "invertible": True
    },
    # ... 其他指标
}

processor.inverse(
    savepath="output/",
    suffix="20240101",
    do_invertion=do_invertion
)
```

### 输出控制

```python
# 只处理特定监测内容
detection_function = [
    "vigor_level",          # NDVI
    "drought_level",        # NDDI
    "irrigation_order",     # 灌溉优先级
]

processor.inverse(
    savepath="output/",
    suffix="20240101",
    detection_function=detection_function
)
```

## 📤 输出文件

### GeoTIFF 文件

每个指标会生成一个 GeoTIFF 文件：

- `vigor_level-{suffix}.tif` - 植被长势
- `drought_level-{suffix}.tif` - 干旱指数
- `leaf_nitrogen_content-{suffix}.tif` - 叶氮含量
- `yield_per_unit_area-{suffix}.tif` - 单位面积产量
- `irrigation_order-{suffix}.tif` - 灌溉优先级
- `fertilization_order-{suffix}.tif` - 施肥优先级
- 等等...

### Shapefile 文件

每个指标会生成对应的 Shapefile，包含以下属性：

- `value`: 指标的原始值
- `level`: 等级 (1-N)
- `crop_type`: 作物类型
- `date`: 采集日期
- `Shape_Area`: 面积
- `Shape_Leng`: 周长

### 目录结构

```
output/
├── mask/
│   └── mask-{suffix}.tif
├── shps/
│   ├── vigor_level-{suffix}.tif
│   ├── vigor_level-{suffix}.shp
│   └── ...
├── valued/
│   └── vigor_level-{suffix}.shp
├── geojson/
│   └── vigor_level-{suffix}.geojson
├── thumbnail/
│   └── vigor_level-{suffix}.webp
└── weather/
    ├── air_temperature-{suffix}.tif
    └── ...
```

## ⚙️ 高级功能

### 自定义地块边界

```python
import json

# 准备地块数据（GeoJSON 格式）
plot_data = [
    {
        "positions": [
            [116.123, 39.456, 0],
            [116.124, 39.456, 0],
            [116.124, 39.457, 0],
            [116.123, 39.457, 0],
            [116.123, 39.456, 0],
        ]
    }
]

processor = RemoteSensingProcessor(
    zipfile="image.zip",
    savepath="output/",
    latitude=39.456,
    longitude=116.123,
    task_create_time="2024-01-01 12:00:00",
    plot=json.dumps(plot_data)
)
```

### 天气数据集成

```python
from cropmirror.remote_sensing import do_idw

# 气象站数据
lon = [116.1, 116.2, 116.3]
lat = [39.4, 39.5, 39.6]
sum_tem = [1000, 1050, 1100]      # 积温
sum_rain = [50, 55, 60]           # 积雨
qiwen = [20, 21, 22]              # 气温

# 执行 IDW 插值
do_idw(
    lon=lon,
    lat=lat,
    sum_tem=sum_tem,
    sum_rain=sum_rain,
    qiwen=qiwen,
    savepath="weather/",
    tif="reference.tif",
    suffix="20240101"
)
```

### 可视化结果

```python
from cropmirror.remote_sensing import display_results_group

# 准备结果字典
results = {
    'NDVI': (ndvi_array, '植被长势'),
    'NDDI': (nddi_array, '干旱指数'),
    'NDNI': (ndni_array, '叶氮含量'),
}

# 显示
display_results_group(
    results,
    window_title="遥感监测结果",
    ncols=3
)
```

## 📝 注意事项

1. **输入数据要求**:
   - 影像格式: GeoTIFF, 支持 4/8 波段多光谱影像
   - 坐标系统: UTM 投影（推荐）
   - 波段顺序: PSScene 8波段或标准 RGB+NIR

2. **内存占用**:
   - 大影像处理需要较多内存
   - 建议使用分块处理大数据

3. **聚类参数**:
   - `do_clustering=False` 适用于积雪覆盖等特殊情况
   - 聚类数量默认为 6，可通过常量配置调整

4. **时间限制**:
   - 反演功能默认限制在 2 月 1 日至 11 月 30 日期间

## 🔗 相关模块

- **planet**: Planet 卫星影像 API 集成
- **ndvi**: NDVI 处方图生成
- **utils**: GIS 工具函数
- **vigorroot**: 根系活力分析

## 📚 参考文档

- [完整使用指南](../../LIBRARY_USAGE.md)
- [使用示例](../../examples/remote_sensing_example.py)
- [API 文档](https://docs.cropmirror.com)

## 💡 向后兼容

为了兼容旧代码，模块保留了 `MainProcess` 别名：

```python
from cropmirror.remote_sensing import MainProcess  # 等同于 RemoteSensingProcessor
```

## 📄 许可证

MIT License

## 👥 贡献者

- Long.liu
- Wenchang

