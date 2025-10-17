from __future__ import annotations

import pytest

from cpz.execution.enums import OrderSide, OrderType, TimeInForce
from cpz.execution.models import OrderSubmitRequest


def test_limit_order_requires_price() -> None:
    with pytest.raises(ValueError):
        OrderSubmitRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            qty=1,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            strategy_id="s1",
        )


def test_market_order_no_price_ok() -> None:
    req = OrderSubmitRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        strategy_id="s1",
    )
    assert req.symbol == "AAPL"
