"""Paired comparison of two arms (baseline A, candidate B) and the verdict.

Unit of analysis is the *task*: both arms ran the same tasks, so per-task differences
cancel out task difficulty. Uncertainty comes from a two-level bootstrap: resample tasks,
then resample trials inside each task and arm. That respects both sources of noise —
which tasks we happened to pick, and agent non-determinism on each task.

    per metric:  delta = mean_task( mean(B trials) - mean(A trials) ),  95% CI by bootstrap
    detected  :  CI excludes 0  AND  |delta| > A/A noise floor (if calibrated)

Verdict
    REGRESSION    a guardrail (works, intent) got worse, or something got worse and nothing better
    TRADE-OFF     something better and something non-guardrail worse (e.g. quality up, cost up)
    IMPROVEMENT   something better, nothing worse
    INCONCLUSIVE  nothing detected beyond noise
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# name, higher_is_better, guardrail, label
METRICS = [
    ("works", True, True, "Works (existing tests pass)"),
    ("intent", True, True, "Business intent (hidden acceptance tests)"),
    ("conventions", True, False, "Team conventions"),
    ("cost_usd", False, False, "Cost per task (USD)"),
    ("tokens", False, False, "Tokens per task"),
    ("duration_s", False, False, "Wall time per task (s)"),
]
QUALITY = {"works", "intent", "conventions"}
EXIT_CODES = {"IMPROVEMENT": 0, "REGRESSION": 1, "INCONCLUSIVE": 2, "TRADE-OFF": 3}
BOOTSTRAP_ITERS = 4000


@dataclass
class MetricResult:
    name: str
    label: str
    higher_is_better: bool
    guardrail: bool
    mean_a: float | None
    mean_b: float | None
    delta: float | None = None
    ci: tuple[float, float] | None = None
    noise_floor: float | None = None
    outcome: str = "n/a"  # better | worse | no change | n/a
    per_task: dict[str, float] = field(default_factory=dict)


@dataclass
class Comparison:
    metrics: list[MetricResult]
    verdict: str
    reasons: list[str]

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.verdict]

    def metric(self, name: str) -> MetricResult:
        return next(m for m in self.metrics if m.name == name)


def metric_value(record: dict, name: str) -> float | None:
    """A failed/timed-out run still counts: quality 0, its real cost and time."""
    if name in QUALITY:
        return float(record.get("scores", {}).get(name, 0.0)) if record["status"] == "ok" else 0.0
    agent = record.get("agent", {})
    if name == "tokens":
        return float(agent.get("input_tokens", 0) + agent.get("output_tokens", 0))
    value = agent.get(name)
    return None if value is None else float(value)


def compare(runs_a: list[dict], runs_b: list[dict], noise: dict[str, float] | None = None,
            seed: int = 7) -> Comparison:
    noise = noise or {}
    tasks = sorted({r["task"] for r in runs_a} & {r["task"] for r in runs_b})
    results = []
    for name, higher, guard, label in METRICS:
        a = _by_task(runs_a, name, tasks)
        b = _by_task(runs_b, name, tasks)
        usable = [t for t in tasks if a.get(t) and b.get(t)]
        m = MetricResult(name, label, higher, guard,
                         _mean([v for t in usable for v in a[t]]) if usable else None,
                         _mean([v for t in usable for v in b[t]]) if usable else None,
                         noise_floor=noise.get(name))
        if usable:
            m.per_task = {t: _mean(b[t]) - _mean(a[t]) for t in usable}
            m.delta = _mean(list(m.per_task.values()))
            m.ci = _bootstrap_ci({t: a[t] for t in usable}, {t: b[t] for t in usable}, seed)
            m.outcome = _outcome(m)
        results.append(m)
    verdict, reasons = _verdict(results)
    return Comparison(results, verdict, reasons)


def noise_floor(comparison: Comparison) -> dict[str, float]:
    """From an A/A comparison: the largest delta the tool produced with *no* real change."""
    return {m.name: max(abs(m.ci[0]), abs(m.ci[1])) for m in comparison.metrics if m.ci}


def _by_task(runs: list[dict], name: str, tasks: list[str]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {t: [] for t in tasks}
    for r in runs:
        if r["task"] in out and (v := metric_value(r, name)) is not None:
            out[r["task"]].append(v)
    return out


def _bootstrap_ci(a: dict[str, list[float]], b: dict[str, list[float]], seed: int,
                  level: float = 0.95) -> tuple[float, float]:
    rng = random.Random(seed)
    tasks = list(a)
    deltas = []
    for _ in range(BOOTSTRAP_ITERS):
        picked = rng.choices(tasks, k=len(tasks))
        deltas.append(_mean([_mean(rng.choices(b[t], k=len(b[t])))
                             - _mean(rng.choices(a[t], k=len(a[t]))) for t in picked]))
    deltas.sort()
    lo = deltas[int((1 - level) / 2 * len(deltas))]
    hi = deltas[int((1 + level) / 2 * len(deltas)) - 1]
    return (lo, hi)


def _outcome(m: MetricResult) -> str:
    lo, hi = m.ci
    if lo <= 0 <= hi:
        return "no change"
    if m.noise_floor is not None and abs(m.delta) <= m.noise_floor:
        return "no change"
    up = lo > 0
    return "better" if up == m.higher_is_better else "worse"


def _verdict(metrics: list[MetricResult]) -> tuple[str, list[str]]:
    better = [m for m in metrics if m.outcome == "better"]
    worse = [m for m in metrics if m.outcome == "worse"]
    reasons = [f"{m.label}: better" for m in better] + [f"{m.label}: worse" for m in worse]
    if any(m.guardrail for m in worse):
        return "REGRESSION", reasons
    if worse and not better:
        return "REGRESSION", reasons
    if better and worse:
        return "TRADE-OFF", reasons
    if better:
        return "IMPROVEMENT", reasons
    return "INCONCLUSIVE", ["no metric moved beyond its confidence interval / noise floor"]


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0
