from __future__ import annotations

from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


def paginate(items: Iterable[T]) -> Iterator[T]:
    for item in items:
        yield item
