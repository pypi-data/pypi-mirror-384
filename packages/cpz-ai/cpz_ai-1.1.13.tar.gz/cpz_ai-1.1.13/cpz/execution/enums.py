from __future__ import annotations

from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    FOK = "FOK"
    IOC = "IOC"
