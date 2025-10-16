from __future__ import annotations

import os
import pytest

from cpz.clients.sync import CPZClient


@pytest.mark.skipif(os.getenv("CPZ_RUN_INTEGRATION") != "1", reason="Set CPZ_RUN_INTEGRATION=1 to run real order placement")
def test_place_ko_order_integration() -> None:
    # Requires CPZ_AI_API_KEY/CPZ_AI_SECRET_KEY in env and broker creds on account
    strategy_id = os.getenv("CPZ_STRATEGY_ID")
    assert strategy_id, "CPZ_STRATEGY_ID must be set for integration test"

    client = CPZClient()
    client.execution.use_broker("alpaca", environment=os.getenv("CPZ_BROKER_ENV", "paper"))

    order = client.execution.order(
        symbol="KO",
        qty=1,
        side="buy",
        order_type="market",
        time_in_force="DAY",
        broker="alpaca",
        env=os.getenv("CPZ_BROKER_ENV", "paper"),
        strategy_id=strategy_id,
    )
    assert order.symbol == "KO"


