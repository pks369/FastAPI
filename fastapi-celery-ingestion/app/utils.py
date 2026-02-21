import hashlib
import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def idempotency_key(provider: str, external_id: str) -> str:
    return hashlib.sha256(f"{provider}:{external_id}".encode()).hexdigest()


def retry_with_backoff(fn: Callable[[], T], *, retries: int, base_delay: float, jitter: float = 0.3) -> T:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt == retries:
                break
            sleep_for = base_delay * (2 ** attempt) * (1 + random.uniform(0, jitter))
            time.sleep(sleep_for)
    raise last_exc  # type: ignore[misc]
