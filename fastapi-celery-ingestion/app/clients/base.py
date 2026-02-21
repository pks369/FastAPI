from __future__ import annotations
import requests
from typing import Iterator
from app.core.config import settings
from app.rate_limiter import RateLimiter

DEFAULT_HEADERS = {"User-Agent": "ingestion-service/1.0"}

class ProviderClient:
    name: str

    def __init__(self, limiter: RateLimiter):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.timeout = settings.HTTP_TIMEOUT_SECONDS
        self.limiter = limiter

    def iter_pages(self) -> Iterator[list[dict]]:
        raise NotImplementedError

    def _get(self, url: str, *, params: dict | None = None) -> requests.Response:
        # Enforce rate limit INSIDE the worker thread
        self.limiter.acquire(self.name)
        return self.session.get(url, params=params, timeout=self.timeout)
