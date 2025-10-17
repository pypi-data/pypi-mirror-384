from __future__ import annotations

from typing import Iterable

import pytest

from cpz.clients.sync import CPZClient
from cpz.execution.enums import OrderSide, OrderType, TimeInForce
from cpz.execution.models import Order, OrderSubmitRequest
from cpz.execution.router import BrokerRouter


class DummyAdapter:
    def __init__(self) -> None:
        self.submitted: list[OrderSubmitRequest] = []

    def get_account(self):
        from cpz.execution.models import Account

        return Account(id="a1", buying_power=100000.0, equity=100000.0, cash=100000.0)

    def get_positions(self):
        return []

    def submit_order(self, req: OrderSubmitRequest) -> Order:
        self.submitted.append(req)
        return Order(
            id="o1",
            symbol=req.symbol,
            side=req.side,
            qty=req.qty,
            type=req.type,
            time_in_force=req.time_in_force,
            status="accepted",
        )

    def get_order(self, order_id: str) -> Order:
        return Order(
            id=order_id,
            symbol="AAPL",
            side=OrderSide.BUY,
            qty=1,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            status="accepted",
        )

    def cancel_order(self, order_id: str) -> Order:
        return self.get_order(order_id)

    def replace_order(self, order_id: str, req):
        return self.get_order(order_id)

    async def stream_quotes(self, symbols: Iterable[str]):
        from cpz.execution.models import Quote

        for s in symbols:
            yield Quote(symbol=s, bid=1.0, ask=1.1)
            break


def test_sync_client_submit_order(monkeypatch: pytest.MonkeyPatch) -> None:
    router = BrokerRouter()
    BrokerRouter._registry.clear()
    BrokerRouter.register("dummy", lambda **_: DummyAdapter())

    client = CPZClient()
    client.execution.router = router  # type: ignore[assignment]
    client.execution.use_broker("dummy")

    req = OrderSubmitRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        strategy_id="test-strat",
    )
    order = client.execution.submit_order(req)
    assert order.id == "o1"
    assert order.symbol == "AAPL"
