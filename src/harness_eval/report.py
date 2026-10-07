"""Evaluation report: one list of blocks rendered to Markdown and to a standalone HTML page.

The report is built to answer, in order: what is the verdict, what changed in the harness,
which numbers moved and how sure are we, where (which tasks / rules), and can I trust the
measurement itself (isolation, failures, tampering, sample size, A/A noise floor).
"""

from __future__ import annotations

import difflib
import html
import json
from collections import Counter
from pathlib import Path

from harness_eval.config import Harness, Suite
from harness_eval.stats import Comparison, MetricResult, metric_value

ADVICE = {
    "IMPROVEMENT": "Safe to roll out: at least one metric improved beyond noise and nothing got worse.",
    "REGRESSION": "Do not roll out: the change made something measurably worse.",
    "TRADE-OFF": "Human decision needed: something improved and something else got worse.",
    "INCONCLUSIVE": "No evidence either way at this sample size. Add tasks or trials before deciding.",
}


def build(suite: Suite, a: Harness, b: Harness, runs_a: list[dict], runs_b: list[dict],
          cmp: Comparison, trials: int, calibration: dict | None, missing: list[str],
          labels: tuple[str, str] = ("baseline", "candidate")) -> list[tuple]:
    la, lb = labels
    blocks: list[tuple] = [
        ("h1", f"Harness evaluation: {suite.name}"),
        ("verdict", cmp.verdict, ADVICE[cmp.verdict]),
        ("p", f"Exit code {cmp.exit_code}. " + ("; ".join(cmp.reasons) + "." if cmp.reasons else "")),
        ("h2", "What changed"),
        ("table", ["", la, lb], [
            ["harness", f"`{a.name}` ({a.hash})", f"`{b.name}` ({b.hash})"],
            ["agent / model", f"{a.agent} / {a.model}", f"{b.agent} / {b.model}"],
            ["runs", str(len(runs_a)), str(len(runs_b))],
        ]),
    ]
    diff = harness_diff(a, b)
    blocks.append(("pre", diff) if diff else ("p", "Harness files are identical (A/A run)."))

    blocks += [("h2", "Scorecard"),
               ("p", f"{len(suite.tasks)} tasks x {trials} trials per arm. Delta = {lb} - {la}, "
                     "averaged per task. 95% CI from a task+trial bootstrap. "
                     "A metric only counts as moved when its CI excludes 0"
                     + (" and the delta beats the A/A noise floor." if calibration else ".")),
               ("table", ["metric", la, lb, "delta", "95% CI", "noise floor", "outcome"],
                [_metric_row(m) for m in cmp.metrics])]

    blocks += [("h2", "Per task"),
               ("p", "Mean per task (works / intent / conventions are 0-1, cost in USD)."),
               ("table", ["task", "works", "intent", "conventions", "cost", "tampered runs"],
                _task_rows(suite, runs_a, runs_b))]

    blocks += [("h2", "Convention violations"),
               ("p", "Runs with at least one violation of each rule (lower is better)."),
               ("table", ["rule", la, lb], _violation_rows(suite, runs_a, runs_b))]

    blocks += [("h2", "Can I trust this measurement?"),
               ("table", ["check", "result"], _trust_rows(suite, a, runs_a, runs_b, trials,
                                                          calibration, missing, labels))]

    blocks += [("h2", "Evidence"),
               ("p", "Every run is a JSON record next to the agent's diff and redacted log. "
                     "Open the diff of any surprising cell before acting on the verdict."),
               ("table", ["arm", "task", "trial", "status", "works", "intent", "conv", "cost", "record"],
                _evidence_rows(runs_a, la) + _evidence_rows(runs_b, lb))]
    return blocks


def harness_diff(a: Harness, b: Harness) -> str:
    fa, fb = a.files(), b.files()
    out = []
    for path in sorted(set(fa) | set(fb)):
        if fa.get(path) != fb.get(path):
            out += difflib.unified_diff(
                (fa.get(path) or "").splitlines(), (fb.get(path) or "").splitlines(),
                f"{a.name}/{path}", f"{b.name}/{path}", lineterm="", n=1)
    if len(out) > 120:
        out = out[:120] + [f"... {len(out) - 120} more diff lines (compare the harness directories)"]
    return "\n".join(out)


def _fmt(name: str, v: float | None) -> str:
    if v is None:
        return "-"
    if name == "cost_usd":
        return f"${v:.4f}"
    if name in ("tokens", "duration_s"):
        return f"{v:,.0f}"
    return f"{v:.2f}"


