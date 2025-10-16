"""Planet Order API request payload generator."""
from typing import List, Dict, Any


def generate_order_request(name: str, ids: List[str], geometry: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Planet order request payload.
    
    Args:
        name: Order name.
        ids: List of scene IDs to order.
        geometry: GeoJSON geometry for clipping AOI.
        
    Returns:
        Order request payload dictionary.
    """
    data = {
        "name": name,
        "products": [
            {
                "item_ids": ids,
                "item_type": "PSScene",
                "product_bundle": "analytic_8b_sr_udm2",
            }
        ],
        "delivery": {
            "archive_filename": f"{name}_psscene_ortho_analytic_8b_sr.zip",
            "archive_type": "zip",
            "single_archive": True,
        },
        "tools": [{"clip": {"aoi": geometry}}],
        "notifications": {"email": True},
        "metadata": {"stac": {}},
        "order_type": "partial",
    }
    return data


# Example response template for reference
_response_template = {
    "_links": {
        "_self": "https://api.planet.com/compute/ops/orders/v2/a5527505-dcc9-414c-a384-441f0db9215e"
    },
    "created_on": "2024-08-27T02:25:11.330Z",
    "delivery": {
        "archive_filename": "cwc order_psscene_analytic_sr_udm2.zip",
        "archive_type": "zip",
        "single_archive": True,
    },
    "error_hints": [],
    "id": "a5527505-dcc9-414c-a384-441f0db9215e",
    "last_message": "Preparing order",
    "last_modified": "2024-08-27T02:25:11.330Z",
    "metadata": {"stac": {}},
    "name": "cwc order",
    "notifications": {"email": True},
    "order_type": "partial",
    "products": [
        {
            "item_ids": ["20240823_030536_66_24ee"],
            "item_type": "PSScene",
            "product_bundle": "analytic_sr_udm2",
        }
    ],
    "state": "queued",
    "tools": [
        {
            "clip": {
                "aoi": {
                    "coordinates": [
                        [
                            [116.87070482466851, 37.23955],
                            [116.87070481885698, 37.23886830763092],
                            # ... truncated for brevity
                            [116.87070482466851, 37.23955],
                        ]
                    ],
                    "type": "Polygon",
                }
            }
        }
    ],
}
