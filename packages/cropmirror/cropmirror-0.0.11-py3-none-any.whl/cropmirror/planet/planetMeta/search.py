class SearchResponse(object):
    def __init__(self, _links, features, type) -> None:
        self._links = _links
        self.features = [Feature(**v) for v in features]
        self.type = type


class Links(object):
    def __init__(self, _first, _next, _self) -> None:
        self._first = _first
        self._next = _next
        self._self = _self


class Feature(object):
    def __init__(self, _links, _permissions, assets, geometry, id, properties, type) -> None:
        self._links = _links
        self._permissions = _permissions
        self.assets = assets
        self.geometry = geometry
        self.id = id
        self.properties = Properties(**properties)
        self.type = type
    

class Properties(object):
    def __init__(self, acquired, anomalous_pixels, clear_confidence_percent, clear_percent,
                 cloud_cover, cloud_percent, ground_control, gsd, heavy_haze_percent, instrument,
                 item_type, light_haze_percent, pixel_resolution, provider, published, publishing_stage,
                 quality_category, satellite_azimuth, satellite_id, shadow_percent, snow_ice_percent,
                 strip_id, sun_azimuth, sun_elevation, updated, view_angle, visible_confidence_percent,
                 visible_percent) -> None:
        self.acquired = acquired
        self.anomalous_pixels = anomalous_pixels
        self.clear_confidence_percent = clear_confidence_percent
        self.clear_percent = clear_percent
        self.cloud_cover = cloud_cover
        self.cloud_percent = cloud_percent
        self.ground_control = ground_control
        self.gsd = gsd
        self.heavy_haze_percent = heavy_haze_percent
        self.instrument = instrument
        self.item_type = item_type
        self.light_haze_percent = light_haze_percent
        self.pixel_resolution = pixel_resolution
        self.provider = provider
        self.published = published
        self.publishing_stage = publishing_stage
        self.quality_category = quality_category
        self.satellite_azimuth = satellite_azimuth
        self.satellite_id = satellite_id
        self.shadow_percent = shadow_percent
        self.snow_ice_percent = snow_ice_percent
        self.strip_id = strip_id
        self.sun_azimuth = sun_azimuth
        self.sun_elevation = sun_elevation
        self.updated = updated
        self.view_angle = view_angle
        self.visible_confidence_percent = visible_confidence_percent
        self.visible_percent = visible_percent


