from __future__ import annotations

import asyncio
import math
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import AsyncIterator, Dict, Iterable, List, Optional

from .interfaces import BrokerAdapter
from .models import (
    Account,
    Bar,
    Order,
    OrderReplaceRequest,
    OrderSubmitRequest,
    Position,
    Quote,
)
from .enums import OrderSide, OrderType, TimeInForce


@dataclass
class _OpenOrder:
    order: Order
    limit_price: Optional[float]


class CPZNativeAdapter(BrokerAdapter):
    """Broker-less adapter that simulates data + paper execution entirely in-memory.
    - No external APIs or SDKs
    - Deterministic-ish random-walk quotes per symbol
    - Immediate fill for MARKET orders
    - LIMIT orders fill if the synthetic last price crosses the limit
    - Simple account/positions ledger
    """

    def __init__(self, *, starting_cash: float = 1_000_000.0, seed: int = 1337) -> None:
        random.seed(seed)
        self._cash: float = float(starting_cash)
        self._positions: Dict[str, float] = {}   # symbol -> qty
        self._avg_price: Dict[str, float] = {}   # symbol -> avg entry
        self._last_price: Dict[str, float] = {}  # symbol -> last synthetic price
        self._orders: Dict[str, _OpenOrder] = {} # order_id -> open order
        self._fills: Dict[str, Order] = {}       # order_id -> final order snapshot

    # -------- helpers --------
    def _now(self) -> datetime:
        return datetime.utcnow()

    def _px(self, symbol: str) -> float:
        base = self._last_price.get(symbol, 100.0 + (hash(symbol) % 50))
        # small random walk
        step = random.uniform(-0.5, 0.5)
        px = max(0.01, base + step)
        self._last_price[symbol] = px
        return px

    def _equity(self) -> float:
        mv = 0.0
        for sym, qty in self._positions.items():
            mv += qty * self._px(sym)
        return self._cash + mv

    def _mk_order(self, req: OrderSubmitRequest, status: str) -> Order:
        return Order(
            id=str(uuid.uuid4()),
            symbol=req.symbol,
            side=req.side,
            qty=req.qty,
            type=req.type,
            time_in_force=req.time_in_force,
            status=status,
            created_at=self._now(),
        )

    # ------------- execution -------------
    def get_account(self) -> Account:
        # naive 2x BP for demo; adjust as needed
        equity = self._equity()
        buying_power = 2.0 * equity
        return Account(id="CPZ_NATIVE", buying_power=buying_power, equity=equity, cash=self._cash)

    def get_positions(self) -> list[Position]:
        out: List[Position] = []
        for sym, qty in self._positions.items():
            mv = qty * self._px(sym)
            out.append(Position(symbol=sym, qty=qty, avg_entry_price=self._avg_price.get(sym, 0.0), market_value=mv))
        return out

    def submit_order(self, req: OrderSubmitRequest) -> Order:
        sym = req.symbol
        side = req.side
        qty = float(req.qty)
        px = self._px(sym)

        if req.type == OrderType.MARKET:
            fill_px = px
            self._apply_fill(sym, side, qty, fill_px)
            o = self._mk_order(req, status="filled")
            self._fills[o.id] = o
            return o

        # LIMIT
        o = self._mk_order(req, status="open")
        self._orders[o.id] = _OpenOrder(order=o, limit_price=req.limit_price)
        # try immediate cross
        if req.limit_price is not None and self._crosses(side, px, req.limit_price):
            self._apply_fill(sym, side, qty, req.limit_price)
            o.status = "filled"
            self._fills[o.id] = o
            del self._orders[o.id]
        return o

    def _crosses(self, side: OrderSide, px: float, limit_px: float) -> bool:
        return (side == OrderSide.BUY and px <= limit_px) or (side == OrderSide.SELL and px >= limit_px)

    def _apply_fill(self, symbol: str, side: OrderSide, qty: float, px: float) -> None:
        # update cash
        notional = qty * px
        if side == OrderSide.BUY:
            self._cash -= notional
            prev_qty = self._positions.get(symbol, 0.0)
            prev_avg = self._avg_price.get(symbol, 0.0)
            new_qty = prev_qty + qty
            new_avg = ((prev_avg * prev_qty) + notional) / new_qty if new_qty != 0 else 0.0
            self._positions[symbol] = new_qty
            self._avg_price[symbol] = new_avg
        else:
            self._cash += notional
            prev_qty = self._positions.get(symbol, 0.0)
            new_qty = prev_qty - qty
            if math.isclose(new_qty, 0.0, abs_tol=1e-9):
                new_qty = 0.0
            self._positions[symbol] = new_qty
            if new_qty == 0.0:
                self._avg_price.pop(symbol, None)

    def get_order(self, order_id: str) -> Order:
        if order_id in self._fills:
            return self._fills[order_id]
        if order_id in self._orders:
            return self._orders[order_id].order
        # unknown => canceled for simplicity
        return Order(
            id=order_id,
            symbol="UNKNOWN",
            side=OrderSide.BUY,
            qty=0.0,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            status="canceled",
            created_at=self._now(),
        )

    def cancel_order(self, order_id: str) -> Order:
        if order_id in self._orders:
            o = self._orders[order_id].order
            o.status = "canceled"
            del self._orders[order_id]
            return o
        return self.get_order(order_id)

    def replace_order(self, order_id: str, req: OrderReplaceRequest) -> Order:
        if order_id not in self._orders:
            return self.get_order(order_id)
        oo = self._orders[order_id]
        o = oo.order
        # mutate qty / limit
        if req.qty is not None:
            o.qty = float(req.qty)
        if req.limit_price is not None:
            oo.limit_price = float(req.limit_price)

        # check cross again
        sym = o.symbol
        side = o.side
        px = self._px(sym)
        lim = oo.limit_price if oo.limit_price is not None else px
        if self._crosses(side, px, lim):
            self._apply_fill(sym, side, o.qty, lim)
            o.status = "filled"
            self._fills[o.id] = o
            del self._orders[o.id]
        return o

    def stream_quotes(self, symbols: Iterable[str]) -> AsyncIterator[Quote]:
        async def _gen() -> AsyncIterator[Quote]:
            while True:
                for sym in symbols:
                    yield Quote(symbol=sym, bid=self._px(sym) - 0.01, ask=self._px(sym) + 0.01)
                await asyncio.sleep(0.5)
        return _gen()

    # ------------- data -------------
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        return [Quote(symbol=s, bid=self._px(s) - 0.01, ask=self._px(s) + 0.01) for s in symbols]

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Bar]:
        # Generate a synthetic OHLCV series as a simple random walk.
        # If 'start'/'end' provided, we walk forward from start to min(end, start + limit*step).
        step = self._timeframe_to_timedelta(timeframe)
        if start is None:
            end = end or self._now()
            start = end - step * limit
        else:
            end = end or (start + step * limit)

        t = start
        px = self._last_price.get(symbol, 100.0 + (hash(symbol) % 50))
        out: List[Bar] = []
        while t < end and len(out) < limit:
            # simulate OHLCV around px
            o = px + random.uniform(-0.2, 0.2)
            h = o + abs(random.uniform(0, 0.5))
            l = o - abs(random.uniform(0, 0.5))
            c = l + (h - l) * random.random()
            v = abs(random.gauss(1_000_000, 200_000))
            out.append(Bar(symbol=symbol, open=max(0.01, o), high=max(0.01, h), low=max(0.01, l), close=max(0.01, c), volume=float(v), ts=t))
            t += step
            px = c
        # update last price
        if out:
            self._last_price[symbol] = out[-1].close
        return out

    # -------- utils --------
    def _timeframe_to_timedelta(self, tf: str) -> timedelta:
        tf = tf.lower()
        if tf in {"1min", "1m", "min"}:
            return timedelta(minutes=1)
        if tf in {"5min", "5m"}:
            return timedelta(minutes=5)
        if tf in {"15min", "15m"}:
            return timedelta(minutes=15)
        if tf in {"1hour", "1h"}:
            return timedelta(hours=1)
        return timedelta(days=1)  # default day

    # factory to match Router.register pattern
    @staticmethod
    def create(**kwargs: object) -> "CPZNativeAdapter":
        starting_cash = float(kwargs.get("starting_cash", 1_000_000.0))  # type: ignore[arg-type]
        seed = int(kwargs.get("seed", 1337))  # type: ignore[arg-type]
        return CPZNativeAdapter(starting_cash=starting_cash, seed=seed)
