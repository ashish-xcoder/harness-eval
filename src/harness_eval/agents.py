"""Agent adapters. Each one runs a single task in a prepared workspace and reports what it
cost. All adapters return the same AgentResult so scoring and stats never care which
agent produced the code.

    claude  -> `claude -p --output-format stream-json`   cost from the CLI itself
    codex   -> `codex exec --json`                       tokens from turn.completed, cost from PRICES
    crewai  -> harness_eval.local_agent (CrewAI + Ollama + workspace MCP server), free
    replay  -> copies canned files from the harness; deterministic, used by the test suite
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from harness_eval.config import Harness, Task
from harness_eval.workspace import agent_env

# USD per million tokens (input, cached input, output) for agents that do not report cost.
# ponytail: hand-maintained table; unknown models report tokens with cost=None.
PRICES = {
    "gpt-5": (1.25, 0.125, 10.0),
    "gpt-5-mini": (0.25, 0.025, 2.0),
    "gpt-5-codex": (1.25, 0.125, 10.0),
}


@dataclass
class AgentResult:
    status: str  # ok | error | timeout | contaminated
    duration_s: float
    cost_usd: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    turns: int = 0
    message: str = ""
    error: str = ""
    loaded: dict = field(default_factory=dict)  # what the agent reports it loaded (tools, MCP, plugins)

    def to_dict(self) -> dict:
        return asdict(self)


def run_agent(harness: Harness, task: Task, workspace: Path, home: Path, log: Path) -> AgentResult:
    runner = {"claude": _claude, "codex": _codex, "crewai": _crewai, "replay": _replay}[harness.agent]
    return runner(harness, task, workspace, home, log)


def _claude(harness: Harness, task: Task, ws: Path, home: Path, log: Path) -> AgentResult:
    cmd = [
        _which("claude"), "-p",
        "--output-format", "stream-json", "--verbose",
        "--max-turns", str(harness.max_turns),
        "--dangerously-skip-permissions",  # unattended run inside a throwaway workspace
        *(["--model", harness.model] if harness.model else []),
        *harness.extra_args,
    ]
    started = time.monotonic()
    code, out, err = _run(cmd, task.prompt, ws, agent_env(home), harness.timeout_s, log)
    res = AgentResult(status="ok", duration_s=round(time.monotonic() - started, 1))
    events = _jsonl(out)
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    res.loaded = {k: init.get(k) for k in ("model", "mcp_servers", "plugins", "skills", "slash_commands")}
    final = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if code == "timeout":
        res.status = "timeout"
    if final:
        usage = final.get("usage") or {}
        res.cost_usd = final.get("total_cost_usd")
        res.input_tokens = sum(usage.get(k) or 0 for k in (
            "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        res.output_tokens = usage.get("output_tokens") or 0
        res.turns = final.get("num_turns") or 0
        res.message = str(final.get("result") or "")[:2000]
        if final.get("is_error") and res.status == "ok":
            res.status, res.error = "error", f"{final.get('subtype')}: {res.message[:300]}"
    elif res.status == "ok":
        res.status, res.error = "error", (err or out)[-1000:]
    return res


def _codex(harness: Harness, task: Task, ws: Path, home: Path, log: Path) -> AgentResult:
    cmd = [
        _which("codex"), "exec", "--json", "--skip-git-repo-check",
        "--sandbox", "workspace-write",
        *(["--model", harness.model] if harness.model else []),
        *harness.extra_args, "-",
    ]
    started = time.monotonic()
    code, out, err = _run(cmd, task.prompt, ws, agent_env(home), harness.timeout_s, log)
    res = AgentResult(status="ok", duration_s=round(time.monotonic() - started, 1))
    events = _jsonl(out)
    cached = 0
    for e in events:
        if e.get("type") == "turn.completed":
            u = e.get("usage") or {}
            res.input_tokens += u.get("input_tokens") or 0
            cached += u.get("cached_input_tokens") or 0
            res.output_tokens += u.get("output_tokens") or 0
        elif e.get("type") == "item.completed":
            item = e.get("item") or {}
            if item.get("type") in ("command_execution", "file_change", "mcp_tool_call"):
                res.turns += 1
            elif item.get("type") == "agent_message":
                res.message = str(item.get("text") or "")[:2000]
        elif e.get("type") in ("turn.failed", "error"):
            res.status, res.error = "error", json.dumps(e)[:1000]
    if price := PRICES.get(harness.model or ""):
        fresh = res.input_tokens - cached
        res.cost_usd = round((fresh * price[0] + cached * price[1] + res.output_tokens * price[2]) / 1e6, 6)
    if code == "timeout":
        res.status = "timeout"
    elif not any(e.get("type") == "turn.completed" for e in events) and res.status == "ok":
        res.status, res.error = "error", (err or out)[-1000:]
    return res


def _crewai(harness: Harness, task: Task, ws: Path, home: Path, log: Path) -> AgentResult:
    cmd = [
        sys.executable, "-m", "harness_eval.local_agent",
        "--model", harness.model or "ollama/qwen2.5:7b",
        "--workspace", str(ws), "--max-iter", str(harness.max_turns),
    ]
    env = agent_env(home)
    # CrewAI resolves its storage dir via appdirs -> SHGetFolderPath, which fails under a
    # private USERPROFILE with no AppData; give it private AppData dirs too.
    for var, sub in (("APPDATA", "Roaming"), ("LOCALAPPDATA", "Local")):
        (home / "AppData" / sub).mkdir(parents=True, exist_ok=True)
        env[var] = str(home / "AppData" / sub)
    started = time.monotonic()
    code, out, err = _run(cmd, task.prompt, ws, env, harness.timeout_s, log)
    res = AgentResult(status="ok", duration_s=round(time.monotonic() - started, 1), cost_usd=0.0)
    summary = next((e for e in reversed(_jsonl(out)) if e.get("type") == "result"), None)
    if code == "timeout":
        res.status = "timeout"
    if summary:
        res.input_tokens = summary.get("prompt_tokens", 0)
        res.output_tokens = summary.get("completion_tokens", 0)
        res.turns = summary.get("tool_calls", 0)
        res.message = str(summary.get("output", ""))[:2000]
        res.loaded = {"mcp_servers": summary.get("tools", [])}
        if summary.get("error") and res.status == "ok":
            res.status, res.error = "error", summary["error"][:1000]
    elif res.status == "ok":
        res.status, res.error = "error", (err or out)[-1000:]
    return res


def _replay(harness: Harness, task: Task, ws: Path, home: Path, log: Path) -> AgentResult:
    """Copy harness/replay/<task-id>/ over the workspace. Lets the test suite drive the
    whole pipeline with known-good, known-bad and test-tampering 'agents' for free."""
    src = harness.root / "replay" / task.id
    if src.is_dir():
        shutil.copytree(src, ws, dirs_exist_ok=True)
    for rel in harness.settings.get("delete", {}).get(task.id, []):
        (ws / rel).unlink(missing_ok=True)
    cost = harness.settings.get("cost_usd", 0.0)
    log.write_text("replay\n", encoding="utf-8")
    return AgentResult(status="ok", duration_s=0.0, cost_usd=cost, input_tokens=1000,
                       output_tokens=100, turns=1, message="replayed")


def _run(cmd: list[str], stdin: str, cwd: Path, env: dict, timeout: int, log: Path):
    """Run with the prompt on stdin (no prompt in argv: cmd.exe mangles quotes/newlines in
    .cmd shims). On timeout kill the whole process tree, not just the shim."""
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    proc = subprocess.Popen(
        cmd, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
        creationflags=flags, start_new_session=sys.platform != "win32",
    )
    try:
        out, err = proc.communicate(stdin, timeout=timeout)
        code: int | str = proc.returncode
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        out, err = proc.communicate()
        code = "timeout"
    log.write_text(out + "\n--- stderr ---\n" + err, encoding="utf-8")
    return code, out, err


def _kill_tree(proc: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        os.killpg(proc.pid, signal.SIGKILL)


def _jsonl(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def _which(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise FileNotFoundError(f"`{name}` CLI not found on PATH")
    return path
