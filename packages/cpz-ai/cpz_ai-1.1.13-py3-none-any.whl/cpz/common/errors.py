from __future__ import annotations


class CPZError(Exception):
    """Base SDK error."""


class CPZBrokerError(CPZError):
    """Broker-specific error mapped into CPZ domain."""


class BrokerNotRegistered(CPZError):
    def __init__(self, name: str) -> None:
        super().__init__(
            f"Broker '{name}' is not registered. Register an adapter or use a supported name (e.g., 'alpaca')."
        )
