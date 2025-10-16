from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from dotenv import load_dotenv


@dataclass
class Config:
    env: str
    log_level: str
    request_timeout_seconds: int
    cpz_ai_url: str
    cpz_ai_api_key: str
    cpz_ai_secret_key: str

    @staticmethod
    def from_env(environ: Mapping[str, str]) -> "Config":
        load_dotenv()  # load from .env if present
        env = environ.get("CPZ_ENV", "dev")
        log_level = environ.get("CPZ_LOG_LEVEL", "INFO")
        timeout = int(environ.get("CPZ_REQUEST_TIMEOUT_SECONDS", "30"))
        cpz_ai_url = environ.get("CPZ_AI_URL", "https://api-ai.cpz-lab.com/cpz")
        cpz_ai_api_key = environ.get("CPZ_AI_API_KEY", "")
        cpz_ai_secret_key = environ.get("CPZ_AI_API_SECRET", "")
        return Config(
            env=env, 
            log_level=log_level, 
            request_timeout_seconds=timeout,
            cpz_ai_url=cpz_ai_url,
            cpz_ai_api_key=cpz_ai_api_key,
            cpz_ai_secret_key=cpz_ai_secret_key
        )
