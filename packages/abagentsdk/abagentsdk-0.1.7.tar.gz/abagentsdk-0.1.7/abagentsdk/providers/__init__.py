# abagent/providers/__init__.py
from __future__ import annotations

from .base import ModelProvider
from .gemini import GeminiProvider

# Optional catalog (don’t hard fail if missing in minimal installs)
try:
    from .gemini_catalog import (
        list_gemini_models,
        best_default,
        validate_or_suggest,
        tag_model,
    )
except Exception:  # pragma: no cover
    list_gemini_models = None  # type: ignore
    best_default = None        # type: ignore
    validate_or_suggest = None # type: ignore
    tag_model = None           # type: ignore

__all__ = [
    "ModelProvider",
    "GeminiProvider",
    "list_gemini_models",
    "best_default",
    "validate_or_suggest",
    "tag_model",
]
