from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator


@dataclass
class ExponentialBackoff:
    base: float = 0.25
    factor: float = 2.0
    max_delay: float = 8.0
    max_retries: int = 3

    def __iter__(self) -> Iterator[float]:
        delay = self.base
        for _ in range(self.max_retries):
            yield delay
            delay = min(delay * self.factor, self.max_delay)

    @staticmethod
    def sleep(delay: float) -> None:
        time.sleep(delay)
