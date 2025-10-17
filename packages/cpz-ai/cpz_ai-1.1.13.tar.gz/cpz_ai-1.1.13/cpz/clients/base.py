from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from ..common.backoff import ExponentialBackoff
from ..common.config import Config
from ..common.logging import get_logger
from ..common.rate_limit import TokenBucketRateLimiter


@dataclass
class BaseClient:
    config: Config
    rate_limiter: TokenBucketRateLimiter
    backoff: ExponentialBackoff

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config.from_env({})
        self.logger: Any = get_logger()
        self.rate_limiter = TokenBucketRateLimiter(tokens_per_second=10, bucket_size=20)
        self.backoff = ExponentialBackoff(base=0.25, factor=2.0, max_delay=8.0, max_retries=3)

    def with_retries(self, func: Callable[[], Any], *, idempotent: bool = True) -> Any:
        if not idempotent:
            return func()
        attempt = 0
        last_exc: Optional[Exception] = None
        for delay in self.backoff:
            try:
                self.rate_limiter.acquire()
                return func()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                attempt += 1
                self.logger.warning("retrying", attempt=attempt, delay=delay, error=str(exc))
                self.backoff.sleep(delay)
        if last_exc is not None:
            raise last_exc
        return func()
