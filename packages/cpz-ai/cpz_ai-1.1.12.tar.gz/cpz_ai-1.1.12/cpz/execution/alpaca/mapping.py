from __future__ import annotations

from ..enums import OrderSide, OrderType, TimeInForce


def map_side_from_alpaca(value: str) -> OrderSide:
    return OrderSide(value.lower())


def map_type_from_alpaca(value: str) -> OrderType:
    return OrderType(value.lower())


def map_tif_from_alpaca(value: str) -> TimeInForce:
    return TimeInForce(value.upper())


def map_order_status(value: str) -> str:
    return value
