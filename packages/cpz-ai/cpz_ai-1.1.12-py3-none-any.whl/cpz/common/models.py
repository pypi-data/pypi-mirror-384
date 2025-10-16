from __future__ import annotations

from pydantic import BaseModel, Field


class Money(BaseModel):
    currency: str = Field(default="USD")
    amount: float


class Pagination(BaseModel):
    next_token: str | None = None
