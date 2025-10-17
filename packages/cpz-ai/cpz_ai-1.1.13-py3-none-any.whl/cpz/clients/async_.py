from __future__ import annotations

from typing import AsyncIterator, Iterable, Optional

from ..common.cpz_ai import CPZAIClient as SupabaseClient
from ..execution.models import (
    Account,
    Order,
    OrderReplaceRequest,
    OrderSubmitRequest,
    Position,
    Quote,
)
from ..execution.router import BrokerRouter
from .base import BaseClient


class _AsyncExecutionNamespace:
    def __init__(self, router: BrokerRouter) -> None:
        self.router = router

    async def use_broker(self, name: str, environment: str = "paper", account_id: Optional[str] = None) -> None:
        self.router.use_broker(name, environment=environment, account_id=account_id)

    def get_account(self) -> Account:
        return self.router.get_account()

    def get_positions(self) -> list[Position]:
        return self.router.get_positions()

    def submit_order(self, req: OrderSubmitRequest) -> Order:
        return self.router.submit_order(req)

    def get_order(self, order_id: str) -> Order:
        return self.router.get_order(order_id)

    def cancel_order(self, order_id: str) -> Order:
        return self.router.cancel_order(order_id)

    def replace_order(self, order_id: str, req: OrderReplaceRequest) -> Order:
        return self.router.replace_order(order_id, req)

    async def stream_quotes(self, symbols: Iterable[str]) -> AsyncIterator[Quote]:
        async for q in self.router.stream_quotes(symbols):
            yield q


class _AsyncPlatformNamespace:
    def __init__(self) -> None:
        self._sb: SupabaseClient | None = None

    async def configure(
        self, *, url: str | None = None, anon: str | None = None, service: str | None = None
    ) -> None:
        if url and anon:
            self._sb = SupabaseClient(url=url, anon_key=anon, service_key=service)
        else:
            self._sb = SupabaseClient.from_env()

    def _require(self) -> SupabaseClient:
        if self._sb is None:
            self._sb = SupabaseClient.from_env()
        return self._sb

    async def health(self) -> bool:
        return self._require().health()

    async def echo(self) -> dict[str, object]:
        return self._require().echo()

    async def list_tables(self) -> list[str]:
        return self._require().list_tables()


class AsyncCPZClient(BaseClient):
    def __init__(self, cpz_client: Optional[SupabaseClient] = None) -> None:
        super().__init__()
        self._cpz_client = cpz_client or SupabaseClient.from_env()
        self.execution = _AsyncExecutionNamespace(BrokerRouter.default().with_cpz_client(self._cpz_client))
        self.platform = _AsyncPlatformNamespace()

    @property
    def router(self) -> BrokerRouter:
        return self.execution.router
