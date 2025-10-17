# abagentsdk/__init__.py
"""
ABZ Agent SDK — Simplify building AI Agents with Google Gemini.

Public API:
    from abagentsdk import Agent, Memory, function_tool
"""

# ─────────────────────────────────────────────
# Silence gRPC / absl / TensorFlow warnings early
# ─────────────────────────────────────────────
try:
    from .utils.silence import install_silence
    install_silence()
except Exception:
    # Never block import due to silence hook
    pass


# ─────────────────────────────────────────────
# Core public imports
# ─────────────────────────────────────────────
from .core.agent import Agent, AgentResult
from .core.memory import Memory
from .core.tools import Tool, ToolCall, function_tool

# Optional: expose SDK config and provider
from .config import SDKConfig
from .providers.gemini import GeminiProvider


# ─────────────────────────────────────────────
# Metadata
# ─────────────────────────────────────────────
__all__ = [
    "Agent",
    "AgentResult",
    "Memory",
    "Tool",
    "ToolCall",
    "function_tool",
    "SDKConfig",
    "GeminiProvider",
]

__version__ = "0.8.9"
__author__ = "Abu Bakar"
__license__ = "MIT"

# ─────────────────────────────────────────────
# Friendly startup banner (optional)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"ABZ Agent SDK v{__version__} — Build AI Agents with Gemini")
