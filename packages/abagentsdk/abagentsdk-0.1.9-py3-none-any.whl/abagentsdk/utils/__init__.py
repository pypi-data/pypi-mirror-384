# abagent/utils/__init__.py
from __future__ import annotations
import os

# Silence gRPC / Gemini warnings globally
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_SUPPRESS_LOGS"] = "1"
from .logging import log_step

__all__ = ["log_step"]
