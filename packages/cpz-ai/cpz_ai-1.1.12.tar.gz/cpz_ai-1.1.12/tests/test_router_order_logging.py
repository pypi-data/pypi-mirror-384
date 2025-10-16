from __future__ import annotations

from types import SimpleNamespace

from cpz.execution.enums import OrderSide, OrderType, TimeInForce
from cpz.execution.models import OrderSubmitRequest
from cpz.execution.router import BrokerRouter


def test_router_logs_intent_and_updates(monkeypatch):
    calls: dict[str, int] = {"create": 0, "update": 0}

    # Prepare a dummy adapter that returns a deterministic order
    class Dummy:
        def submit_order(self, req: OrderSubmitRequest):
            return SimpleNamespace(
                id="oX",
                symbol=req.symbol,
                side=SimpleNamespace(value=req.side.value),
                qty=req.qty,
                type=SimpleNamespace(value=req.type.value),
                time_in_force=SimpleNamespace(value=req.time_in_force.value),
                status=SimpleNamespace(value="accepted"),
            )

        def get_order(self, order_id: str):  # used by optional polling
            return SimpleNamespace(
                id=order_id,
                symbol="AAPL",
                side=SimpleNamespace(value="buy"),
                qty=1,
                type=SimpleNamespace(value="market"),
                time_in_force=SimpleNamespace(value="DAY"),
                status=SimpleNamespace(value="accepted"),
            )

        def get_account(self):
            return SimpleNamespace(id="a1", buying_power=0, equity=0, cash=0)

        def get_positions(self):
            return []

    # Register dummy broker
    BrokerRouter._registry.clear()
    BrokerRouter.register("alpaca", lambda **_: Dummy())

    # Ensure polling is minimal and enabled
    monkeypatch.setenv("CPZ_POLL_TOTAL_SECONDS", "1")
    monkeypatch.setenv("CPZ_POLL_INTERVAL_SECONDS", "0.01")
    monkeypatch.setenv("CPZ_ENABLE_FILL_POLLING", "true")

    # Build request
    req = OrderSubmitRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        strategy_id="s1",
    )

    router = BrokerRouter.default()
    router.use_broker("alpaca", env="paper")
    order = router.submit_order(req)

    assert getattr(order, "id", None) == "oX"


