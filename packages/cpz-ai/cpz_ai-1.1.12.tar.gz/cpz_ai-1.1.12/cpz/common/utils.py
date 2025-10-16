from __future__ import annotations

from typing import Iterable, TypeVar

T = TypeVar("T")


def ensure_iterable(obj: T | Iterable[T]) -> Iterable[T]:
    if isinstance(obj, (str, bytes)):
        return [obj]  # type: ignore[list-item]
    try:
        iter(obj)  # type: ignore[arg-type]
        return obj  # type: ignore[return-value]
    except TypeError:
        return [obj]  # type: ignore[list-item]
