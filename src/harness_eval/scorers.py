"""Deterministic scoring of one finished run.

    works        did the repo's own tests still pass?   (pristine copies, agent edits reverted)
    intent       fraction of hidden acceptance tests passed (business requirement)
    conventions  fraction of team convention rules satisfied (AST checks on source)
    tampered     the agent changed or removed an existing test (reported, never rewarded)

Order matters: tampering and tests-added are read from the agent's tree *before* the
pristine tests are restored; hidden tests are copied in only after the agent has exited.
"""

from __future__ import annotations

import ast
import builtins
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from harness_eval.config import Suite, Task
from harness_eval.workspace import changed_files

HIDDEN_DIR = "_harness_eval_hidden"


def score_run(suite: Suite, task: Task, ws: Path) -> dict:
    changes = changed_files(ws)
    tampered = tampered_tests(suite, ws)
    added_tests = sorted(p for p, s in changes.items()
                         if p.startswith(suite.tests + "/") and s in "AM" and p.endswith(".py"))

    # Restore the repo's original tests so "works" cannot be gamed by editing them.
    original_tests = sorted((suite.repo / suite.tests).rglob("test_*.py"))
    for src in original_tests:
        dst = ws / src.relative_to(suite.repo)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    works = run_pytest(ws, [str(p.relative_to(suite.repo)) for p in original_tests])

    hidden = ws / HIDDEN_DIR / f"test_{task.id.replace('-', '_')}.py"
    hidden.parent.mkdir(exist_ok=True)
    shutil.copy2(task.hidden_tests, hidden)
    intent = run_pytest(ws, [hidden.relative_to(ws).as_posix()])

    violations = check_conventions(ws / suite.source, suite.conventions, bool(added_tests))
    rules = list(suite.conventions)
    failed_rules = {v["rule"] for v in violations}
    return {
        "works": 1.0 if works["total"] and works["passed"] == works["total"] else 0.0,
        "works_detail": works,
        "intent": works_fraction(intent),
        "intent_detail": intent,
        "conventions": (len(rules) - len(failed_rules)) / len(rules) if rules else 1.0,
        "violations": violations,
        "tampered": tampered,
        "tests_added": added_tests,
        "files_changed": changes,
    }


def works_fraction(result: dict) -> float:
    return result["passed"] / result["total"] if result["total"] else 0.0


def run_pytest(ws: Path, paths: list[str], timeout: int = 180) -> dict:
    """Run pytest on explicit paths with an empty ini and no conftest, so files the agent
    added (pytest.ini, conftest.py) cannot change how the tests run."""
    junit = ws.parent / f"junit-{len(list(ws.parent.glob('junit-*')))}.xml"
    empty_ini = ws.parent / "pytest-empty.ini"
    empty_ini.write_text("[pytest]\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest",
           "-c", str(empty_ini), "--rootdir", str(ws), f"--junitxml={junit}", *paths]
    try:
        out = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=timeout,
                             encoding="utf-8", errors="replace")
        tail = (out.stdout + out.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        return {"passed": 0, "total": 0, "failed": [], "output": "pytest timed out"}
    return {**_parse_junit(junit), "output": tail}


def _parse_junit(path: Path) -> dict:
    if not path.is_file():
        return {"passed": 0, "total": 0, "failed": ["<no junit report: collection crashed>"]}
    root = ET.parse(path).getroot()
    total, failed = 0, []
    for case in root.iter("testcase"):
        total += 1
        if any(child.tag in ("failure", "error") for child in case):
            failed.append(case.get("name", "?"))
    # Collection errors produce <error> on a testsuite with no testcases.
    for suite in root.iter("testsuite"):
        if int(suite.get("errors", 0)) and not list(suite.iter("testcase")):
            failed.append("<collection error>")
            total = max(total, 1)
    return {"passed": total - len(failed), "total": total, "failed": failed}


def tampered_tests(suite: Suite, ws: Path) -> list[str]:
    """Original test functions that the agent deleted or modified."""
    problems = []
    for src in sorted((suite.repo / suite.tests).rglob("test_*.py")):
        rel = src.relative_to(suite.repo).as_posix()
        dst = ws / rel
        if not dst.is_file():
            problems.append(f"{rel}: deleted")
            continue
        before, after = _test_functions(src), _test_functions(dst)
        for name, body in before.items():
            if name not in after:
                problems.append(f"{rel}::{name}: removed")
            elif after[name] != body:
                problems.append(f"{rel}::{name}: modified")
    return problems


def _test_functions(path: Path) -> dict[str, str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return {}
    return {n.name: ast.dump(n) for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")}


# --- conventions -------------------------------------------------------------------------

BUILTIN_EXCEPTIONS = {
    name for name, obj in vars(builtins).items()
    if isinstance(obj, type) and issubclass(obj, BaseException)
}
LOG_LEVELS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}


def check_conventions(source: Path, rules: tuple[str, ...], tests_added: bool) -> list[dict]:
    """Return one dict per violation: {rule, file, line, detail}."""
    violations: list[dict] = []
    if "tests-added" in rules and not tests_added:
        violations.append({"rule": "tests-added", "file": "", "line": 0,
                           "detail": "no test file added or changed"})
    for path in sorted(source.rglob("*.py")):
        rel = path.relative_to(source.parent).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as e:
            violations.append({"rule": "syntax", "file": rel, "line": e.lineno or 0, "detail": str(e)})
            continue
        for rule, line, detail in _ast_violations(tree, rules):
            violations.append({"rule": rule, "file": rel, "line": line, "detail": detail})
    return violations


def _ast_violations(tree: ast.AST, rules: tuple[str, ...]):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if "no-print" in rules and isinstance(fn, ast.Name) and fn.id == "print":
                yield "no-print", node.lineno, "print() call"
            if "decimal-money" in rules and isinstance(fn, ast.Name) and fn.id == "float":
                yield "decimal-money", node.lineno, "float() call"
            if ("module-logger" in rules and isinstance(fn, ast.Attribute)
                    and isinstance(fn.value, ast.Name) and fn.value.id == "logging"
                    and fn.attr in LOG_LEVELS):
                yield "module-logger", node.lineno, f"root logger call logging.{fn.attr}()"
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            if "decimal-money" in rules:
                yield "decimal-money", node.lineno, f"float literal {node.value!r}"
        elif isinstance(node, ast.Raise) and node.exc is not None and "domain-errors" in rules:
            exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            if isinstance(exc, ast.Name) and exc.id in BUILTIN_EXCEPTIONS:
                yield "domain-errors", node.lineno, f"raises built-in {exc.id}"
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and "type-hints" in rules:
            if node.name.startswith("_") and node.name != "__init__":
                continue
            args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            missing = [a.arg for a in args if a.annotation is None and a.arg not in ("self", "cls")]
            if missing or node.returns is None:
                what = ", ".join(missing + ([] if node.returns else ["return"]))
                yield "type-hints", node.lineno, f"{node.name}() missing hints: {what}"
