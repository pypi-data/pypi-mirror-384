from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_alpaca_submit_order_monkeypatch(monkeypatch: pytest.MonkeyPatch) -> None:
    # Monkeypatch TradingClient before importing adapter
    class DummyTradingClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def submit_order(self, order_data):
            def enum(v: str):
                return SimpleNamespace(value=v)

            return SimpleNamespace(
                id="o1",
                symbol=order_data.symbol,
                side=enum(order_data.side.value.lower()),
                qty=order_data.qty,
                type=enum(getattr(order_data, "type", "market").lower()),
                time_in_force=enum(order_data.time_in_force.value),
                status=enum("accepted"),
            )

        def get_account(self):
            return SimpleNamespace(id="a1", buying_power=100000, equity=100000, cash=100000)

        def get_all_positions(self):
            return []

        def get_order_by_id(self, order_id: str):
            return SimpleNamespace(
                id=order_id,
                symbol="AAPL",
                side=SimpleNamespace(value="buy"),
                qty=1,
                type=SimpleNamespace(value="market"),
                time_in_force=SimpleNamespace(value="DAY"),
                status=SimpleNamespace(value="accepted"),
            )

        def cancel_order_by_id(self, order_id: str):
            return None

        def replace_order_by_id(self, order_id: str, order_data):
            return self.get_order_by_id(order_id)

    monkeypatch.setitem(sys.modules, "alpaca.trading.client", SimpleNamespace(TradingClient=DummyTradingClient))
    monkeypatch.setitem(sys.modules, "alpaca.trading.requests", SimpleNamespace(
        LimitOrderRequest=SimpleNamespace,
        MarketOrderRequest=SimpleNamespace,
        ReplaceOrderRequest=SimpleNamespace,
    ))
    monkeypatch.setitem(sys.modules, "alpaca.trading.enums", SimpleNamespace(
        OrderSide=SimpleNamespace,
        TimeInForce=SimpleNamespace,
    ))

    import cpz.execution.alpaca.adapter as adapter

    importlib.reload(adapter)

    from cpz.execution.alpaca.adapter import AlpacaAdapter
    from cpz.execution.enums import OrderSide, OrderType, TimeInForce
    from cpz.execution.models import OrderSubmitRequest

    adapter = AlpacaAdapter(api_key_id="x", api_secret_key="y", env="paper")
    req = OrderSubmitRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        strategy_id="s1",
    )
    order = adapter.submit_order(req)
    assert order.id == "o1"
    assert order.symbol == "AAPL"
    assert order.side.value == "buy"
