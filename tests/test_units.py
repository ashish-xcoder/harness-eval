import ast
import json
import random

from harness_eval import runner, stats
from harness_eval.agents import AgentResult
from harness_eval.config import load_harness
from harness_eval.scorers import _ast_violations, check_conventions
from harness_eval.workspace import leaked_ancestors


def rules_hit(src: str) -> set[str]:
    rules = ("no-print", "domain-errors", "decimal-money", "type-hints", "module-logger")
    return {r for r, _, _ in _ast_violations(ast.parse(src), rules)}


def test_convention_rules_fire_on_each_violation():
    assert rules_hit("def f(x: int) -> int:\n    print(x)\n    return x") == {"no-print"}
    assert rules_hit("def f() -> None:\n    raise ValueError('x')") == {"domain-errors"}
    assert rules_hit("def f() -> float:\n    return 0.05") == {"decimal-money"}
    assert rules_hit("def f(a):\n    return a") == {"type-hints"}
    assert rules_hit("import logging\ndef f() -> None:\n    logging.info('x')") == {"module-logger"}


def test_convention_rules_accept_clean_code():
    clean = (
        "import logging\nfrom decimal import Decimal\nfrom app.errors import OrderError\n"
        "logger = logging.getLogger(__name__)\n"
        "class Bad(OrderError):\n    pass\n"
        "def f(x: Decimal) -> Decimal:\n    logger.info('x')\n    if not x:\n        raise Bad()\n"
        "    return x * Decimal('0.9')\n"
        "def _private(a):\n    return a\n"
    )
    assert rules_hit(clean) == set()


def test_tests_added_rule(tmp_path):
    (tmp_path / "app").mkdir()
    v = check_conventions(tmp_path / "app", ("tests-added",), tests_added=False)
    assert [x["rule"] for x in v] == ["tests-added"]
    assert check_conventions(tmp_path / "app", ("tests-added",), tests_added=True) == []


def run(task: str, value: float, status: str = "ok") -> dict:
    return {"task": task, "status": status, "scores": {"works": value, "intent": value,
            "conventions": value}, "agent": {"cost_usd": 0.1, "input_tokens": 10,
            "output_tokens": 1, "duration_s": 5}}


def test_pure_noise_is_inconclusive():
    rng = random.Random(1)
    a = [run(f"t{t}", rng.choice([0.0, 1.0])) for t in range(5) for _ in range(3)]
    b = [run(f"t{t}", rng.choice([0.0, 1.0])) for t in range(5) for _ in range(3)]
    assert stats.compare(a, b).verdict == "INCONCLUSIVE"


def test_failed_runs_count_as_zero_not_missing():
    a = [run(f"t{t}", 1.0) for t in range(5) for _ in range(3)]
    b = [run(f"t{t}", 1.0, status="timeout") for t in range(5) for _ in range(3)]
    assert stats.compare(a, b).verdict == "REGRESSION"


def test_noise_floor_suppresses_small_effects():
    a = [run(f"t{t}", 0.80) for t in range(5) for _ in range(3)]
    b = [run(f"t{t}", 0.85) for t in range(5) for _ in range(3)]
    assert stats.compare(a, b).verdict == "IMPROVEMENT"
    noisy = {"works": 0.1, "intent": 0.1, "conventions": 0.1}
    assert stats.compare(a, b, noise=noisy).verdict == "INCONCLUSIVE"


def test_ancestor_instruction_files_are_detected(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("global rules")
    assert tmp_path / "CLAUDE.md" in leaked_ancestors(tmp_path / "runs" / "x")


def test_contamination_flags_plugins_and_undeclared_mcp(tmp_path):
    (tmp_path / "workspace").mkdir()
    (tmp_path / "harness.yaml").write_text("agent: claude\n")
    (tmp_path / "workspace" / ".mcp.json").write_text(json.dumps({"mcpServers": {"ok": {}}}))
    h = load_harness(tmp_path)
    clean = AgentResult("ok", 1, loaded={"plugins": [], "mcp_servers": [{"name": "ok"}]})
    assert runner.contamination(h, clean) == ""
    assert "plugins" in runner.contamination(h, AgentResult("ok", 1, loaded={"plugins": ["x"]}))
    extra = AgentResult("ok", 1, loaded={"plugins": [], "mcp_servers": [{"name": "rogue"}]})
    assert "rogue" in runner.contamination(h, extra)


def test_redaction_removes_credential_values(tmp_path, monkeypatch):
    cred = tmp_path / "cred.json"
    cred.write_text(json.dumps({"oauth": {"accessToken": "sk-secret-token-0123456789abcdef"}}))
    monkeypatch.setattr(runner, "CREDENTIALS", {"claude": (cred, None)})
    log = tmp_path / "x.log"
    log.write_text("agent printed sk-secret-token-0123456789abcdef here")
    runner._redact(log)
    assert "sk-secret" not in log.read_text()
