from __future__ import annotations

import os
from types import SimpleNamespace
from typing import AsyncIterator, Iterable

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest, ReplaceOrderRequest

from ..enums import OrderSide, OrderType, TimeInForce
from ..interfaces import BrokerAdapter
from ..models import (
    OrderSubmitRequest,
    OrderReplaceRequest,
    Order,
    Account,
    Position,
    Quote,
)
from .mapping import map_order_status
from ...common.cpz_ai import CPZAIClient
from ...common.logging import get_logger


def _mk_side(value: str):
    try:
        from alpaca.trading.enums import OrderSide as AlpacaSide  # type: ignore

        return AlpacaSide(value)
    except Exception:
        return SimpleNamespace(value=value)


def _mk_tif(value: str):
    try:
        from alpaca.trading.enums import TimeInForce as AlpacaTIF  # type: ignore

        return AlpacaTIF(value)
    except Exception:
        return SimpleNamespace(value=value)


class AlpacaAdapter(BrokerAdapter):
    def __init__(self, api_key_id: str, api_secret_key: str, env: str = "paper") -> None:
        paper = env == "paper"
        self._client = TradingClient(api_key_id, api_secret_key, paper=paper)

    @staticmethod
    def create(**kwargs: object) -> "AlpacaAdapter":
        logger = get_logger()
        # Prefer explicit kwargs
        api_key_id = str(kwargs.get("api_key_id") or "")
        api_secret_key = str(kwargs.get("api_secret_key") or "")
        # Prioritize account_id; env is secondary and ignored if account_id is provided
        env = str(kwargs.get("env") or kwargs.get("environment") or os.getenv("ALPACA_ENV", "paper"))
        account_id = str(kwargs.get("account_id") or "").strip() or None

        # Prefer CPZ AI-managed credentials FIRST when account_id is provided or CPZ keys are present
        use_cpz_first = True if account_id else bool(os.getenv("CPZ_AI_API_KEY") and (os.getenv("CPZ_AI_API_SECRET") or os.getenv("CPZ_AI_SECRET_KEY")))
        creds_used = ""
        if use_cpz_first:
            platform = CPZAIClient.from_env()
            creds = platform.get_broker_credentials("alpaca", env=None if account_id else env, account_id=account_id)
            if creds:
                api_key_id = creds.get("api_key_id", api_key_id)
                api_secret_key = creds.get("api_secret_key", api_secret_key)
                if creds.get("env"):
                    env = str(creds["env"]).lower()
                elif account_id and account_id.upper().startswith("PA"):
                    env = "paper"
                creds_used = "cpz"

        # Fallback to environment variables only if still missing
        if (not api_key_id or not api_secret_key) and not creds_used:
            api_key_id = api_key_id or os.getenv("ALPACA_API_KEY_ID", "")
            api_secret_key = api_secret_key or os.getenv("ALPACA_API_SECRET_KEY", "")

        # Log selected credentials (masked) for debugging account routing
        try:
            def _mask(val: str) -> str:
                return (val[:3] + "…" + val[-4:]) if val else ""
            logger.info(
                "alpaca_adapter_creds_selected",
                account_id=account_id or "",
                env=env,
                api_key_id=_mask(api_key_id),
            )
        except Exception:
            pass

        return AlpacaAdapter(api_key_id=api_key_id, api_secret_key=api_secret_key, env=env)

    def get_account(self) -> Account:
        acct = self._client.get_account()
        acct_id = str(getattr(acct, "id", ""))
        buying_power = float(getattr(acct, "buying_power", 0) or 0)
        equity = float(getattr(acct, "equity", 0) or 0)
        cash = float(getattr(acct, "cash", 0) or 0)
        return Account(id=acct_id, buying_power=buying_power, equity=equity, cash=cash)

    def get_positions(self) -> list[Position]:
        raw = self._client.get_all_positions()
        positions: list[Position] = []
        for p in raw:
            symbol = str(getattr(p, "symbol", ""))
            qty = float(getattr(p, "qty", 0) or 0)
            avg_entry_price = float(getattr(p, "avg_entry_price", 0) or 0)
            market_value = float(getattr(p, "market_value", 0) or 0)
            positions.append(
                Position(symbol=symbol, qty=qty, avg_entry_price=avg_entry_price, market_value=market_value)
            )
        return positions

    def submit_order(self, req: OrderSubmitRequest) -> Order:
        side_val = req.side.value  # already lowercase
        tif_val = req.time_in_force.value.lower()
        if req.type == OrderType.MARKET:
            order = self._client.submit_order(
                order_data=MarketOrderRequest(
                    symbol=req.symbol,
                    qty=req.qty,
                    side=_mk_side(side_val),
                    time_in_force=_mk_tif(tif_val),
                )
            )
        else:
            order = self._client.submit_order(
                order_data=LimitOrderRequest(
                    symbol=req.symbol,
                    qty=req.qty,
                    side=_mk_side(side_val),
                    time_in_force=_mk_tif(tif_val),
                    limit_price=req.limit_price,
                )
            )
        return self._map_order(order)

    def get_order(self, order_id: str) -> Order:
        order = self._client.get_order_by_id(order_id)
        return self._map_order(order)

    def cancel_order(self, order_id: str) -> Order:
        self._client.cancel_order_by_id(order_id)
        return self.get_order(order_id)

    def replace_order(self, order_id: str, req: OrderReplaceRequest) -> Order:
        a_req = ReplaceOrderRequest(qty=req.qty, limit_price=req.limit_price)
        order = self._client.replace_order_by_id(order_id=order_id, order_data=a_req)
        return self._map_order(order)

    def stream_quotes(self, symbols: Iterable[str]) -> AsyncIterator[Quote]:
        async def _gen() -> AsyncIterator[Quote]:
            for sym in symbols:
                yield Quote(symbol=sym, bid=0.0, ask=0.0)
                break
        return _gen()

    @staticmethod
    def _map_order(order_obj: object) -> Order:
        oid = str(getattr(order_obj, "id", ""))
        symbol = str(getattr(order_obj, "symbol", ""))
        side_val = getattr(getattr(order_obj, "side", None), "value", getattr(order_obj, "side", "buy"))
        type_val = getattr(getattr(order_obj, "type", None), "value", getattr(order_obj, "type", "market"))
        tif_val = getattr(
            getattr(order_obj, "time_in_force", None), "value", getattr(order_obj, "time_in_force", "DAY")
        )
        status_val = getattr(getattr(order_obj, "status", None), "value", getattr(order_obj, "status", ""))
        qty_val = getattr(order_obj, "qty", 0)

        # Optional execution fields, if present
        filled_qty = getattr(order_obj, "filled_qty", None)
        avg_fill_price = getattr(order_obj, "average_fill_price", None)
        submitted_at = getattr(order_obj, "submitted_at", None)
        filled_at = getattr(order_obj, "filled_at", None)

        return Order(
            id=oid,
            symbol=symbol,
            side=OrderSide(str(side_val).lower()),
            qty=float(qty_val or 0),
            type=OrderType(str(type_val).lower()),
            time_in_force=TimeInForce(str(tif_val).upper()),
            status=map_order_status(str(status_val)),
            filled_qty=float(filled_qty or 0) if filled_qty is not None else None,
            average_fill_price=float(avg_fill_price or 0) if avg_fill_price is not None else None,
            submitted_at=submitted_at,
            filled_at=filled_at,
        )
