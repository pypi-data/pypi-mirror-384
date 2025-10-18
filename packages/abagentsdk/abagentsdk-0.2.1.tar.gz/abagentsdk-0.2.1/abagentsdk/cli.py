# abagentsdk/cli.py
from __future__ import annotations
import os
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_SUPPRESS_LOGS"] = "1"
os.environ["GLOG_minloglevel"] = "3"

import argparse
import os
import runpy
import sys
from pathlib import Path

BANNER = "ABZ Agent SDK CLI"

TEMPLATE_AGENT = """\
from dotenv import load_dotenv
load_dotenv()  # reads GEMINI_API_KEY from .env or env
import os
from abagentsdk import Agent, Memory

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    agent = Agent(
        name={agent_name!r},
        instructions={instructions!r},
        model={model!r},
        memory=Memory(),
        api_key=GEMINI_API_KEY
    )
    response = agent.run("Hello, how are you?")
    print("Agent response:", response.content)

if __name__ == "__main__":
    main()
"""

TEMPLATE_ENV = "GEMINI_API_KEY={api_key}\n"


def _print_help_and_exit(parser: argparse.ArgumentParser, code: int = 0) -> int:
    parser.print_help()
    return code


def _cmd_run(file: str) -> int:
    path = Path(file)
    if not path.exists():
        print(f"File not found: {file}", file=sys.stderr)
        return 2
    # Execute as a script (__main__) so relative imports behave
    runpy.run_path(str(path), run_name="__main__")
    return 0


def _prompt_nonempty(prompt: str, default: str | None = None) -> str:
    try:
        val = input(prompt).strip()
    except EOFError:
        val = ""
    if not val and default is not None:
        return default
    return val


def _cmd_setup() -> int:
    print(f"{BANNER} — Project setup\n")

    # Ask minimal questions (don’t list models; just accept a string)
    api_key = _prompt_nonempty("Enter your GEMINI_API_KEY (leave blank to fill later): ", "")
    agent_name = _prompt_nonempty("Agent name [My Agent]: ", "My Agent")
    instructions = _prompt_nonempty("Agent instructions [Be helpful and concise.]: ", "Be helpful and concise.")
    model = _prompt_nonempty("Model id [gemini-2.0-flash]: ", "gemini-2.0-flash")
    filename = _prompt_nonempty("Starter file name [agent.py]: ", "agent.py")

    # Write .env (append or create)
    env_path = Path(".env")
    if api_key:
        existing = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
        lines = []
        if existing:
            for ln in existing.splitlines():
                if not ln.startswith("GEMINI_API_KEY="):
                    lines.append(ln)
        lines.append(TEMPLATE_ENV.format(api_key=api_key).strip())
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"✓ Wrote {env_path}")
    else:
        if not env_path.exists():
            env_path.write_text(TEMPLATE_ENV.format(api_key="YOUR_KEY_HERE"), encoding="utf-8")
            print(f"✓ Created {env_path} (fill in your key later)")

    # Write starter agent file
    agent_path = Path(filename)
    if agent_path.exists():
        print(f"⚠ {agent_path} already exists; not overwriting.")
    else:
        agent_code = TEMPLATE_AGENT.format(
            agent_name=agent_name,
            instructions=instructions,
            model=model,
        )
        agent_path.write_text(agent_code, encoding="utf-8")
        print(f"✓ Created {agent_path}")

    print(
        "\nNext steps:\n"
        "  1) Ensure your .env has GEMINI_API_KEY set (or set the env var in your shell)\n"
        f"  2) Run:  abagentsdk run {filename}\n"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="abagentsdk",
        description="ABZ Agent SDK CLI — run a script or scaffold a starter agent.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd")

    # abagentsdk run <file.py>
    p_run = sub.add_parser(
        "run",
        help="Run a Python file in a fresh __main__ module (like `python file.py`).",
    )
    p_run.add_argument("file", help="Python file to run")
    p_run.set_defaults(func=lambda args: _cmd_run(args.file))

    # abagentsdk setup
    p_setup = sub.add_parser(
        "setup",
        help="Interactive project setup: writes .env and a starter agent file.",
    )
    p_setup.set_defaults(func=lambda args: _cmd_setup())

    # If user runs with no subcommands, show help
    p.set_defaults(func=lambda args: _print_help_and_exit(p, 0))

    return p


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if not func:
        return _print_help_and_exit(parser, 0)
    return int(func(args) or 0)


if __name__ == "__main__":
    import sys
    sys.exit(main())
