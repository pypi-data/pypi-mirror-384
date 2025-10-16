from __future__ import annotations


class CPZError(Exception):
    """Base SDK error."""


class CPZBrokerError(CPZError):
    """Broker-specific error mapped into CPZ domain."""


class BrokerNotRegistered(CPZError):
    def __init__(self, name: str) -> None:
        super().__init__(
            f"Broker '{name}' is not registered. Call client.execution.use_broker(...) first or use a supported name (e.g., 'alpaca')."
        )


class InvalidStrategyId(CPZError):
    def __init__(self) -> None:
        super().__init__(
            "strategy_id is required for all orders. Provide OrderSubmitRequest.strategy_id (UUID/string)."
        )


class StrategyNotFound(CPZError):
    def __init__(self, strategy_id: str) -> None:
        super().__init__(
            f"Strategy '{strategy_id}' was not found or you do not have access. Create or share access in CPZ AI, then retry."
        )
