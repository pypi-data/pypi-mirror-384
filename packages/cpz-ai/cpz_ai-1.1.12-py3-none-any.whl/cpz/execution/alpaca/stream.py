from __future__ import annotations

from typing import AsyncIterator, Iterable

from ..models import Quote


async def stream_quotes(symbols: Iterable[str]) -> AsyncIterator[Quote]:
    # Placeholder; actual streaming handled by adapter
    for sym in symbols:
        yield Quote(symbol=sym, bid=0.0, ask=0.0)
        break
