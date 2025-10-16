from __future__ import annotations

import logging
from typing import Any, Mapping, MutableMapping

import structlog

REDACT_KEYS = {"authorization", "api_key", "apikey", "api_secret", "ALPACA_API_SECRET_KEY"}


def _redact_processor(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> Mapping[str, Any]:
    for k in list(event_dict.keys()):
        if k in REDACT_KEYS:
            event_dict[k] = "<redacted>"
    return event_dict


def get_logger() -> Any:
    level_name = logging.getLevelName(logging.getLogger().level)
    level_name = level_name if isinstance(level_name, str) else "INFO"
    level_num = getattr(logging, level_name, logging.INFO)
    structlog.configure(
        processors=[
            _redact_processor,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_num),
    )
    return structlog.get_logger()
