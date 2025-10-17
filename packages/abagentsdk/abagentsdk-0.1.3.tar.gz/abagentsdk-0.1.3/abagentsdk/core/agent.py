# abagentsdk/core/agent.py
from __future__ import annotations

import asyncio
import inspect
import json
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Type, Union

from pydantic import BaseModel, TypeAdapter, ValidationError

from .memory import Memory
from .tools import Tool, ToolCall, function_tool

# Optional imports guarded to avoid circulars if modules are absent during partial installs
try:
    from .handoffs import Handoff, handoff as handoff_factory, RunContextWrapper
except Exception:
    class RunContextWrapper:  # minimal fallback for type hints
        def __init__(self, current_agent=None, target_agent=None, memory=None, steps=None, context=None):
            self.current_agent = current_agent
            self.target_agent = target_agent
            self.memory = memory
            self.steps = steps or []
            self.context = context
    Handoff = None          # type: ignore
    def handoff_factory(agent):  # type: ignore
        raise RuntimeError("Handoffs are not available; module not found.")

try:
    from .guardrails import run_input_guardrails, run_output_guardrails
except Exception:
    def run_input_guardrails(*args, **kwargs):  # type: ignore
        return None
    def run_output_guardrails(*args, **kwargs):  # type: ignore
        return None

from ..config import SDKConfig
from ..providers.gemini import GeminiProvider


BASE_SYSTEM_PROMPT = (
    "You are the ABZ Agent SDK runtime.\n"
    "When you need a TOOL, output ONLY a single JSON object on ONE line, with NO markdown/backticks/extra text:\n"
    '{"tool":"<name>","args":{...}}\n'
    "When replying to the user, DO NOT include any tool JSON—reply only with the final answer text.\n"
    "Use ONLY tool names exactly as given in the tools manifest."
)

InstructionsFn = Callable[[RunContextWrapper, "Agent"], Union[str, Awaitable[str]]]


class AgentResult:
    def __init__(self, content: str, steps: List[str], parsed: Any = None):
        self.content = content
        self.steps = steps
        self.parsed = parsed


