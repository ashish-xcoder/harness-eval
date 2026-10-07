"""harness-eval CLI.

    harness-eval evaluate  SUITE --baseline DIR --candidate DIR   -> report + exit code
    harness-eval calibrate SUITE --harness DIR                    -> A/A noise floor

Exit codes for CI gating: 0 IMPROVEMENT, 1 REGRESSION, 2 INCONCLUSIVE, 3 TRADE-OFF.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from harness_eval import report, stats
from harness_eval.config import ConfigError, load_harness, load_suite
from harness_eval.runner import ContaminationError, Runner
from harness_eval.workspace import IsolationError

app = typer.Typer(add_completion=False, no_args_is_help=True,
                  help="Did this harness change make the coding agent's code better or worse?")

SuiteArg = typer.Argument(..., help="Suite directory or suite.yaml")
ResultsOpt = typer.Option(None, help="Run cache + reports (default: <suite>/results)")
TrialsOpt = typer.Option(3, min=1, help="Trials per task per arm")
CostOpt = typer.Option(None, help="Stop starting new runs once this much USD was spent")
OfflineOpt = typer.Option(False, help="Never run agents; use cached results only ($0)")


@app.command()
def evaluate(
    suite_path: Path = SuiteArg,
    baseline: Path = typer.Option(..., help="Harness directory currently in use"),
    candidate: Path = typer.Option(..., help="Harness directory with the change"),
    trials: int = TrialsOpt,
    results: Path = ResultsOpt,
    max_cost: float = CostOpt,
    offline: bool = OfflineOpt,
) -> None:
    """Run (or reuse) baseline and candidate on every task, compare, write the report."""
    suite, a, b = _load(suite_path, baseline, candidate)
    results = results or suite.root / "results"
    calibration = _read_json(results / f"calibration-{a.hash}.json")
    runner = Runner(suite, results, max_cost=max_cost, offline=offline, log=typer.echo)
    typer.echo(f"evaluate {suite.name}: {a.name} ({a.hash}) vs {b.name} ({b.hash}), "
               f"{len(suite.tasks)} tasks x {trials} trials")
    runs = _collect(runner, {"baseline": (a, list(range(trials))),
                             "candidate": (b, list(range(trials)))})
    if calibration and calibration.get("trials") != trials:
        typer.echo(f"note: calibration used {calibration.get('trials')} trials, this run {trials}")
    cmp = stats.compare(runs["baseline"], runs["candidate"],
                        noise=calibration["noise"] if calibration else None)
    blocks = report.build(suite, a, b, runs["baseline"], runs["candidate"], cmp, trials,
                          calibration, runner.missing)
    out = results / "reports" / f"{a.name}-vs-{b.name}"
    paths = report.write(blocks, out, f"{suite.name}: {a.name} vs {b.name}",
                         _data(cmp, a, b, trials, runner))
    _finish(cmp, paths, runner)


@app.command()
def calibrate(
    suite_path: Path = SuiteArg,
    harness: Path = typer.Option(..., help="Harness to compare against itself (A/A)"),
    trials: int = TrialsOpt,
    results: Path = ResultsOpt,
    max_cost: float = CostOpt,
    offline: bool = OfflineOpt,
) -> None:
    """Compare a harness with itself. A trustworthy tool must say INCONCLUSIVE here; the
    spread it measures becomes the noise floor every later `evaluate` must beat.
    Trials 0..n-1 are shared with `evaluate`, so this costs n extra trials, not 2n."""
    suite, h, _ = _load(suite_path, harness, harness)
    results = results or suite.root / "results"
    runner = Runner(suite, results, max_cost=max_cost, offline=offline, log=typer.echo)
    typer.echo(f"calibrate {suite.name}: {h.name} ({h.hash}) vs itself, {trials}+{trials} trials")
    runs = _collect(runner, {"A": (h, list(range(trials))),
                             "A'": (h, list(range(trials, 2 * trials)))})
    cmp = stats.compare(runs["A"], runs["A'"])
    cal = {"harness": h.name, "harness_hash": h.hash, "verdict": cmp.verdict,
           "tasks": len(suite.tasks), "trials": trials, "noise": stats.noise_floor(cmp)}
    (results / f"calibration-{h.hash}.json").write_text(json.dumps(cal, indent=2), encoding="utf-8")
    blocks = report.build(suite, h, h, runs["A"], runs["A'"], cmp, trials, None, runner.missing,
                          labels=("A", "A'"))
    paths = report.write(blocks, results / "reports" / f"{h.name}-calibration",
                         f"{suite.name}: {h.name} A/A", _data(cmp, h, h, trials, runner))
    if cmp.verdict != "INCONCLUSIVE":
        typer.secho("WARNING: A/A produced a non-inconclusive verdict. At this sample size the "
                    "tool can report differences that do not exist. Add trials or tasks.",
                    fg=typer.colors.RED)
    _finish(cmp, paths, runner, exit_with_verdict=False)


def _load(suite_path, a_path, b_path):
    try:
        return load_suite(suite_path), load_harness(a_path), load_harness(b_path)
    except ConfigError as e:
        typer.secho(f"config error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(64) from None


def _collect(runner: Runner, arms):
    try:
        return runner.collect(arms)
    except (IsolationError, ContaminationError) as e:
        typer.secho(f"isolation failure, results would not be trustworthy:\n{e}",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(65) from None


def _data(cmp, a, b, trials, runner) -> dict:
    return {"verdict": cmp.verdict, "exit_code": cmp.exit_code, "reasons": cmp.reasons,
            "baseline": {"name": a.name, "hash": a.hash}, "candidate": {"name": b.name, "hash": b.hash},
            "trials": trials, "spent_usd_this_invocation": round(runner.spent, 4),
            "missing": runner.missing, "metrics": [m.__dict__ for m in cmp.metrics]}


def _finish(cmp, paths, runner, exit_with_verdict: bool = True) -> None:
    color = {"IMPROVEMENT": "green", "REGRESSION": "red", "TRADE-OFF": "yellow"}.get(cmp.verdict, "white")
    typer.echo("")
    typer.secho(f"VERDICT: {cmp.verdict}", fg=color, bold=True)
    for r in cmp.reasons:
        typer.echo(f"  - {r}")
    typer.echo(f"spent this invocation: ${runner.spent:.2f}"
               + (f", {len(runner.missing)} runs missing" if runner.missing else ""))
    typer.echo(f"report: {paths['html']}\n        {paths['md']}")
    if exit_with_verdict:
        raise typer.Exit(cmp.exit_code)


def _read_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
