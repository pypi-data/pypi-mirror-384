"""Planet API constants and configuration."""

# API Base URLs
BASE_URL = "https://api.planet.com/data/v1"
ORDERS_URL = "https://api.planet.com/compute/ops/orders/v2"
STATS_URL = "https://api.planet.com/compute/ops/stats/orders/v2"

# API Endpoints
QUICK_SEARCH_ENDPOINT = "quick-search"
QUICK_SEARCH_URL = f"{BASE_URL}/{QUICK_SEARCH_ENDPOINT}?_page_size=10&_sort=acquired+desc"

# Order States
ORDER_STATE_QUEUED = "queued"
ORDER_STATE_RUNNING = "running"
ORDER_STATE_SUCCESS = "success"
ORDER_STATE_FAILED = "failed"
ORDER_STATE_PARTIAL = "partial"
ORDER_STATE_CANCELLED = "cancelled"

# Order Status (Database)
ORDER_STATUS_REQUEST = "request"
ORDER_STATUS_DOWNLOAD = "download"
ORDER_STATUS_DONE = "done"

# Product Types
ITEM_TYPE_PSSCENE = "PSScene"
ITEM_TYPE_SKYSAT = "SkySatCollect"

# Product Bundles
PRODUCT_BUNDLE_4B = "analytic_4b_sr_udm2"
PRODUCT_BUNDLE_8B = "analytic_8b_sr_udm2"

# Asset Types
ASSET_ORTHO_ANALYTIC_8B_SR = "ortho_analytic_8b_sr"
ASSET_ORTHO_ANALYTIC_4B_SR = "ortho_analytic_4b_sr"

# Search Parameters
DEFAULT_PAGE_SIZE = 10
DEFAULT_CLOUD_COVER_MIN = 0
DEFAULT_CLOUD_COVER_MAX = 0.1

# Download Settings
DOWNLOAD_CHUNK_SIZE = 1024 * 10  # 10KB
DOWNLOAD_TIMEOUT = 300  # 5 minutes

DISTANCE_METERS = 1000 # 1km 边长/直径   1km2 == 1500亩