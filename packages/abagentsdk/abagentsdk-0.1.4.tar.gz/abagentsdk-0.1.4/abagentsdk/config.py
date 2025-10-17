# abagent/config.py
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class SDKConfig:
    """
    Central runtime config for ABZ Agent SDK (Gemini-only).
    NOTE: The API key must be provided by the USER (never hardcode, never your key).
    """
    model: str = os.getenv("ABZ_GEMINI_MODEL", "models/gemini-1.5-pro")
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    temperature: float = float(os.getenv("ABZ_TEMPERATURE", "0.4"))
    max_iterations: int = int(os.getenv("ABZ_MAX_ITERS", "4"))
    verbose: bool = os.getenv("ABZ_VERBOSE", "1") == "1"

    def has_key(self) -> bool:
        return bool(self.api_key)

    def require_key(self) -> "SDKConfig":
        """
        Hard-fail unless the USER provided a key.
        Ways to provide:
          - export GEMINI_API_KEY in env (or .env via python-dotenv)
          - pass Agent(api_key="...") which overrides this field
        """
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Provide YOUR OWN Google Generative AI API key "
                "(environment variable or .env) or pass Agent(api_key='...')."
            )
        return self
