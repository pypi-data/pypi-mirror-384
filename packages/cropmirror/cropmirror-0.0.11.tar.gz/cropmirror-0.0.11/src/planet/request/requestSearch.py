"""Planet Search API request payload generator."""
import datetime
from typing import Dict, Any


def generate_search_requst(geometry: Dict[str, Any],
                           endtime: str = None) -> Dict[str, Any]:
    """Generate Planet quick search request payload.
    
    Args:
        geometry: GeoJSON geometry to search within.
        endtime: End time for acquisition date filter (ISO 8601 format).
                If None, defaults to current time.
        
    Returns:
        Search request payload dictionary.
    """
    if endtime is None:
        endtime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "filter": {
            "type": "AndFilter",
            "config": [
                {
                    "type": "OrFilter",
                    "config": [
                        {
                            "type": "AndFilter",
                            "config": [
                                {
                                    "type": "AndFilter",
                                    "config": [
                                        {
                                            "type": "StringInFilter",
                                            "field_name": "item_type",
                                            "config": ["PSScene"],
                                        },
                                        {
                                            "type": "AndFilter",
                                            "config": [
                                                {
                                                    "type": "AssetFilter",
                                                    "config": ["ortho_analytic_8b_sr"],
                                                }
                                            ],
                                        },
                                    ],
                                },
                                {
                                    "type": "RangeFilter",
                                    "config": {"gte": 0, "lte": 0.1},
                                    "field_name": "cloud_cover",
                                },
                                {
                                    "type": "StringInFilter",
                                    "field_name": "publishing_stage",
                                    "config": ["standard", "finalized"],
                                },
                            ],
                        },
                        {
                            "type": "AndFilter",
                            "config": [
                                {
                                    "type": "StringInFilter",
                                    "field_name": "item_type",
                                    "config": ["SkySatCollect"],
                                },
                                {
                                    "type": "RangeFilter",
                                    "config": {"gte": 0, "lte": 0.1},
                                    "field_name": "cloud_cover",
                                },
                            ],
                        },
                    ],
                },
                {"type": "PermissionFilter", "config": ["assets:download"]},
                {
                    "type": "OrFilter",
                    "config": [
                        {
                            "type": "DateRangeFilter",
                            "field_name": "acquired",
                            "config": {"lte": endtime}
                        }
                    ]
                }
            ],
        },
        "item_types": ["PSScene", "SkySatCollect"],
        "geometry": geometry
    }
