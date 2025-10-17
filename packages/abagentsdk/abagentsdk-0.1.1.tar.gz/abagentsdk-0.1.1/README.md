# ABZ Agent SDK (Gemini‑only)

A lightweight, extensible **Agent SDK** for Python that makes it dead‑simple to build LLM agents on **Google Gemini**. It includes:

* 🔧 **Tools API** — subclass `Tool` *or* turn any Python function into a tool with `@function_tool`
* 🔀 **Handoffs** — delegate from one agent to another via transfer tools (e.g., `transfer_to_refund_agent`)
* 🧠 **Memory** — simple conversation buffer (swap for your own store at any time)
* ♻️ **ReAct loop** — reason → (tool?) → observe → finalize, with strict JSON tool calls
* 🧰 **Agent-as-a-Tool** — expose an Agent as a callable tool for orchestration
* 🧭 **Model selection** — `model="auto" | "choose" | "<exact>"` with optional validation

> **Scope**: This SDK is **Gemini‑only** by design. No OpenAI/Claude/DeepSeek here.

---

## Requirements

* Python **3.10+**
* A Google Generative AI API key in `GEMINI_API_KEY`

Core dependencies are installed automatically:

* `google-generativeai>=0.7.0`
* `pydantic>=2.6.0`
* `rich>=13.7.0`
* `python-dotenv>=1.0.1`
* `tzdata>=2024.1` *(Windows only)*

Optional:

* `griffe` for docstring parsing (nice metadata for function tools)
* `nest-asyncio` if you run async tools inside notebooks (existing event loop)

---

## Installation

```bash
pip install abagent
# or from source
pip install -e .
```

Extras:

```bash
pip install "abagent[docstrings]"          # enable docstring parsing for tools
pip install -e ".[docstrings,notebooks,dev]"  # full dev setup
```

Set your key:

```bash
# PowerShell
$env:GEMINI_API_KEY = "YOUR_KEY"
# bash/zsh
export GEMINI_API_KEY="YOUR_KEY"
```

---

## Quickstart

```python
from abagent.core.agent import Agent
from abagent.core.memory import Memory

agent = Agent(
    name="ABZ Helper",
    instructions="Answer briefly.",
    model="auto",      # lists models and picks a sensible default
    memory=Memory(),
)

print(agent.run("Say hi in 3 words.").content)
```

### Interactive chat

```python
from abagent.core.agent import Agent
from abagent.core.memory import Memory

agent = Agent(
    name="ABZ Chat",
    instructions="Be concise; use tools for math/time.",
    model="choose",  # prints models and lets you pick (TTY)
    memory=Memory(),
)

while True:
    q = input("You > ").strip()
    if q.lower() in {"q","quit","exit"}: break
    print("Agent >", agent.run(q).content, "\n")
```

---

## Tools

### Option A — Decorate a function (`@function_tool`)

```python
from typing import Optional, Union
import ast, operator as op
from abagent.core.tools import function_tool

ALLOWED = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
           ast.Pow: op.pow, ast.Mod: op.mod, ast.USub: op.neg, ast.UAdd: lambda x: x}

def _ev(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int,float)): return n.value
    if isinstance(n, ast.BinOp): return ALLOWED[type(n.op)](_ev(n.left), _ev(n.right))
    if isinstance(n, ast.UnaryOp): return ALLOWED[type(n.op)](_ev(n.operand))
    raise ValueError("Invalid expression")

@function_tool(name_override="calculator", description_override="Safely evaluate arithmetic.")
def calculator(expression: str) -> Union[int, float]:
    """Evaluate + - * / % ** with precedence."""
    return _ev(ast.parse(expression, mode="eval").body)
```

Register it:

```python
from abagent.core.agent import Agent
from abagent.core.memory import Memory
from tools_calculator import calculator

agent = Agent(
    name="ABZ Tools",
    instructions="Use calculator for math.",
    model="auto",
    tools=[calculator.as_tool],   # 👈 attach the tool instance
    memory=Memory(),
)
```

### Option B — Subclass `Tool`

```python
from pydantic import BaseModel
from abagent.core.tools import Tool

class SearchArgs(BaseModel):
    query: str
    top_k: int = 5

class SearchTool(Tool):
    name = "search"
    description = "Search a KB and return top results"
    schema = SearchArgs
    def __init__(self, kb): self.kb = kb
    def run(self, **kwargs) -> str:
        args = SearchArgs(**kwargs)
        return f"(demo) results for '{args.query}', k={args.top_k}"
```

### Matching model tool names

Gemini often guesses generic names like `calculator` or `clock`. Name your tools accordingly or rely on the SDK’s **tools manifest** (auto‑injected) to steer it.

---

## Handoffs (Agent → Agent)

Delegate to specialists via transfer tools.

```python
from abagent.core.agent import Agent
from abagent.core.memory import Memory
from abagent.core.handoffs import handoff
from abagent.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

refunds = Agent(
  name="Refund agent",
  instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
  Handle refunds; ask for order ID if missing.""",
  model="auto",
)

billing = Agent(
  name="Billing agent",
  instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
  Handle billing/invoice questions only.""",
  model="auto",
)

triage = Agent(
  name="Triage agent",
  instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
  Route to refunds/billing; else answer yourself.""",
  model="auto",
  handoffs=[refunds, handoff(billing)],  # Agent or Handoff
  memory=Memory(),
)

print(triage.run("I want a refund for order #ABZ-123").content)
```

**Customize** with `handoff(agent, on_handoff=..., input_type=..., input_filter=..., tool_name_override=...)`.

---

## Agent as a Tool (Orchestration)

Expose an Agent as a tool for another Agent to call.

```python
spanish = Agent(name="Spanish", instructions="Translate to Spanish", model="auto")
french  = Agent(name="French",  instructions="Translate to French",  model="auto")

orchestrator = Agent(
  name="Orchestrator",
  instructions="Use tools to translate as requested.",
  model="auto",
  tools=[
    spanish.as_tool(tool_name="translate_to_spanish", tool_description="Translate text to Spanish"),
    french.as_tool(tool_name="translate_to_french",   tool_description="Translate text to French"),
  ],
)

print(orchestrator.run("Say 'Hello' in Spanish.").content)
```

---

## Model Selection

* `model="auto"` (default): prints available Gemini models and auto‑picks a good default
* `model="choose"|"list"|"?"`: prints models and prompts you in a TTY
* `model="models/gemini-1.5-flash-8b-001"`: exact name; enable `validate_model=True` to catch typos

> Uses live listing if available, with static fallback for offline safety.

---

## Environment & Logging

Silence noisy gRPC/absl logs at the top of your script:

```python
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_LOG_SEVERITY_OVERRIDE"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ABSL_LOGGING_STDERR_THRESHOLD"] = "3"
```

---

## Testing

Install dev deps:

```bash
pip install -e ".[dev]"
pytest -q
```

Unit tests use a **Stub provider** to avoid API calls. See `tests/` for examples.

---

## FAQ

**Why Gemini‑only?**

> To keep the API tight and predictable. Other providers can be added later via a new provider module.

**Does the SDK stream tokens?**

> MVP returns full text. Add streaming in `providers/gemini.py` by enabling `stream=True` and plumbing a callback into `Agent`.

**Can I change memory?**

> Yes — replace `Memory` with your own class that implements the same methods.

---

## Contributing

PRs welcome! Please run `ruff`, `mypy`, and `pytest` before submitting.

---

## License

MIT © Abu Bakar
