"""Run matrix execution with a content-addressed cache.

    results/runs/<harness-hash>/<task-id>-<task-hash>/trial-<n>.json   scored record
                                                        trial-<n>.diff   what the agent changed
                                                        trial-<n>.log    raw agent output (redacted)

A record is reused whenever harness files, repo, prompt and hidden tests are unchanged, so
re-running `evaluate` never pays twice, and committed results re-render a report for $0.
Arms are interleaved (A1 B1 A2 B2 ...) so drift during the run (rate limits, provider
load, time of day) hits both arms equally instead of biasing one.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from harness_eval.agents import AgentResult, run_agent
from harness_eval.config import Harness, Suite, Task
from harness_eval.scorers import score_run
from harness_eval.workspace import CREDENTIALS, capture_diff, check_isolation, prepared_run


class ContaminationError(Exception):
    pass


class Runner:
    def __init__(self, suite: Suite, results: Path, max_cost: float | None = None,
                 offline: bool = False, log: Callable[[str], None] = print):
        self.suite = suite
        self.results = Path(results)
        self.max_cost = max_cost
        self.offline = offline
        self.log = log
        self.spent = 0.0
        self.missing: list[str] = []

    def record_path(self, harness: Harness, task: Task, trial: int) -> Path:
        return (self.results / "runs" / harness.hash / f"{task.id}-{self.suite.task_hash(task)}"
                / f"trial-{trial}.json")

    def collect(self, arms: dict[str, tuple[Harness, list[int]]]) -> dict[str, list[dict]]:
        """arms = {label: (harness, trial numbers)}. Returns {label: records}.
        A/A calibration is two labels on the same harness with disjoint trial numbers."""
        todo = [(h, t, n) for h, trials in arms.values() for t in self.suite.tasks for n in trials]
        real = [(h, t, n) for h, t, n in todo if h.agent != "replay"]  # replay never leaves the repo
        if not self.offline and any(not self.record_path(h, t, n).is_file() for h, t, n in real):
            check_isolation()
        out: dict[str, list[dict]] = {label: [] for label in arms}
        rounds = max(len(trials) for _, trials in arms.values())
        for task in self.suite.tasks:
            for i in range(rounds):
                for label, (harness, trials) in arms.items():
                    if i < len(trials) and (rec := self.get_or_run(harness, task, trials[i])):
                        out[label].append(rec)
        return out

    def get_or_run(self, harness: Harness, task: Task, trial: int) -> dict | None:
        path = self.record_path(harness, task, trial)
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        label = f"{harness.name}/{task.id}/trial-{trial}"
        if self.offline:
            self.missing.append(f"{label} (offline, not cached)")
            return None
        if self.max_cost is not None and self.spent >= self.max_cost:
            self.missing.append(f"{label} (budget ${self.max_cost:.2f} reached)")
            return None
        self.log(f"  run  {label} ...")
        rec = self._run_one(harness, task, trial, path)
        self.spent += rec["agent"].get("cost_usd") or 0.0
        s = rec.get("scores", {})
        self.log(f"       {rec['status']:<8} works={s.get('works', 0):.0f} "
                 f"intent={s.get('intent', 0):.2f} conv={s.get('conventions', 0):.2f} "
                 f"${rec['agent'].get('cost_usd') or 0:.3f} {rec['agent']['duration_s']:.0f}s")
        return rec

    def _run_one(self, harness: Harness, task: Task, trial: int, path: Path) -> dict:
        path.parent.mkdir(parents=True, exist_ok=True)
        log_path = path.with_suffix(".log")
        with prepared_run(self.suite, harness) as dirs:
            started = time.monotonic()
            try:
                agent = run_agent(harness, task, dirs.workspace, dirs.home, log_path)
            except Exception as e:  # missing CLI, crash in adapter: a failed run, not a crash
                agent = AgentResult(status="error", duration_s=round(time.monotonic() - started, 1),
                                    error=f"{type(e).__name__}: {e}")
            if problem := contamination(harness, agent):
                agent.status = "contaminated"
                agent.error = problem
            diff = capture_diff(dirs.workspace)
            scores = score_run(self.suite, task, dirs.workspace)
        _redact(log_path)
        path.with_suffix(".diff").write_text(diff, encoding="utf-8")
        rec = {
            "suite": self.suite.name,
            "harness": harness.name,
            "harness_hash": harness.hash,
            "agent_kind": harness.agent,
            "model": harness.model,
            "task": task.id,
            "task_hash": self.suite.task_hash(task),
            "trial": trial,
            "status": agent.status,
            "agent": agent.to_dict(),
            "scores": scores,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        if agent.status == "contaminated":
            raise ContaminationError(f"{harness.name}/{task.id}: {agent.error}")
        return rec


def contamination(harness: Harness, agent: AgentResult) -> str:
    """The agent loaded something that is not part of the harness under test."""
    if harness.agent != "claude" or not agent.loaded:
        return ""
    plugins = agent.loaded.get("plugins") or []
    if plugins:
        return f"plugins loaded from outside the harness: {plugins}"
    declared = set()
    mcp = harness.workspace_dir / ".mcp.json"
    if mcp.is_file():
        declared = set(json.loads(mcp.read_text(encoding="utf-8")).get("mcpServers", {}))
    servers = {s.get("name") for s in agent.loaded.get("mcp_servers") or [] if isinstance(s, dict)}
    if extra := servers - declared:
        return f"MCP servers loaded from outside the harness: {sorted(extra)}"
    return ""


def _redact(log: Path) -> None:
    """Agents can read their home dir; make sure no credential value survives in a log."""
    if not log.is_file():
        return
    secrets = set()
    for src, _ in CREDENTIALS.values():
        if src.is_file():
            try:
                _strings(json.loads(src.read_text(encoding="utf-8")), secrets)
            except (json.JSONDecodeError, OSError):
                pass
    text = log.read_text(encoding="utf-8", errors="replace")
    for s in secrets:
        text = text.replace(s, "[REDACTED]")
    log.write_text(text, encoding="utf-8")


def _strings(obj, acc: set[str]) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            _strings(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _strings(v, acc)
    elif isinstance(obj, str) and len(obj) >= 20:
        acc.add(obj)
