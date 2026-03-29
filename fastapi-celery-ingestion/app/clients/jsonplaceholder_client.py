from __future__ import annotations
from typing import Iterator
from app.clients.base import ProviderClient

BASE = "https://jsonplaceholder.typicode.com"

class JSONPlaceholderClient(ProviderClient):
    name = "jsonplaceholder"

    def iter_pages(self) -> Iterator[list[dict]]:
        # 100 posts total; paginate with _page and _limit
        page = 1
        limit = 20
        while True:
            resp = self._get(f"{BASE}/posts", params={"_page": page, "_limit": limit})
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            yield data
            page += 1
