class OrderDetail(object):
    def __init__(self, _links, id, name, tools=None, products=None, metadata=None,
                 created_on=None, last_modified=None, state=None, last_message=None, error_hints=None,
                 delivery=None, notifications=None, order_type=None,
                 source_type=None, hosting=None, subscription_id=None) -> None:
        self._links = Links(**_links)
        self.id = id
        self.name = name
        self.subscription_id = subscription_id
        self.tools = tools
        self.products = [Product(**p) for p in (products or [])]
        self.metadata = metadata
        self.created_on = created_on
        self.last_modified = last_modified
        self.state = state
        self.last_message = last_message
        self.error_hints = error_hints
        self.delivery = delivery
        self.notifications = notifications
        self.order_type = order_type
        self.source_type = source_type
        self.hosting = hosting


class Links(object):
    def __init__(self, _self, results: list = None) -> None:
        self._self = _self
        self.results = [Result(**v) for v in (results or [])]


class Result(object):
    def __init__(self, delivery, name, location, expires_at) -> None:
        self.delivery = delivery
        self.name = name
        self.location = location
        self.expires_at = expires_at


class Product(object):
    def __init__(self, item_ids, item_type, product_bundle) -> None:
        self.item_ids = item_ids
        self.item_type = item_type
        self.product_bundle = product_bundle