__template = {
    "_links": {
        "_first": "https://api.planet.com/data/v1/searches/ed5cb39433d542a99020d7b206612244/results?_page=eyJwYWdlX3NpemUiOiAxLCAic29ydF9ieSI6ICJhY3F1aXJlZCIsICJzb3J0X2Rlc2MiOiB0cnVlLCAic29ydF9zdGFydCI6IG51bGwsICJzb3J0X2xhc3RfaWQiOiBudWxsLCAic29ydF9wcmV2IjogZmFsc2UsICJxdWVyeV9wYXJhbXMiOiB7Il9wYWdlX3NpemUiOiAiMSIsICJfc29ydCI6ICJhY3F1aXJlZCBkZXNjIn19",
        "_next": "https://api.planet.com/data/v1/searches/ed5cb39433d542a99020d7b206612244/results?_page=eyJwYWdlX3NpemUiOiAxLCAic29ydF9ieSI6ICJhY3F1aXJlZCIsICJzb3J0X2Rlc2MiOiB0cnVlLCAic29ydF9zdGFydCI6ICIyMDI0LTA4LTIzVDAzOjA1OjM5LjAzNTc0OFoiLCAic29ydF9sYXN0X2lkIjogIjIwMjQwODIzXzAzMDUzOV8wM18yNGVlIiwgInNvcnRfcHJldiI6IGZhbHNlLCAicXVlcnlfcGFyYW1zIjogeyJfcGFnZV9zaXplIjogIjEiLCAiX3NvcnQiOiAiYWNxdWlyZWQgZGVzYyJ9fQ%3D%3D",
        "_self": "https://api.planet.com/data/v1/searches/ed5cb39433d542a99020d7b206612244/results?_page=eyJwYWdlX3NpemUiOiAxLCAic29ydF9ieSI6ICJhY3F1aXJlZCIsICJzb3J0X2Rlc2MiOiB0cnVlLCAic29ydF9zdGFydCI6IG51bGwsICJzb3J0X2xhc3RfaWQiOiBudWxsLCAic29ydF9wcmV2IjogZmFsc2UsICJxdWVyeV9wYXJhbXMiOiB7Il9wYWdlX3NpemUiOiAiMSIsICJfc29ydCI6ICJhY3F1aXJlZCBkZXNjIn19"
    },
    "features": [
        {
            "_links": {
                "_self": "https://api.planet.com/data/v1/item-types/PSScene/items/20240823_030539_03_24ee",
                "assets": "https://api.planet.com/data/v1/item-types/PSScene/items/20240823_030539_03_24ee/assets/",
                "thumbnail": "https://tiles.planet.com/data/v1/item-types/PSScene/items/20240823_030539_03_24ee/thumb"
            },
            "_permissions": [
                "assets.basic_analytic_4b:download",
                "assets.basic_analytic_4b_rpc:download",
                "assets.basic_analytic_4b_xml:download",
                "assets.basic_analytic_8b:download",
                "assets.basic_analytic_8b_xml:download",
                "assets.basic_udm2:download",
                "assets.ortho_analytic_4b:download",
                "assets.ortho_analytic_4b_sr:download",
                "assets.ortho_analytic_4b_xml:download",
                "assets.ortho_analytic_8b:download",
                "assets.ortho_analytic_8b_sr:download",
                "assets.ortho_analytic_8b_xml:download",
                "assets.ortho_udm2:download",
                "assets.ortho_visual:download"
            ],
            "assets": [
                "basic_analytic_4b",
                "basic_analytic_4b_rpc",
                "basic_analytic_4b_xml",
                "basic_analytic_8b",
                "basic_analytic_8b_xml",
                "basic_udm2",
                "ortho_analytic_4b",
                "ortho_analytic_4b_sr",
                "ortho_analytic_4b_xml",
                "ortho_analytic_8b",
                "ortho_analytic_8b_sr",
                "ortho_analytic_8b_xml",
                "ortho_udm2",
                "ortho_visual"
            ],
            "geometry": {
                "coordinates": [
                    [
                        [
                            116.86979944505433,
                            37.223015045357265
                        ],
                        [
                            116.82117865788278,
                            37.04013951313693
                        ],
                        [
                            117.20263714124003,
                            36.97487704900282
                        ],
                        [
                            117.25194454628722,
                            37.15680881967846
                        ],
                        [
                            116.86979944505433,
                            37.223015045357265
                        ]
                    ]
                ],
                "type": "Polygon"
            },
            "id": "20240823_030539_03_24ee",
            "properties": {
                "acquired": "2024-08-23T03:05:39.035748Z",
                "anomalous_pixels": 0,
                "clear_confidence_percent": 95,
                "clear_percent": 97,
                "cloud_cover": 0.02,
                "cloud_percent": 2,
                "ground_control": True,
                "gsd": 3.9,
                "heavy_haze_percent": 0,
                "instrument": "PSB.SD",
                "item_type": "PSScene",
                "light_haze_percent": 1,
                "pixel_resolution": 3,
                "provider": "planetscope",
                "published": "2024-08-23T10:20:05Z",
                "publishing_stage": "finalized",
                "quality_category": "standard",
                "satellite_azimuth": 102.1,
                "satellite_id": "24ee",
                "shadow_percent": 1,
                "snow_ice_percent": 0,
                "strip_id": "7527050",
                "sun_azimuth": 145.1,
                "sun_elevation": 60.1,
                "updated": "2024-08-24T04:07:13Z",
                "view_angle": 3,
                "visible_confidence_percent": 71,
                "visible_percent": 98
            },
            "type": "Feature"
        }
    ],
    "type": "FeatureCollection"
}
