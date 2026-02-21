from __future__ import annotations
from typing import Iterator
from app.clients.base import ProviderClient

BASE = "https://reqres.in/api"

class ReqResClient(ProviderClient):
    name = "reqres"

    def iter_pages(self) -> Iterator[list[dict]]:
        page = 1
        while True:
            resp = self._get(f"{BASE}/users", params={"page": page})
            resp.raise_for_status()
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break
            yield items
            total_pages = payload.get("total_pages", page)
            page += 1
            if page > total_pages:
                break
