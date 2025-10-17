# abagent/providers/gemini.py
from __future__ import annotations
import os as _os

# extra guard in case this file is imported directly
_os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
_os.environ.setdefault("GRPC_LOG_SEVERITY_OVERRIDE", "ERROR")
_os.environ.setdefault("ABSL_LOGGING_STDERR_THRESHOLD", "3")
_os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import google.generativeai as genai
from typing import Optional

from .base import ModelProvider
from ..config import SDKConfig


class GeminiProvider(ModelProvider):
    """
    Thin wrapper around google-generativeai. Requires a user-supplied API key.
    """

    def __init__(self, config: SDKConfig):
        self.config = config.require_key()  # enforce key
        genai.configure(api_key=self.config.api_key)

        self._model_name = self.config.model
        self._model: Optional[genai.GenerativeModel] = None

    @property
    def model(self) -> genai.GenerativeModel:
        if self._model is None or getattr(self._model, "model_name", None) != self._model_name:
            self._model = genai.GenerativeModel(self._model_name)
        return self._model

    def generate(self, prompt: str) -> str:
        resp = self.model.generate_content(prompt)
        return getattr(resp, "text", "") or ""
