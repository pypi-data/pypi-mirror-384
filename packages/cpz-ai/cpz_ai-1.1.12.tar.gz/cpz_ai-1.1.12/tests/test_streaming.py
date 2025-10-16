from __future__ import annotations

from cpz.clients.async_ import AsyncCPZClient
from cpz.execution.models import Quote
from cpz.execution.router import BrokerRouter


class DummyAdapter:
    def get_account(self):
        raise NotImplementedError

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
        for s in symbols:
            yield Quote(symbol=s, bid=1.0, ask=1.1)
            break


def test_streaming_quotes() -> None:
    import asyncio

    async def run() -> None:
        BrokerRouter._registry.clear()
        BrokerRouter.register("dummy", lambda **_: DummyAdapter())
        client = AsyncCPZClient()
        await client.execution.use_broker("dummy")
        async for q in client.execution.stream_quotes(["AAPL"]):
            assert q.symbol == "AAPL"
            break

    asyncio.run(run())