class Agent:
    """
    Gemini-only Agent with tools, handoffs, memory, optional structured outputs,
    guardrails, and dynamic instructions.

    Required:
      - name: str
      - instructions: str | (ctx, agent) -> str | awaitable str
    """

    def __init__(
        self,
        *,
        name: str,
        instructions: Union[str, InstructionsFn],
        model: Optional[str] = "auto",
        tools: Optional[List[Union[Tool, Callable[..., Any]]]] = None,
        handoffs: Optional[List[Union["Agent", Handoff]]] = None,
        memory: Optional[Memory] = None,
        verbose: bool = False,            # quiet by default
        max_iterations: int = 4,
        api_key: Optional[str] = None,    # user supplies via env or here
        validate_model: bool = False,
        include_experimental: bool = True,
        output_type: Optional[Type[Any]] = None,
        input_guardrails: Optional[Sequence[Any]] = None,
        output_guardrails: Optional[Sequence[Any]] = None,
    ) -> None:
        if not name:
            raise ValueError("Agent 'name' is required.")
        if instructions is None or (isinstance(instructions, str) and instructions.strip() == ""):
            raise ValueError("Agent 'instructions' is required (string or function).")

        self.name = name
        self._instructions_src: Union[str, InstructionsFn] = instructions
        self.instructions: str = ""  # filled each run
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.memory = memory or Memory()

        # Structured output setup (optional)
        self.output_type: Optional[Type[Any]] = output_type
        self._type_adapter: Optional[TypeAdapter[Any]] = (
            TypeAdapter(output_type) if output_type is not None else None
        )

        # Guardrails (optional)
        self.input_guardrails = list(input_guardrails or [])
        self.output_guardrails = list(output_guardrails or [])

        # Model select (Gemini only)
        self.model = self._resolve_model_param(
            model=model,
            include_experimental=include_experimental,
            validate_model=validate_model,
        )

        # ----- Tools: normalize & index (accept Tool objects OR plain callables) -----
        self.tools = self._normalize_and_index_tools(tools or [])

        # ----- Handoffs → tools -----
        self._handoffs: List[Handoff] = []
        for item in (handoffs or []):
            if Handoff is not None and isinstance(item, Handoff):  # type: ignore
                self._handoffs.append(item)
            else:
                self._handoffs.append(handoff_factory(agent=item))  # type: ignore
        for h in self._handoffs:
            ht = h.to_tool(self)  # type: ignore[attr-defined]
            self.tools[ht.name] = ht

        # ----- Provider / key resolution -----
        cfg_env = SDKConfig()  # reads env/.env
        resolved_key = api_key or cfg_env.api_key
        if not resolved_key:
            raise RuntimeError(
                "GEMINI_API_KEY is Missing — set your API key in environment variables or .env"
            )
        cfg = SDKConfig(
            model=self.model,
            api_key=resolved_key,
            temperature=cfg_env.temperature,
            max_iterations=self.max_iterations,
            verbose=self.verbose,
        )
        self.provider = GeminiProvider(cfg)

    # ---------- Public API ----------

    def register_tool(self, tool: Union[Tool, Callable[..., Any]]) -> None:
        t = self._coerce_tool(tool, idx=-1)
        self.tools[t.name] = t

    class _AgentInvokeSchema(BaseModel):
        message: str

    def as_tool(self, *, tool_name: str, tool_description: str) -> Tool:
        outer = self

        class _AgentTool(Tool):
            name = tool_name
            description = tool_description
            schema = Agent._AgentInvokeSchema

            def run(self, **kwargs) -> str:
                msg = kwargs.get("message", "Please take over from here.")
                return outer.run(msg).content

        return _AgentTool()

    def run(self, user_message: str, *, context: Any = None) -> AgentResult:
        steps: List[str] = []

        ctx_for_run = RunContextWrapper(
            current_agent=self,
            target_agent=self,
            memory=self.memory,
            steps=steps,
            context=context,
        )

        # Input guardrails (if any)
        if self.input_guardrails:
            run_input_guardrails(
                guards=self.input_guardrails,
                ctx=ctx_for_run,
                agent=self,
                user_input=user_message,
            )

        # Remember user
        self.memory.remember("user", user_message)

        for _i in range(self.max_iterations):
            effective_instructions = self._resolve_instructions(ctx_for_run)
            prompt = self._build_prompt(
                user_message if _i == 0 else "Continue.",
                effective_instructions=effective_instructions,
            )

            model_out = self.provider.generate(prompt)
            steps.append(model_out)

            # Tool call?
            tool_call = self._maybe_parse_toolcall(model_out)
            if tool_call:
                observation = self._execute_tool(tool_call)
                self.memory.remember("assistant", model_out)
                self.memory.remember("tool", observation)
                if self.verbose:
                    print(f"[Tool {tool_call.tool}] {observation}")

                # CRITICAL: force next turn to use the tool result and produce final text
                user_message = (
                    "Use the TOOL RESULT below to answer the user's original request.\n\n"
                    f"TOOL RESULT ({tool_call.tool}): {observation}\n\n"
                    "Now reply with the final answer ONLY — no JSON, no tool calls, no code fences."
                )
                continue  # iterate again with updated user_message

            # Final answer (no tool)
            self.memory.remember("assistant", model_out)

            # Plain text
            if self._type_adapter is None:
                if self.output_guardrails:
                    run_output_guardrails(
                        guards=self.output_guardrails,
                        ctx=ctx_for_run,
                        agent=self,
                        final_output=model_out,
                    )
                return AgentResult(content=model_out, steps=steps)

            # Structured output
            parsed = self._coerce_to_output_type(model_out)
            if self.output_guardrails:
                run_output_guardrails(
                    guards=self.output_guardrails,
                    ctx=ctx_for_run,
                    agent=self,
                    final_output=parsed,
                )
            return AgentResult(content=model_out, steps=steps, parsed=parsed)

        fallback = (
            "Reached iteration limit without final answer. Here's the latest output:\n\n"
            + (steps[-1] if steps else "")
        )
        return AgentResult(content=fallback, steps=steps)

    # ---------- Internals ----------

    def _normalize_and_index_tools(self, tools_in: List[Union[Tool, Callable[..., Any]]]) -> Dict[str, Tool]:
        """Accept Tool instances, decorated functions, or plain callables; always return a name→Tool dict."""
        def _bad_kind(x: Any) -> Optional[str]:
            if isinstance(x, str):
                return "str"
            if inspect.ismodule(x):
                return "module"
            if inspect.isclass(x):
                return "class"
            return None

        tools_dict: Dict[str, Tool] = {}

        for idx, raw in enumerate(tools_in):
            # Already a Tool?
            if isinstance(raw, Tool):
                name = getattr(raw, "name", None) or f"tool_{idx}"
                tools_dict[name] = raw
                continue

            # Obvious wrong types
            bad = _bad_kind(raw)
            if bad:
                raise TypeError(
                    f"tools[{idx}] is a {bad}. Pass a Tool instance or a function, not {bad}."
                )

            # Plain callable → wrap via function_tool()
            if callable(raw):
                try:
                    wrapped = function_tool()(raw)  # decorator factory → Tool
                    name = getattr(wrapped, "name", None) or getattr(raw, "__name__", f"tool_{idx}")
                    tools_dict[name] = wrapped
                    continue
                except Exception:
                    # Last resort: minimal wrapper so we NEVER crash here
                    fn_name = getattr(raw, "__name__", f"tool_{idx}")

                    class _FallbackTool(Tool):
                        name: str = fn_name
                        description: str = f"Auto-wrapped tool for callable {fn_name}"
                        schema = None

                        def run(self, **kwargs) -> str:
                            try:
                                out = raw(**kwargs)
                                return out if isinstance(out, str) else str(out)
                            except Exception as e:
                                return f"[Tool Error] {e}"

                    tools_dict[_FallbackTool.name] = _FallbackTool()
                    continue

            # Not supported
            raise TypeError(
                f"tools[{idx}] has unsupported type {type(raw).__name__}. "
                "Pass a Tool instance or a callable."
            )

        return tools_dict

    def _resolve_instructions(self, ctx: RunContextWrapper) -> str:
        src = self._instructions_src
        if isinstance(src, str):
            self.instructions = src
            return src
        fn = src
        try:
            if inspect.iscoroutinefunction(fn):
                try:
                    return asyncio.run(fn(ctx, self))
                except RuntimeError:
                    import nest_asyncio  # type: ignore
                    nest_asyncio.apply()
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(fn(ctx, self))
            else:
                text = fn(ctx, self)
                if not isinstance(text, str) or text.strip() == "":
                    raise ValueError("Dynamic instructions function must return a non-empty string.")
                self.instructions = text
                return text
        except Exception as e:
            raise RuntimeError(f"Dynamic instructions function raised: {e}") from e

    def _output_schema_json(self) -> Optional[str]:
        if self._type_adapter is None:
            return None
        try:
            schema = self._type_adapter.json_schema()
            return json.dumps(schema, ensure_ascii=False)
        except Exception:
            return None

    def _coerce_to_output_type(self, text: str) -> Any:
        assert self._type_adapter is not None
        # First try: direct JSON
        try:
            return self._type_adapter.validate_json(text)
        except Exception:
            pass
        # Second: extract JSON blob
        blob = _extract_json_blob(text)
        if blob is not None:
            try:
                return self._type_adapter.validate_json(blob)
            except ValidationError as ve:
                preview = blob[:400]
                raise ValueError(
                    f"Structured output validation failed.\n"
                    f"Expected schema: {self._short_schema_hint()}\n"
                    f"Got (truncated): {preview}\n\n{ve}"
                ) from ve
        preview = text[:400]
        raise ValueError(
            "Model did not return valid JSON for the requested output_type.\n"
            f"Expected schema: {self._short_schema_hint()}\n"
            f"Raw (truncated): {preview}"
        )

    def _short_schema_hint(self) -> str:
        js = self._output_schema_json()
        return (js[:240] + "…") if js and len(js) > 240 else (js or "<unknown>")

    def _resolve_model_param(
        self,
        *,
        model: Optional[str],
        include_experimental: bool,
        validate_model: bool,
    ) -> str:
        # Keep simple and stable: explicit string or default
        if not model or str(model).strip().lower() == "auto":
            return "gemini-2.0-flash"
        return str(model)

    def _execute_tool(self, call: ToolCall) -> str:
        tool = self.tools.get(call.tool)
        if not tool:
            return f"[Tool Error] Unknown tool: {call.tool}"
        try:
            kwargs = tool.parse_args(call.args)
            if hasattr(tool, "_invoke_with_ctx"):
                ctx = RunContextWrapper(current_agent=self, target_agent=self, memory=self.memory, steps=[])
                return tool._invoke_with_ctx(ctx, **kwargs)  # type: ignore[attr-defined]
            return tool.run(**kwargs)
        except Exception as e:
            return f"[Tool Error] {e}"

    def _build_prompt(self, user_message: str, *, effective_instructions: str) -> str:
        system = (
            f"{BASE_SYSTEM_PROMPT}\n\n"
            f"[AGENT NAME]: {self.name}\n"
            f"[INSTRUCTIONS]: {effective_instructions}\n"
            f"[MODEL]: {self.model}\n"
        )

        if self.tools:
            manifest_lines = ["Available TOOLS (use JSON with these exact names):"]
            for name, tool in self.tools.items():
                desc = (tool.description or "").strip().replace("\n", " ")
                manifest_lines.append(f"- {name}: {desc}")
            system += "\n" + "\n".join(manifest_lines)

        if self._type_adapter is not None:
            schema_json = self._output_schema_json()
            system += (
                "\n\n[STRUCTURED OUTPUT]:\n"
                "Return ONLY valid JSON for the final answer (no markdown, no prose).\n"
            )
            if schema_json:
                system += f"Target JSON schema (informative):\n{schema_json}\n"
            system += "If you cannot fully satisfy the schema, return your best-effort JSON matching the schema keys.\n"

        prefix = f"[SYSTEM]: {system}\n\n"
        history = self.memory.to_prompt()
        user_tail = user_message if self._type_adapter is None else (user_message + "\n\nReturn ONLY the final JSON.")
        return prefix + history + ("\n\n[USER]: " + user_tail)

    def _maybe_parse_toolcall(self, text: str) -> Optional[ToolCall]:
        # Try to find a JSON blob anywhere (handles code fences & prose)
        blob = _extract_json_blob(text.strip())
        if not blob:
            # fallback: if text is already pure JSON
            s = text.strip()
            if s.startswith("{") and s.endswith("}"):
                blob = s
        if not blob:
            return None
        try:
            data = json.loads(blob)
            if isinstance(data, dict) and "tool" in data:
                args = data.get("args") or {}
                if not isinstance(args, dict):
                    args = {}
                return ToolCall(tool=str(data["tool"]), args=args)
        except Exception:
            return None
        return None


# ---------- helpers ----------
_JSON_OBJECT_OR_ARRAY = re.compile(r"(\{.*\}|\[.*\])", re.DOTALL)

def _extract_json_blob(text: str) -> Optional[str]:
    m = _JSON_OBJECT_OR_ARRAY.search(text.strip())
    if not m:
        return None
    return m.group(1)
