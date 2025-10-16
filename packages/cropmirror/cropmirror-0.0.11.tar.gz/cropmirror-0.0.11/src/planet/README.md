# Planet API Integration Module

Planet 卫星影像 API 集成模块，提供搜索、订购、下载卫星影像以及预处理 Planet 影像 zip 文件的功能。

## 模块结构

```
src/planet/
├── __init__.py              # 模块入口，导出主要 API
├── constants.py             # API 常量配置
├── planet_preprocessor.py   # Planet 影像预处理器（新增）
├── order.py                 # PlanetOrder 业务逻辑类
├── orderRequest.py          # API 客户端函数
├── planetMeta/              # API 响应数据模型
│   ├── __init__.py
│   ├── order.py            # 订单相关数据模型
│   └── search.py           # 搜索相关数据模型
└── request/                 # API 请求负载生成器
    ├── __init__.py
    ├── requestOrder.py     # 订单请求负载生成
    └── requestSearch.py    # 搜索请求负载生成
```

## 主要功能

### 1. PlanetPreprocessor 类（新增）

预处理 Planet 卫星影像 zip 文件。

```python
from cropmirror.planet import PlanetPreprocessor

# 初始化预处理器
preprocessor = PlanetPreprocessor("planet_image.zip")

# 处理 zip 文件，提取 GeoTIFF 和元数据
tiffile, geometry, properties = preprocessor.process()

# 获取详细信息
image_info = preprocessor.get_image_info()
print(f"Image size: {image_info['width']}x{image_info['height']}")
print(f"Bands: {image_info['bands']}")
```

或使用便捷函数：

```python
from cropmirror.planet import preprocess_planet_image

# 一步完成预处理
tiffile, geometry, properties = preprocess_planet_image("planet_image.zip")
```

### 2. PlanetOrder 类

高层业务逻辑类，管理特定位置的卫星影像订单。

```python
from core.planet import PlanetOrder

order_manager = PlanetOrder(
    session=db_session,
    device_id="device_001",
    latitude=37.7749,
    longitude=-122.4194,
    endtime="2024-10-01 00:00:00"
)

# 请求订单
order_id = order_manager.request_order()

# 下载订单
success = order_manager.download_order("/path/to/save")

# 关闭会话
order_manager.close()
```

### 2. API 客户端函数

低层 API 客户端函数，提供直接的 API 访问。

```python
from core.planet import (
    create_session,
    quick_search,
    create_order,
    get_order,
    download_order_file
)

# 创建会话
session = create_session(api_key="your_api_key")

# 搜索场景
geometry = {"type": "Polygon", "coordinates": [...]}
scene_ids = quick_search(session, geometry, "2024-10-01T00:00:00Z")

# 创建订单
order = create_order(session, scene_ids, geometry, "order_name")

# 获取订单状态
order = get_order(session, order_id)

# 下载文件
download_order_file(session, "/path/to/file.zip", download_url)

session.close()
```

## 数据模型

### OrderDetail
订单详情模型，包含订单的完整信息。

**主要属性：**
- `id`: 订单 ID
- `name`: 订单名称
- `state`: 订单状态（queued/running/success/failed）
- `products`: 产品列表
- `_links`: 下载链接

### SearchResponse
搜索响应模型，包含匹配的场景信息。

**主要属性：**
- `features`: 场景列表
- `type`: FeatureCollection
- `_links`: 分页链接

## 配置常量

在 `constants.py` 中定义了所有 API 相关的常量：

- **API URLs**: BASE_URL, ORDERS_URL, STATS_URL
- **订单状态**: ORDER_STATE_SUCCESS, ORDER_STATE_FAILED 等
- **产品类型**: ITEM_TYPE_PSSCENE, ITEM_TYPE_SKYSAT
- **下载设置**: DOWNLOAD_CHUNK_SIZE, DOWNLOAD_TIMEOUT

## 代码优化亮点

### 1. **清晰的模块结构**
- 按功能分层：API 客户端、业务逻辑、数据模型、请求生成器
- 每个文件职责单一，易于维护

### 2. **完整的类型提示**
```python
def create_order(session: requests.Session, ids: List[str], 
                 geometry: dict, name: str) -> Optional[Order]:
    ...
```

### 3. **详细的文档字符串**
每个函数都有完整的 docstring，说明参数和返回值

### 4. **使用列表推导式**
```python
# 优化前
self.products = []
for p in products:
    self.products.append(Product(**p))

# 优化后
self.products = [Product(**p) for p in (products or [])]
```

### 5. **提取常量配置**
所有硬编码的 URL、超时时间等都提取到 `constants.py`

### 6. **改善错误处理**
```python
if res.status_code == 200:
    return Order(**res.json())
logging.error(f"Failed to get order {order_id}: {res.status_code}")
return None
```

### 7. **统一代码风格**
- 所有函数参数间都有空格
- 类之间有两个空行
- 移除了所有无用的 `pass` 语句
- 修复了拼写错误（`_premissions` → `_permissions`）

## 使用示例

### 完整工作流程

```python
from core.planet import PlanetOrder
from schema.base import SessionLocal

# 创建数据库会话
db_session = SessionLocal()

try:
    # 初始化订单管理器
    planet_order = PlanetOrder(
        session=db_session,
        device_id="test_device",
        latitude=37.7749,
        longitude=-122.4194,
        endtime="2024-10-15 00:00:00"
    )
    
    # 请求订单
    order_id = planet_order.request_order()
    if order_id:
        print(f"Order created: {order_id}")
        
        # 等待订单完成后下载
        success = planet_order.download_order("/data/satellite")
        if success:
            print("Download completed!")
    
finally:
    planet_order.close()
    db_session.close()
```

## 环境变量

- `PL_API_KEY`: Planet API 密钥

## 依赖

- `requests`: HTTP 客户端
- `shapely`: 几何计算
- `sqlalchemy`: 数据库操作
- `config`: 应用配置

## 版本历史

### v1.0.0 (2024-10-15)
- 完整的代码重构和优化
- 添加类型提示和文档
- 提取常量配置
- 改善代码组织和可维护性

