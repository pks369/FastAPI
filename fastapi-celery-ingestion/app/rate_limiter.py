import threading
import time
from collections import defaultdict

class TokenBucket:
    def __init__(self, rate_per_sec: int, capacity: int | None = None):
        self.rate = max(1, rate_per_sec)
        self.capacity = capacity or self.rate
        self.tokens = float(self.capacity)
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.updated
            self.updated = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            # not enough tokens; compute wait
            needed = 1 - self.tokens
            wait = needed / self.rate
        time.sleep(wait)
        # after sleep, take token recursively
        return self.acquire()

class RateLimiter:
    def __init__(self, global_rps: int, provider_limits: dict[str, int]):
        self.global_bucket = TokenBucket(global_rps)
        self.provider_buckets = {k: TokenBucket(v) for k, v in provider_limits.items()}

    def acquire(self, provider: str):
        # acquire order avoids starvation
        self.global_bucket.acquire()
        bucket = self.provider_buckets.get(provider)
        if bucket is None:
            return
        bucket.acquire()
