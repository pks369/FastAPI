from __future__ import annotations
from typing import Iterator
from app.clients.base import ProviderClient

BASE = "https://dummyjson.com"

class DummyJSONClient(ProviderClient):
    name = "dummyjson"

    def iter_pages(self) -> Iterator[list[dict]]:
        limit = 30
        skip = 0
        while True:
            resp = self._get(f"{BASE}/products", params={"limit": limit, "skip": skip})
            resp.raise_for_status()
            payload = resp.json()
            items = payload.get("products", [])
            if not items:
                break
            yield items
            skip += limit
            if skip >= payload.get("total", 0):
                break
