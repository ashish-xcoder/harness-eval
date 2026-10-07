"""End-to-end: the real `evaluate` / `calibrate` commands on the real example suite, driven
by deterministic replay agents. Proves the verdict logic on known answers for $0."""

import json
from pathlib import Path

from typer.testing import CliRunner

from harness_eval.cli import app
from tests.conftest import ROOT, make_harness

cli = CliRunner()


def evaluate(suite: Path, a: Path, b: Path, *extra: str):
    return cli.invoke(app, ["evaluate", str(suite), "--baseline", str(a), "--candidate", str(b),
                            "--trials", "2", *extra])


def records(suite: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in (suite / "results" / "runs").rglob("*.json")]


def test_known_bad_change_is_a_regression(suite_dir, tmp_path):
    good = make_harness(tmp_path, "good")
    bad = make_harness(tmp_path, "bad", "bad")
    res = evaluate(suite_dir, good, bad)
    assert res.exit_code == 1, res.output
    assert "VERDICT: REGRESSION" in res.output
    report = (suite_dir / "results" / "reports" / "good-vs-bad" / "report.md").read_text()
    assert "Works (existing tests pass) (guardrail)" in report


def test_identical_harnesses_are_inconclusive(suite_dir, tmp_path):
    a = make_harness(tmp_path, "a")
    b = make_harness(tmp_path, "b")
    res = evaluate(suite_dir, a, b)
    assert res.exit_code == 2, res.output


def test_better_conventions_is_an_improvement(suite_dir, tmp_path):
    sloppy = make_harness(tmp_path, "sloppy", "sloppy")
    good = make_harness(tmp_path, "good")
    res = evaluate(suite_dir, sloppy, good)
    assert res.exit_code == 0, res.output
    assert "Team conventions: better" in res.output
    rules = {v["rule"] for r in records(suite_dir) if r["harness"] == "sloppy"
             for v in r["scores"]["violations"]}
    assert rules == {"no-print", "domain-errors", "decimal-money", "type-hints", "tests-added"}


def test_quality_up_cost_up_is_a_trade_off(suite_dir, tmp_path):
    sloppy = make_harness(tmp_path, "sloppy", "sloppy", cost=0.01)
    good = make_harness(tmp_path, "good-pricey", "good", cost=0.20)
    res = evaluate(suite_dir, sloppy, good)
    assert res.exit_code == 3, res.output


def test_test_tampering_is_flagged_and_earns_nothing(suite_dir, tmp_path):
    good = make_harness(tmp_path, "good")
    tamper = make_harness(tmp_path, "tamper", "tamper")
    res = evaluate(suite_dir, good, tamper)
    assert res.exit_code == 1, res.output
    tampered = [r for r in records(suite_dir) if r["harness"] == "tamper"]
    assert all(r["scores"]["tampered"] for r in tampered)
    assert all(r["scores"]["works"] == 0.0 for r in tampered)  # originals restored, still fails


def test_rerun_uses_cache_and_offline_rerenders_for_free(suite_dir, tmp_path):
    good = make_harness(tmp_path, "good")
    bad = make_harness(tmp_path, "bad", "bad")
    evaluate(suite_dir, good, bad)
    before = {p: p.stat().st_mtime for p in (suite_dir / "results" / "runs").rglob("*.json")}
    res = evaluate(suite_dir, good, bad, "--offline")
    assert res.exit_code == 1, res.output
    assert "runs missing" not in res.output
    after = {p: p.stat().st_mtime for p in (suite_dir / "results" / "runs").rglob("*.json")}
    assert before == after


def test_offline_without_cache_reports_missing_runs(suite_dir, tmp_path):
    a = make_harness(tmp_path, "a")
    b = make_harness(tmp_path, "b")
    res = evaluate(suite_dir, a, b, "--offline")
    assert "runs missing" in res.output


def test_calibrate_aa_is_inconclusive_and_feeds_noise_floor(suite_dir, tmp_path):
    good = make_harness(tmp_path, "good")
    res = cli.invoke(app, ["calibrate", str(suite_dir), "--harness", str(good), "--trials", "2"])
    assert res.exit_code == 0, res.output
    assert "VERDICT: INCONCLUSIVE" in res.output
    cal = next((suite_dir / "results").glob("calibration-*.json"))
    assert json.loads(cal.read_text())["verdict"] == "INCONCLUSIVE"
    res = evaluate(suite_dir, good, make_harness(tmp_path, "bad", "bad"))
    report = (suite_dir / "results" / "reports" / "good-vs-bad" / "report.md").read_text()
    assert "baseline vs itself gave INCONCLUSIVE" in report


def test_committed_results_contain_no_credentials():
    leaked = [p for p in (ROOT / "examples").rglob("*")
              if p.name in (".credentials.json", "auth.json")]
    assert leaked == []