def _metric_row(m: MetricResult) -> list[str]:
    icon = {"better": "better", "worse": "WORSE", "no change": "no change", "n/a": "n/a"}[m.outcome]
    signed = f"{'+' if (m.delta or 0) >= 0 else ''}{_fmt(m.name, m.delta)}" if m.delta is not None else "-"
    ci = f"[{_fmt(m.name, m.ci[0])}, {_fmt(m.name, m.ci[1])}]" if m.ci else "-"
    label = m.label + (" (guardrail)" if m.guardrail else "")
    return [label, _fmt(m.name, m.mean_a), _fmt(m.name, m.mean_b), signed, ci,
            _fmt(m.name, m.noise_floor), icon]


def _task_rows(suite: Suite, runs_a: list[dict], runs_b: list[dict]) -> list[list[str]]:
    rows = []
    for task in suite.tasks:
        ra = [r for r in runs_a if r["task"] == task.id]
        rb = [r for r in runs_b if r["task"] == task.id]
        cells = [task.id]
        for name in ("works", "intent", "conventions", "cost_usd"):
            cells.append(f"{_fmt(name, _avg(ra, name))} -> {_fmt(name, _avg(rb, name))}")
        cells.append(f"{_tampered(ra)} -> {_tampered(rb)}")
        rows.append(cells)
    return rows


def _avg(runs: list[dict], name: str) -> float | None:
    vals = [v for r in runs if (v := metric_value(r, name)) is not None]
    return sum(vals) / len(vals) if vals else None


def _tampered(runs: list[dict]) -> int:
    return sum(1 for r in runs if r.get("scores", {}).get("tampered"))


def _violation_rows(suite: Suite, runs_a: list[dict], runs_b: list[dict]) -> list[list[str]]:
    def count(runs):
        c = Counter()
        for r in runs:
            c.update({v["rule"] for v in r.get("scores", {}).get("violations", [])})
        return c

    ca, cb = count(runs_a), count(runs_b)
    return [[rule, f"{ca[rule]}/{len(runs_a)}", f"{cb[rule]}/{len(runs_b)}"]
            for rule in suite.conventions]


def _trust_rows(suite, a, runs_a, runs_b, trials, calibration, missing, labels) -> list[list[str]]:
    rows = []
    for label, runs in zip(labels, (runs_a, runs_b)):
        st = Counter(r["status"] for r in runs)
        rows.append([f"run status ({label})", ", ".join(f"{k}: {v}" for k, v in sorted(st.items()))
                     + (" - failed runs score 0 quality, they are not dropped" if len(st) > 1 else "")])
    claude = [r for r in runs_a + runs_b if r["agent_kind"] == "claude"]
    if claude:
        leaked = sum(1 for r in claude if (r["agent"].get("loaded") or {}).get("plugins"))
        rows.append(["isolation", f"{len(claude) - leaked}/{len(claude)} Claude runs loaded no plugins, "
                                  "no MCP servers beyond the harness; runs execute outside the user "
                                  "profile after an ancestor CLAUDE.md/AGENTS.md scan"])
    else:
        rows.append(["isolation", "private HOME/CODEX_HOME per run; ancestor CLAUDE.md/AGENTS.md scan"])
    tam = _tampered(runs_a) + _tampered(runs_b)
    rows.append(["test tampering", f"{tam} run(s) edited or deleted existing tests "
                                   "(originals are restored before scoring, so this cannot earn points)"])
    rows.append(["hidden tests", "copied in only after the agent exited; conftest/ini ignored"])
    size_note = "OK" if trials >= 3 and len(suite.tasks) >= 5 else "SMALL - treat as indicative"
    rows.append(["sample size", f"{len(suite.tasks)} tasks x {trials} trials per arm ({size_note})"])
    if calibration:
        rows.append(["A/A calibration", f"baseline vs itself gave {calibration['verdict']} "
                                        f"({calibration['tasks']} tasks x {calibration['trials']} trials); "
                                        "its CI widths are the noise floors in the scorecard"])
    else:
        rows.append(["A/A calibration", "not run - run `harness-eval calibrate` to measure the noise floor"])
    if missing:
        rows.append(["missing runs", f"{len(missing)}: " + "; ".join(missing[:5])])
    return rows