__template = {
    "_links": {
        "_self": "https://api.planet.com/compute/ops/orders/v2/bda241bb-a62d-4369-9aaa-b4fd207de8b4",
        "results": [
            {
                "delivery": "success",
                "expires_at": "2024-08-27T13:23:34.526Z",
                "location": "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjQ3NjUwMTQsInN1YiI6InRVbGxYLy9qeUJBaktzZGxTNUp1Y0xCOGNuaW9LNTZqdGNScGxKVzlKRGtMQzd1UWJWbWt4cFlxb21vSGVCVlFFUit5OVFoRVlZcXNSakFCZXdoWC9BPT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS9iZGEyNDFiYi1hNjJkLTQzNjktOWFhYS1iNGZkMjA3ZGU4YjQvY3djdGVzdDFfcHNzY2VuZV9hbmFseXRpY19zcl91ZG0yLnppcD9YLUdvb2ctQWxnb3JpdGhtPUdPT0c0LVJTQS1TSEEyNTZcdTAwMjZYLUdvb2ctQ3JlZGVudGlhbD1jb21wdXRlLWdjcy1zdmNhY2MlNDBwbGFuZXQtY29tcHV0ZS1wcm9kLmlhbS5nc2VydmljZWFjY291bnQuY29tJTJGMjAyNDA4MjYlMkZhdXRvJTJGc3RvcmFnZSUyRmdvb2c0X3JlcXVlc3RcdTAwMjZYLUdvb2ctRGF0ZT0yMDI0MDgyNlQxMzIzMzRaXHUwMDI2WC1Hb29nLUV4cGlyZXM9ODYzOTlcdTAwMjZYLUdvb2ctU2lnbmF0dXJlPTk5ZjRmNTRlMTVjODk4MWQ0YjkwYmRjYjRlOTVhNDMwZjdlY2FlOTc0NWMwMzkyMjBhNDMyNDYwYmIyZDk0OWVlNmZmYWZhOGQ0YmNhNWJiMTEzYzI0OTkzNDJlMjcyZWZjYWEzNGRjYWM3ZmE5OTlkM2FhYWY3NTA5NDFmY2JjNWZhMjk1NmYzOGE4MmJhNjFmMjk3Zjc2Y2MxMmU1YWE0ZjBiYzFkNGNlMGJlZWUzZTFjOTQyNjc5ZjVlNGE0YzRhNzVkZTVmZjJmMzI5OWI3YzYyNzQxMmFlZjEzY2IzNDdlZjA4YmNlNGJlNmNmMmFkMWEwZjQ1ODU0MjY5YTA5OGM0NjlkNTcxMTg2NGE0MmFmMmZhNmQ5OTRlZDZmN2EzMzlhMjhlMDIyZWM3OGMwNDVmZTk2NGY2YTA4ODJjZDI4YWM2MmYxMGFiNmI1NWFiZjM3YTZlNWQyZDkzMjEzNTMzNzRlNGIyODVhZTQ1NTI4NzM2NGI1YzI4YTE4NjhlMmRkZDk4NGEyMmU1ZmQyNGZmM2M2YjU1MDRmNmVmOTM1MzcyZjQ1ZTE1NmQ3ZGI1YTRjOTE4NjYzZGI2Mzg5ODJmNjM2Y2NmZmQ0ZTBhOTA0OTg1MGY1NGU2MWQ3NmMzOWJhNGI4YzY1MjNmNWJmMWQyMTZhNGVkZjQzNjc3XHUwMDI2WC1Hb29nLVNpZ25lZEhlYWRlcnM9aG9zdCIsInNvdXJjZSI6Ik9yZGVycyBTZXJ2aWNlIn0.1LVhIyWwkLBtRcTICUuMfH0oTaExWDcsXA1k54HNDBI5CBbeWxP-r217xumSgVlil8D5EPyt6xKqDHZhpO-XYQ",
                "name": "bda241bb-a62d-4369-9aaa-b4fd207de8b4/cwctest1_psscene_analytic_sr_udm2.zip"
            },
            {
                "delivery": "success",
                "expires_at": "2024-08-27T13:23:34.527Z",
                "location": "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjQ3NjUwMTQsInN1YiI6IjA3VUJHYm9ZNEJjeXViaU9ncXlpUC9ESlBTVTQ0NnZReVFCY2FZakdFblFCRng4RnFFZ1VjWVl5NWRzZmJGVW93L09SclJlb29RaTlIQy9SMlptdXh3PT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS9iZGEyNDFiYi1hNjJkLTQzNjktOWFhYS1iNGZkMjA3ZGU4YjQvbWFuaWZlc3QuanNvbj9YLUdvb2ctQWxnb3JpdGhtPUdPT0c0LVJTQS1TSEEyNTZcdTAwMjZYLUdvb2ctQ3JlZGVudGlhbD1jb21wdXRlLWdjcy1zdmNhY2MlNDBwbGFuZXQtY29tcHV0ZS1wcm9kLmlhbS5nc2VydmljZWFjY291bnQuY29tJTJGMjAyNDA4MjYlMkZhdXRvJTJGc3RvcmFnZSUyRmdvb2c0X3JlcXVlc3RcdTAwMjZYLUdvb2ctRGF0ZT0yMDI0MDgyNlQxMzIzMzRaXHUwMDI2WC1Hb29nLUV4cGlyZXM9ODYzOTlcdTAwMjZYLUdvb2ctU2lnbmF0dXJlPTYzZGZkMzA1MTQzZjY4YTVjMDUyODA3ZmYzNDhmYzhjMWIwYTAyMTg5ZDlhM2E5NDE3MmIyNWRlNDU1YTk3OTRmZDE5YjMxZmYxOWE0NzM0NDJlYTNlNmQzNzk3YWIxZDhhNWRiNGIxMzI2YTdlN2E5ODU2YWE1ZmQ1Mzk5YWVmZjFkZTBmZjAzOWQzNTEwMTQxODg0MGU4NzU0N2I4NDNiN2ZjYjMyNzI3ZWQ2Y2M5NWMxNmEzMjY2ZTAzYzQ2ZTAxYThjOTc2NDRkNGQwNWQ0ZmYwNmQ4MWQxYjdlNmU4MjRmZjI1YjQ5ZDdiYWFmNjBkNDMxMTMzNDQ5ZWI3Y2U1MWEyNmJjNzAyYTE2YWFjYmY4ODNiMGEyZmFmODI5Zjc3MTNmZDQ2YWQyNjg3YzU4ODU1M2RmNmJhNzcyMTYwNmQ2ZWJkYWJmZTk5NzI2ZjNhOGI0ZmEzMWJiYzJmMjJmOGRjMjI0Y2U3ZTMxZGQ1YjM4Njk5MjdiODE1NzExZWU2ZDAwMzg4ODVmYWUzMDc4OWUyYWFmYzBkOGY4ZTI0YzdmOTEzNDhmMzhmNGQ3YTNhN2Y5Yzc2NDA3NDM4MjhhOTgyZmNhMDM1MDQ5Y2UyMmVlYzAxYzRhYjVhMmNiMzQ5NDg0NDFkMDMzMzJiNjNmMDg1NDhlZTlmMWUxMzk4XHUwMDI2WC1Hb29nLVNpZ25lZEhlYWRlcnM9aG9zdCIsInNvdXJjZSI6Ik9yZGVycyBTZXJ2aWNlIn0.PWboDvwPJ0W_PSWAcsXuWiU-i4X44YFC6vbQVFPz9QksCR8fvrwkmbmjXb0eGdjaSE_YEQYdmgCblvBqfrzTzw",
                "name": "bda241bb-a62d-4369-9aaa-b4fd207de8b4/manifest.json"
            }
        ]
    },
    "created_on": "2024-08-22T01:53:19.755Z",
    "delivery": {
        "archive_filename": "{{name}}_psscene_analytic_sr_udm2.zip",
        "archive_type": "zip",
        "single_archive": True
    },
    "error_hints": [],
    "id": "bda241bb-a62d-4369-9aaa-b4fd207de8b4",
    "last_message": "Manifest delivery completed",
    "last_modified": "2024-08-22T02:01:17.587Z",
    "metadata": {
        "stac": {}
    },
    "name": "cwctest1",
    "notifications": {
        "email": True
    },
    "order_type": "partial",
    "products": [
        {
            "item_ids": [
                "20220429_021332_1002"
            ],
            "item_type": "PSScene",
            "product_bundle": "analytic_sr_udm2"
        }
    ],
    "state": "success",
    "tools": [
        {
            "clip": {
                "aoi": {
                    "coordinates": [
                        [
                            [
                                121.2758509,
                                37.51339838
                            ],
                            [
                                121.2780917,
                                37.52732028
                            ],
                            [
                                121.28406718,
                                37.52776455
                            ],
                            [
                                121.28107944,
                                37.51384273
                            ],
                            [
                                121.2758509,
                                37.51339838
                            ]
                        ]
                    ],
                    "type": "Polygon"
                }
            }
        }
    ]
}