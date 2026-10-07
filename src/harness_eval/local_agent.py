"""Free local coding agent: CrewAI + an Ollama model + the workspace MCP server.

    echo "<task prompt>" | python -m harness_eval.local_agent --model ollama/qwen2.5:7b --workspace W

The harness reaches the agent the same way it reaches Claude Code or Codex: AGENTS.md in the
workspace becomes the agent's standing instructions. Prints one JSON line {"type": "result"}.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--max-iter", type=int, default=25)
    args = parser.parse_args()
    prompt = sys.stdin.read()
    ws = Path(args.workspace)
    result = {"type": "result", "prompt_tokens": 0, "completion_tokens": 0, "tool_calls": 0}
    try:
        result.update(_run(args.model, ws, prompt, args.max_iter))
    except Exception as e:  # report, don't crash: a failed run is data
        result["error"] = f"{type(e).__name__}: {e}"
    print(json.dumps(result), flush=True)


def _run(model: str, ws: Path, prompt: str, max_iter: int) -> dict:
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    from crewai import LLM, Agent, Crew, Task
    from crewai_tools import MCPServerAdapter
    from mcp import StdioServerParameters

    guide = ws / "AGENTS.md"
    instructions = guide.read_text(encoding="utf-8") if guide.is_file() else ""
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "harness_eval.mcp_server", "--root", str(ws)],
        env=dict(os.environ),
    )
    # Ollama's default 4k context silently truncates CrewAI's prompt + tool schemas + AGENTS.md
    # and the model then never calls a tool (found the hard way: 15 min, zero tool calls).
    # CrewAI talks to Ollama through an OpenAI-compatible client that rejects num_ctx, so the
    # context size is baked into the model instead (see README: *-16k Modelfiles).
    llm = LLM(model=model, base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
              temperature=0.2)
    with MCPServerAdapter(server) as tools:
        agent = Agent(
            role="Software engineer",
            goal="Implement the requested change in the repository so that it is correct and tested.",
            backstory="You work in this repository. Its AGENTS.md says:\n\n" + instructions,
            tools=list(tools), llm=llm, max_iter=max_iter, verbose=False,
        )
        task = Task(
            description=(prompt + "\n\nUse the tools to read the code, then write the full updated "
                         "file contents with write_file. Paths are relative to the repository root."),
            expected_output="A short summary of the files you changed.",
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        output = crew.kickoff()
        usage = crew.usage_metrics
        return {
            "output": str(output)[:2000],
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "tool_calls": getattr(usage, "successful_requests", 0) or 0,
            "tools": [t.name for t in tools],
        }


if __name__ == "__main__":
    main()
