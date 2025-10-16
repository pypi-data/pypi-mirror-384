# Cropmirror Utils

云稷基础算法库 - 农业遥感处理的专业 Python 库

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## 📦 安装

```bash
pip install cropmirror
```

或从源码安装：

```bash
git clone https://github.com/cropmirror/cropmirror-utils.git
cd cropmirror-utils
pip install -e .
```

## 🌟 功能特性

- 🛰️ **遥感影像处理**: 支持 Planet, Sentinel, Landsat 等多种卫星数据
- 📊 **多指标计算**: NDVI, NDDI, NDNI, FPAR, ET, FVC, 产量预测等
- 🗺️ **智能分割**: 自动识别地块、道路和田埂
- 🎯 **精准农业**: 灌溉和施肥优先级计算
- 🌡️ **天气集成**: 气象数据 IDW 插值
- 📈 **可视化**: 丰富的数据可视化工具
- 🔄 **格式转换**: GeoTIFF, Shapefile, GeoJSON 互转

## 🚀 快速开始

### 处理 Planet 卫星影像

```python
from cropmirror.remote_sensing import preprocess_planet_image, RemoteSensingProcessor

# 1. 预处理 Planet 影像
tiffile, geometry, properties = preprocess_planet_image("satellite_image.zip")

# 2. 处理遥感数据
processor = RemoteSensingProcessor(
    tiffile=tiffile,
    savepath="output/",
    latitude=37.7749,
    longitude=-122.4194,
    task_create_time="2024-01-01 12:00:00",
    geometry=geometry,
    properties=properties
)

# 3. 运行处理
success = processor.run()
```

### 计算植被指数

```python
from cropmirror.remote_sensing import read_tiff, calculate_ndvi

# 读取影像
data, width, height, geotrans, proj = read_tiff("image.tif")

# 计算 NDVI
red_band = data[5, :, :]
nir_band = data[7, :, :]
ndvi = calculate_ndvi(red_band, nir_band)
```

### 使用 Planet API

```python
from cropmirror.planet import create_session, quick_search, create_order

# 创建会话
session = create_session(api_key="your_api_key")

# 搜索影像
geometry = {"type": "Polygon", "coordinates": [...]}
scene_ids = quick_search(session, geometry, "2024-01-01T00:00:00Z")

# 创建订单
order = create_order(session, scene_ids, geometry, "my_order")
```

## 📚 模块说明

### remote_sensing 模块

农业卫星遥感影像处理的核心模块，是遥感数据处理的主入口。

- **主要类**: `RemoteSensingProcessor`, `PlanetPreprocessor`, `AgricultureProcessor`
- **功能**: 多指标计算、智能聚类、地块分割、掩膜生成
- **文档**: [详细文档](src/remote_sensing/README.md)

### planet 模块

Planet 卫星影像 API 集成。

- **功能**: 影像搜索、订单创建、自动下载
- **文档**: [详细文档](src/planet/README.md)

### ndvi 模块

NDVI 计算和处方图生成。

- **功能**: 灌溉处方图、施肥处方图、喷药处方图
- **文档**: [详细文档](src/ndvi/README.md)

### utils 模块

通用 GIS 工具函数。

- **功能**: GeoJSON 转换、Shapefile 处理、坐标转换

## 📖 文档

### 快速开始

- **[快速参考](QUICK_REFERENCE.md)** - 5分钟快速上手 ⚡
- **[完整使用指南](docs/LIBRARY_USAGE.md)** - 详细教程 📚
- **[文档索引](INDEX.md)** - 所有文档导航 🗂️
- **[项目状态](PROJECT_STATUS.md)** - 项目状态报告 📊

### API 文档

- **[Remote Sensing 模块](src/remote_sensing/README.md)** - 遥感处理核心
- **[Planet 模块](src/planet/README.md)** - Planet API 集成
- **[NDVI 模块](src/ndvi/README.md)** - NDVI 分析

### 迁移和技术

- **[迁移指南](docs/MIGRATION_GUIDE.md)** - 从旧版本迁移
- **[架构改进](docs/ARCHITECTURE_IMPROVEMENTS.md)** - 设计说明
- **[优化报告](docs/COMPLETE_OPTIMIZATION_REPORT.md)** - 完整报告

## 💡 使用示例

查看 [examples/](examples/) 目录获取完整示例：

```bash
# 运行遥感处理示例
python examples/remote_sensing_example.py 1

# 运行 Planet 预处理演示
python examples/planet_preprocessing_demo.py 2
```

## 🔧 依赖项

主要依赖：

- GDAL >= 3.0
- NumPy >= 2.1.0
- SciPy >= 1.15.2
- scikit-learn >= 1.7.0
- scikit-image >= 0.24.0
- Rasterio >= 1.4.3
- GeoPandas >= 1.0.1

完整依赖列表见 [pyproject.toml](pyproject.toml)

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest src/test/ndvi/

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 🤝 贡献

欢迎贡献！请：

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

- Long.liu
- Wenchang

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/cropmirror/cropmirror-utils/issues)
- **Email**: support@cropmirror.com

## 🔗 相关链接

- [GitHub 仓库](https://github.com/cropmirror/cropmirror-utils)
- [问题跟踪](https://github.com/cropmirror/cropmirror-utils/issues)
- [更新日志](CHANGELOG.md)

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个 Star！

---

**当前版本**: v0.0.10  
**最后更新**: 2024-10-15
