from __future__ import annotations

import json

from click.testing import CliRunner

from cpz.cli import main
from cpz.execution.router import BrokerRouter


def test_cli_broker_list_smoke() -> None:
    BrokerRouter._registry.clear()
    runner = CliRunner()
    res = runner.invoke(main, ["broker", "list"])
    assert res.exit_code == 0


def test_cli_order_submit_smoke(monkeypatch) -> None:
    from cpz.execution.enums import OrderSide, OrderType, TimeInForce
    from cpz.execution.models import Order, Quote

    class Dummy:
        def get_account(self):
            from cpz.execution.models import Account

            return Account(id="a1", buying_power=0, equity=0, cash=0)

        def get_positions(self):
            return []

        def submit_order(self, req):
            return Order(
                id="o1",
                symbol=req.symbol,
                side=req.side,
                qty=req.qty,
                type=req.type,
                time_in_force=req.time_in_force,
                status="accepted",
            )

        def get_order(self, order_id):
            return Order(
                id=order_id,
                symbol="AAPL",
                side=OrderSide.BUY,
                qty=1,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
                status="accepted",
            )

        def cancel_order(self, order_id):
            return self.get_order(order_id)

        def replace_order(self, order_id, req):
            return self.get_order(order_id)

        async def stream_quotes(self, symbols):
            for s in symbols:
                yield Quote(symbol=s, bid=1.0, ask=1.1)
                break

    BrokerRouter._registry.clear()
    BrokerRouter.register("alpaca", lambda **_: Dummy())

    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "order",
            "submit",
            "--symbol",
            "AAPL",
            "--side",
            "buy",
            "--qty",
            "1",
            "--type",
            "market",
            "--strategy-id",
            "test-strategy",
            "--tif",
            "day",
        ],
    )
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["id"] == "o1"