def _evidence_rows(runs: list[dict], label: str) -> list[list[str]]:
    rows = []
    for r in sorted(runs, key=lambda r: (r["task"], r["trial"])):
        s = r.get("scores", {})
        rel = f"runs/{r['harness_hash']}/{r['task']}-{r['task_hash']}/trial-{r['trial']}"
        rows.append([label, r["task"], str(r["trial"]), r["status"], f"{s.get('works', 0):.0f}",
                     f"{s.get('intent', 0):.2f}", f"{s.get('conventions', 0):.2f}",
                     _fmt("cost_usd", r["agent"].get("cost_usd")), f"[json]({rel}.json) [diff]({rel}.diff)"])
    return rows


# --- rendering ---------------------------------------------------------------------------

def to_markdown(blocks: list[tuple]) -> str:
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            out.append(f"# {b[1]}")
        elif kind == "h2":
            out.append(f"## {b[1]}")
        elif kind == "verdict":
            out.append(f"> **Verdict: {b[1]}** - {b[2]}")
        elif kind == "p":
            out.append(b[1])
        elif kind == "pre":
            out.append(f"```diff\n{b[1]}\n```")
        elif kind == "table":
            headers, rows = b[1], b[2]
            out.append("| " + " | ".join(headers) + " |")
            out.append("|" + "---|" * len(headers))
            out += ["| " + " | ".join(c.replace("|", "\\|") for c in row) + " |" for row in rows]
        out.append("")
    return "\n".join(out)


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a65;--line:#e4e1d8;--card:#fff;
--good:#1f7a4d;--bad:#b3261e;--warn:#9a6b00;--neutral:#4a5568}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--fg:#ecebe6;--muted:#a3a19a;
--line:#2e2d2a;--card:#1c1c1a;--good:#5cc28f;--bad:#f2867e;--warn:#e5b54a;--neutral:#a0aec0}}
body{background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;
margin:0;padding:24px 16px}main{max-width:1100px;margin:auto}
h1{font-size:26px;margin:0 0 16px}h2{font-size:18px;margin:32px 0 8px;border-bottom:1px solid var(--line);
padding-bottom:4px}p{color:var(--muted)}
.verdict{border-radius:10px;padding:16px 20px;background:var(--card);border:2px solid var(--neutral)}
.verdict b{font-size:22px;display:block}.IMPROVEMENT{border-color:var(--good)}.REGRESSION{border-color:var(--bad)}
.TRADE-OFF{border-color:var(--warn)}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;background:var(--card);font-size:13.5px}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{font-weight:600}td.better{color:var(--good);font-weight:600}td.WORSE{color:var(--bad);font-weight:700}
pre{background:var(--card);border:1px solid var(--line);padding:12px;overflow-x:auto;font-size:12.5px}
.add{color:var(--good)}.del{color:var(--bad)}a{color:inherit}
"""


def to_html(blocks: list[tuple], title: str) -> str:
    parts = []
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            parts.append(f"<h1>{_inline(b[1])}</h1>")
        elif kind == "h2":
            parts.append(f"<h2>{_inline(b[1])}</h2>")
        elif kind == "verdict":
            parts.append(f'<div class="verdict {b[1]}"><b>{b[1]}</b>{_inline(b[2])}</div>')
        elif kind == "p":
            parts.append(f"<p>{_inline(b[1])}</p>")
        elif kind == "pre":
            lines = []
            for line in b[1].splitlines():
                cls = "add" if line.startswith("+") else "del" if line.startswith("-") else ""
                lines.append(f'<span class="{cls}">{html.escape(line)}</span>')
            parts.append("<pre>" + "\n".join(lines) + "</pre>")
        elif kind == "table":
            head = "".join(f"<th>{_inline(h)}</th>" for h in b[1])
            body = "".join("<tr>" + "".join(f'<td class="{html.escape(c)}">{_inline(c)}</td>' for c in row)
                           + "</tr>" for row in b[2])
            parts.append(f'<div class="wrap"><table><tr>{head}</tr>{body}</table></div>')
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body><main>{''.join(parts)}</main></body></html>")


def _inline(text: str) -> str:
    """Escape, then render the two bits of Markdown we emit: `code` and [text](link)."""
    import re

    s = html.escape(text)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)


def write(blocks: list[tuple], out_dir: Path, title: str, data: dict) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {"md": out_dir / "report.md", "html": out_dir / "report.html", "json": out_dir / "report.json"}
    paths["md"].write_text(to_markdown(blocks), encoding="utf-8")
    paths["html"].write_text(to_html(blocks, title), encoding="utf-8")
    paths["json"].write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return paths
