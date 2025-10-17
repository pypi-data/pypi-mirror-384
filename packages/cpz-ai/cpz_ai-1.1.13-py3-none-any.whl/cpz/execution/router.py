from __future__ import annotations

import os
from typing import AsyncIterator, Callable, Dict, Iterable, Optional
import time

from ..common.errors import BrokerNotRegistered
from .interfaces import BrokerAdapter
from .models import Account, Order, OrderReplaceRequest, OrderSubmitRequest, Position, Quote

BROKER_ALPACA = "alpaca"


class BrokerRouter:
    _registry: Dict[str, Callable[..., BrokerAdapter]] = {}

    def __init__(self) -> None:
        self._active: Optional[BrokerAdapter] = None
        self._active_name: Optional[str] = None
        self._active_kwargs: Dict[str, object] = {}

    @classmethod
    def register(cls, name: str, factory: Callable[..., BrokerAdapter]) -> None:
        cls._registry[name] = factory

    def list_brokers(self) -> list[str]:
        return list(self._registry.keys())

    @classmethod
    def default(cls) -> "BrokerRouter":
        if BROKER_ALPACA not in cls._registry:
            try:
                from .alpaca.adapter import AlpacaAdapter

                cls.register(BROKER_ALPACA, AlpacaAdapter.create)
            except Exception:
                pass
        return cls()

    def use_broker(self, name: str, **kwargs: object) -> None:
        if name not in self._registry:
            raise BrokerNotRegistered(name)
        factory = self._registry[name]
        self._active = factory(**kwargs)
        self._active_name = name
        self._active_kwargs = dict(kwargs)

    def _require_active(self) -> BrokerAdapter:
        if self._active is None:
            if len(self._registry) == 1:
                _name, factory = next(iter(self._registry.items()))
                self._active = factory()
                return self._active
            if os.getenv("ALPACA_API_KEY_ID"):
                self.use_broker(BROKER_ALPACA, env=os.getenv("ALPACA_ENV", "paper"))
            else:
                raise BrokerNotRegistered("<none>")
        assert self._active is not None
        return self._active

    def get_account(self) -> Account:
        return self._require_active().get_account()

    def get_positions(self) -> list[Position]:
        return self._require_active().get_positions()

    def submit_order(self, req: OrderSubmitRequest) -> Order:
        from ..common.cpz_ai import CPZAIClient

        broker_name = self._active_name or BROKER_ALPACA
        account_id = str(self._active_kwargs.get("account_id") or "").strip() or None
        # If account_id is provided, ignore env for routing/credential resolution
        env = "" if account_id else str(self._active_kwargs.get("env") or "paper")
        logging_mode = os.getenv("CPZ_ORDER_LOGGING_MODE", "intent-first").lower()

        sb = CPZAIClient.from_env()
        intent_id: Optional[str] = None

        # 1) Logging strategy
        if logging_mode == "disabled":
            intent = None
        elif logging_mode == "broker-first":
            # Best-effort: try to create an intent but do not abort on failure
            try:
                intent = sb.create_order_intent(
                    symbol=req.symbol,
                    side=req.side.value,
                    qty=req.qty,
                    type=req.type.value,
                    time_in_force=req.time_in_force.value,
                    broker=broker_name,
                    env=env,
                    strategy_id=getattr(req, "strategy_id", ""),
                    status="pending",
                    account_id=account_id,
                )
                if isinstance(intent, dict):
                    intent_id = str(intent.get("id") or "") or None
            except Exception:
                intent = None
        else:
            # intent-first (default): must succeed before sending to broker
            intent = sb.create_order_intent(
                symbol=req.symbol,
                side=req.side.value,
                qty=req.qty,
                type=req.type.value,
                time_in_force=req.time_in_force.value,
                broker=broker_name,
                env=env,
                strategy_id=getattr(req, "strategy_id", ""),
                status="pending",
                account_id=account_id,
            )
            if not intent or not isinstance(intent, dict) or not intent.get("id"):
                raise RuntimeError("Failed to record order intent in CPZ orders table")
            intent_id = str(intent.get("id"))

        # 2) Send to broker
        order = self._require_active().submit_order(req)

        # 3) Update order record with broker order_id, status, and fills if available
        try:
            if intent_id:
                sb.update_order_record(
                    id=intent_id,
                    order_id=order.id,
                    status=getattr(order, "status", None),
                    filled_qty=getattr(order, "filled_qty", None),
                    average_fill_price=getattr(order, "average_fill_price", None),
                    submitted_at=(getattr(order, "submitted_at", None).isoformat() if getattr(order, "submitted_at", None) else None),
                    filled_at=(getattr(order, "filled_at", None).isoformat() if getattr(order, "filled_at", None) else None),
                )
            elif logging_mode == "broker-first":
                # Create a record post-broker if initial intent was skipped/failed
                try:
                    sb.record_order(
                        order_id=order.id,
                        symbol=req.symbol,
                        side=req.side.value,
                        qty=req.qty,
                        type=req.type.value,
                        time_in_force=req.time_in_force.value,
                        broker=broker_name,
                        env=env,
                        strategy_id=getattr(req, "strategy_id", None),
                        status=getattr(order, "status", None),
                        filled_at=(getattr(order, "filled_at", None).isoformat() if getattr(order, "filled_at", None) else None),
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # 4) Optional polling to sync fills until terminal or timeout
        try:
            poll_total = int(os.getenv("CPZ_POLL_TOTAL_SECONDS", "60"))
            poll_interval = float(os.getenv("CPZ_POLL_INTERVAL_SECONDS", "2"))
            enable_poll = os.getenv("CPZ_ENABLE_FILL_POLLING", "true").lower() != "false"
            if enable_poll and poll_total > 0 and logging_mode != "disabled":
                deadline = time.time() + poll_total
                while time.time() < deadline:
                    cur = self._require_active().get_order(order.id)
                    if intent_id:
                        sb.update_order_record(
                            id=intent_id,
                            order_id=cur.id,
                            status=getattr(cur, "status", None),
                            filled_qty=getattr(cur, "filled_qty", None),
                            average_fill_price=getattr(cur, "average_fill_price", None),
                            submitted_at=(getattr(cur, "submitted_at", None).isoformat() if getattr(cur, "submitted_at", None) else None),
                            filled_at=(getattr(cur, "filled_at", None).isoformat() if getattr(cur, "filled_at", None) else None),
                        )
                    if str(getattr(cur, "status", "")).lower() in {"filled", "canceled", "partially_filled"}:
                        order = cur
                        break
                    time.sleep(poll_interval)
        except Exception:
            pass

        return order

    def get_order(self, order_id: str) -> Order:
        return self._require_active().get_order(order_id)

    def cancel_order(self, order_id: str) -> Order:
        return self._require_active().cancel_order(order_id)

    def replace_order(self, order_id: str, req: OrderReplaceRequest) -> Order:
        return self._require_active().replace_order(order_id, req)

    def stream_quotes(self, symbols: Iterable[str]) -> AsyncIterator[Quote]:
        active = self._require_active()
        return active.stream_quotes(symbols)
