from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class TokenBucketRateLimiter:
    tokens_per_second: float
    bucket_size: int

    def __post_init__(self) -> None:
        self._tokens = float(self.bucket_size)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self.bucket_size, self._tokens + elapsed * self.tokens_per_second)
            if self._tokens < 1.0:
                sleep_for = (1.0 - self._tokens) / self.tokens_per_second
                time.sleep(sleep_for)
                self._tokens = 0.0
                self._last = time.monotonic()
            else:
                self._tokens -= 1.0
