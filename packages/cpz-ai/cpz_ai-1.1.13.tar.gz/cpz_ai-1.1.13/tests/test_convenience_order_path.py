from __future__ import annotations

from types import SimpleNamespace

from cpz.clients.sync import CPZClient
from cpz.execution.enums import OrderSide, OrderType, TimeInForce


def test_client_convenience_order(monkeypatch):
    # Dummy adapter that returns a fixed order
    class Dummy:
        def submit_order(self, req):
            return SimpleNamespace(
                id="o2",
                symbol=req.symbol,
                side=SimpleNamespace(value=req.side.value),
                qty=req.qty,
                type=SimpleNamespace(value=req.type.value),
                time_in_force=SimpleNamespace(value=req.time_in_force.value),
                status=SimpleNamespace(value="accepted"),
            )

        def get_account(self):
            return SimpleNamespace(id="a1", buying_power=0, equity=0, cash=0)

        def get_positions(self):
            return []

    from cpz.execution.router import BrokerRouter

    BrokerRouter._registry.clear()
    BrokerRouter.register("alpaca", lambda **_: Dummy())

    c = CPZClient()
    c.execution.use_broker("alpaca", environment="paper")
    order = c.execution.order(
        symbol="MSFT",
        qty=2,
        side="buy",
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        broker="alpaca",
        env="paper",
        strategy_id="s-xyz",
    )
    assert getattr(order, "id", None) == "o2"


