from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator, AliasChoices

from .enums import OrderSide, OrderType, TimeInForce


class OrderSubmitRequest(BaseModel):
    symbol: str
    side: OrderSide
    qty: float
    # Accept either "order_type" or legacy "type" at input; serialize as "type"
    order_type: OrderType = Field(
        validation_alias=AliasChoices("order_type", "type"),
        serialization_alias="type",
    )
    time_in_force: TimeInForce
    limit_price: Optional[float] = None
    # Strategy identifier is required for all orders
    strategy_id: str

    # Backwards-compatibility: expose `.type` like before
    @property
    def type(self) -> OrderType:  # pragma: no cover - simple alias
        return self.order_type

    @model_validator(mode="after")
    def _validate_limit_price(self) -> "OrderSubmitRequest":
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price required for limit orders")
        return self


class OrderReplaceRequest(BaseModel):
    qty: Optional[float] = None
    limit_price: Optional[float] = None


class Order(BaseModel):
    id: str
    symbol: str
    side: OrderSide
    qty: float
    type: OrderType
    time_in_force: TimeInForce
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Optional broker execution details (populated when available)
    filled_qty: float | None = None
    average_fill_price: float | None = None
    submitted_at: datetime | None = None
    filled_at: datetime | None = None


class Account(BaseModel):
    id: str
    buying_power: float
    equity: float
    cash: float


class Position(BaseModel):
    symbol: str
    qty: float
    avg_entry_price: float
    market_value: float


class Quote(BaseModel):
    symbol: str
    bid: float
    ask: float
    bid_size: float = 0
    ask_size: float = 0
    ts: datetime = Field(default_factory=datetime.utcnow)


class Bar(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    ts: datetime = Field(default_factory=datetime.utcnow)
