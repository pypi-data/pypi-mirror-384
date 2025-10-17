from __future__ import annotations

import os

import pytest

from cpz.common.errors import BrokerNotRegistered
from cpz.execution.router import BrokerRouter


def test_broker_not_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPACA_API_KEY_ID", raising=False)
    BrokerRouter._registry.clear()
    router = BrokerRouter()
    with pytest.raises(BrokerNotRegistered):
        router.get_positions()


def test_register_and_use() -> None:
    class Dummy:
        def get_account(self):
            from cpz.execution.models import Account

            return Account(id="a1", buying_power=0.0, equity=0.0, cash=0.0)

        def get_positions(self):
            return []

        def submit_order(self, req):
            raise NotImplementedError

        def get_order(self, order_id: str):
            raise NotImplementedError

        def cancel_order(self, order_id: str):
            raise NotImplementedError

        def replace_order(self, order_id: str, req):
            raise NotImplementedError

        async def stream_quotes(self, symbols):
            if False:
                from cpz.execution.models import Quote
                yield Quote(symbol="", bid=0.0, ask=0.0)

    BrokerRouter._registry.clear()
    BrokerRouter.register("dummy", lambda **_: Dummy())

    router = BrokerRouter()
    router.use_broker("dummy")
    assert router.get_positions() == []
