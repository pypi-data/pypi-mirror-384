# abagentsdk/core/handoffs.py
from __future__ import annotations

import asyncio
import inspect
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union, TYPE_CHECKING

from pydantic import BaseModel, Field, ValidationError

from .memory import Memory
from .tools import Tool

# ⚠️ Do NOT import Agent at runtime — prevents circular import with core.agent.
if TYPE_CHECKING:
    from .agent import Agent  # type hint only


HANDOFF_MARK_PREFIX = "<<<HANDOFF:"  # e.g. "<<<HANDOFF:Billing Agent>>>"

T = TypeVar("T")


@dataclass
class RunContextWrapper(Generic[T]):
    """Context given to callbacks and dynamic instructions."""
    current_agent: "Agent"   # forward string type
    target_agent: "Agent"
    memory: Memory
    steps: List[str]
    context: Optional[T] = None


class HandoffInputData(BaseModel):
    user_message: str = Field(default="Please take over from here.")
    history: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    return s.strip("_")


def _default_tool_name_for(agent_name: str) -> str:
    return f"transfer_to_{_slug(agent_name)}"


def _default_tool_desc_for(agent_name: str) -> str:
    return f"Handoff to the specialized agent '{agent_name}'. Use when this agent is better suited."


def _memory_to_history(memory: Memory) -> List[Dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in memory.load()]


class Handoff:
    """Configures a 'handoff tool' to transfer control to another Agent."""

    def __init__(
        self,
        *,
        agent: "Agent",
        tool_name_override: Optional[str] = None,
        tool_description_override: Optional[str] = None,
        on_handoff: Optional[Callable[..., Any]] = None,   # (ctx[, input_data])
        input_type: Optional[Type[BaseModel]] = None,
        input_filter: Optional[Callable[[HandoffInputData], HandoffInputData]] = None,
        is_enabled: Union[bool, Callable[[], bool]] = True,
    ) -> None:
        self.agent = agent
        self.tool_name = tool_name_override or _default_tool_name_for(agent.name)
        self.description = tool_description_override or _default_tool_desc_for(agent.name)
        self.on_handoff = on_handoff
        self.input_type = input_type
        self.input_filter = input_filter
        self.is_enabled = is_enabled

    def to_tool(self, current_agent: "Agent") -> Tool:
        input_schema = self.input_type

        class _HandoffTool(Tool):
            name = self.tool_name
            description = self.description
            schema = input_schema

            def run(inner_self, **kwargs) -> str:
                enabled = self.is_enabled() if callable(self.is_enabled) else self.is_enabled
                if not enabled:
                    return f"[Handoff Disabled] {self.tool_name}"

                if self.input_type is not None:
                    try:
                        input_obj = self.input_type(**kwargs)
                    except ValidationError as e:
                        return f"[Handoff Input Error] {e}"
                else:
                    input_obj = None  # type: ignore

                hid = HandoffInputData(
                    user_message=(kwargs.get("message") if "message" in kwargs else "Please take over from here."),
                    history=_memory_to_history(current_agent.memory),
                    metadata={"from_agent": current_agent.name, "to_agent": self.agent.name},
                )

                if self.input_filter:
                    try:
                        hid = self.input_filter(hid)
                    except Exception as e:
                        return f"[Handoff Filter Error] {e}"

                if self.on_handoff:
                    ctx = RunContextWrapper(
                        current_agent=current_agent,
                        target_agent=self.agent,
                        memory=current_agent.memory,
                        steps=[],
                        context=None,
                    )
                    try:
                        if input_obj is not None:
                            if inspect.iscoroutinefunction(self.on_handoff):
                                asyncio.run(self.on_handoff(ctx, input_obj))
                            else:
                                self.on_handoff(ctx, input_obj)
                        else:
                            if inspect.iscoroutinefunction(self.on_handoff):
                                asyncio.run(self.on_handoff(ctx))
                            else:
                                self.on_handoff(ctx)
                    except Exception as e:
                        return f"[Handoff Callback Error] {e}"

                start = (
                    f"Takeover reason/data:\n{input_obj.model_dump_json(indent=2)}"
                    if input_obj is not None
                    else hid.user_message
                )
                result = self.agent.run(start)

                marker = f"{HANDOFF_MARK_PREFIX}{self.agent.name}>>>"
                return f"{marker}\n{result.content}"

        return _HandoffTool()


def handoff(
    agent: "Agent",
    *,
    tool_name_override: Optional[str] = None,
    tool_description_override: Optional[str] = None,
    on_handoff: Optional[Callable[..., Any]] = None,
    input_type: Optional[Type[BaseModel]] = None,
    input_filter: Optional[Callable[[HandoffInputData], HandoffInputData]] = None,
    is_enabled: Union[bool, Callable[[], bool]] = True,
) -> Handoff:
    return Handoff(
        agent=agent,
        tool_name_override=tool_name_override,
        tool_description_override=tool_description_override,
        on_handoff=on_handoff,
        input_type=input_type,
        input_filter=input_filter,
        is_enabled=is_enabled,
    )
