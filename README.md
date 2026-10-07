<div align="center">

<img src="docs/assets/banner.png" alt="harness-eval: did this harness change make the coding agent's code better or worse?" width="100%">

<br>

[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![uv](https://img.shields.io/badge/managed%20with-uv-DE5FE9?logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![tests](https://img.shields.io/badge/tests-18%20passing-2ea44f?logo=pytest&logoColor=white)](tests)
[![lint](https://img.shields.io/badge/ruff-clean-D7FF64?logo=ruff&logoColor=black)](pyproject.toml)
<br>
[![Claude Code](https://img.shields.io/badge/agent-Claude%20Code-D97757?logo=anthropic&logoColor=white)](src/harness_eval/agents.py)
[![Codex](https://img.shields.io/badge/agent-Codex-412991?logo=openai&logoColor=white)](src/harness_eval/agents.py)
[![CrewAI + Ollama](https://img.shields.io/badge/agent-CrewAI%20%2B%20Ollama-0f766e)](src/harness_eval/local_agent.py)
[![MCP](https://img.shields.io/badge/MCP-workspace%20server-13293d)](src/harness_eval/mcp_server.py)
<br>
[![demo verdict](https://img.shields.io/badge/demo%20verdict-INCONCLUSIVE-64748b)](examples/orders/results/reports/baseline-vs-candidate/report.md)
[![demo runs](https://img.shields.io/badge/real%20runs-60%20Claude%20Code-0f766e)](examples/orders/results/runs)
[![demo cost](https://img.shields.io/badge/demo%20spend-%245.28-b45309)](docs/one-pager.pdf)
[![replay](https://img.shields.io/badge/re--render-%240-2ea44f)](#quick-start-no-agent-runs-0)

**[Quick start](#quick-start-no-agent-runs-0)** ·
**[Architecture](#system-architecture)** ·
**[What it measures](#what-it-measures)** ·
**[Why you can trust it](#why-you-can-trust-the-verdict)** ·
**[One-pager (PDF)](docs/one-pager.pdf)** ·
**[How it was built](process/README.md)**

</div>

---

> **Did this change to our coding-agent harness make the code better or worse?**

`harness-eval` runs the same real coding tasks with your current harness (**baseline**) and the
changed one (**candidate**), scores every result on four dimensions, and returns a verdict a
harness maintainer can act on, backed by confidence intervals and an evidence trail down to
each agent's diff.

| | |
|---|---|
| **Harness** | Everything around the model: `AGENTS.md`/`CLAUDE.md`, skills, MCP servers, hooks, settings, the model, the agent CLI. Here it is just a directory, so every kind of change is evaluated the same way. |
| **Verdict** | `IMPROVEMENT` (exit 0) · `REGRESSION` (1) · `INCONCLUSIVE` (2) · `TRADE-OFF` (3), ready to gate CI. |
| **Evidence** | Paired per-task deltas, a task+trial bootstrap 95% CI, an A/A noise floor, and a JSON record + diff + redacted log for every run. |

## Quick start (no agent runs, $0)

The repo ships with the results of a real evaluation, so the report re-renders without
calling any agent:

```bash
uv sync
uv run harness-eval evaluate examples/orders \
    --baseline examples/orders/harnesses/baseline \
    --candidate examples/orders/harnesses/candidate \
    --trials 6 --offline
```

Open `examples/orders/results/reports/baseline-vs-candidate/report.html`.
The committed result is a real run: Claude Code (Haiku), 5 tasks x 6 trials per arm, plus an A/A calibration, $5.28 in total. Verdict: INCONCLUSIVE, explained in the [one-pager](docs/one-pager.pdf).

Exit code: `0` IMPROVEMENT, `1` REGRESSION, `2` INCONCLUSIVE, `3` TRADE-OFF (use it to gate CI).

### The committed demo at a glance

Baseline = bare `AGENTS.md`; candidate = `AGENTS.md` + team conventions. Claude Code on Haiku, 5 tasks × 6 trials per arm.

| Metric | Baseline | Candidate | Δ (95% CI) | Outcome |
|---|---:|---:|---|---|
| Works (guardrail) | 1.00 | 1.00 | +0.00 | no change |
| Business intent (guardrail) | 1.00 | 0.99 | −0.01 [−0.03, 0.00] | no change |
| Team conventions | 0.84 | **0.90** | +0.06 [0.02, 0.11] | below A/A noise floor (0.067) |
| Runs with no tests added | 28/30 | **18/30** | | |
| Cost per task | $0.083 | $0.093 | +$0.010 [−0.001, 0.021] | no change |

**Verdict: INCONCLUSIVE**: a small, probably real convention gain that the tool will not call proven.
Why I distrusted the 3-trial version of this result and what I did about it: [one-pager](docs/one-pager.pdf).

## System architecture

<p align="center"><img src="docs/assets/architecture.png" alt="harness-eval system architecture: inputs, orchestration, isolated execution, deterministic scoring, verdict" width="100%"></p>

1. **Inputs**: a suite (repo, prompts, hidden tests, convention rules) and two harness directories.
2. **Orchestrate**: the runner interleaves arms, caches every run by content hash, enforces budget/time caps, and refuses to start if any ancestor directory holds instruction files.
3. **Execute**: each run gets a fresh workspace and a private home outside the user profile; the agent adapter (Claude Code, Codex, CrewAI + Ollama via the workspace MCP server, or replay) does the task.
4. **Score**: tamper check, then pristine tests (*works*), hidden tests (*intent*), AST rules (*conventions*) and the agent's own usage (*cost*).
5. **Decide**: paired deltas, bootstrap CI, A/A noise floor, guardrails, then report + exit code.

## Run it for real

Requirements: [uv](https://docs.astral.sh/uv/), git, and the agent you evaluate
(`claude` logged in, or `codex` logged in, or Ollama for the free local agent).

```bash
# 1. measure the noise floor once per baseline: harness vs itself (A/A)
uv run harness-eval calibrate examples/orders --harness examples/orders/harnesses/baseline --trials 3

# 2. evaluate the change (reuses the baseline runs from step 1; cached runs are never paid twice)
uv run harness-eval evaluate examples/orders \
    --baseline examples/orders/harnesses/baseline \
    --candidate examples/orders/harnesses/candidate --trials 3 --max-cost 10
```

Free, fully local (CrewAI + Ollama + the bundled workspace MCP server), evaluating a model swap:

```bash
ollama pull qwen2.5:7b && ollama pull qwen3.5:4b
# Ollama's default 4k context truncates the agent prompt -> the model never calls a tool.
printf 'FROM qwen2.5:7b\nPARAMETER num_ctx 16384\n' > M1 && ollama create qwen2.5-7b-16k -f M1
printf 'FROM qwen3.5:4b\nPARAMETER num_ctx 16384\n' > M2 && ollama create qwen3.5-4b-16k -f M2
UV_PROJECT_ENVIRONMENT=.venv-local uv run --extra local harness-eval evaluate examples/orders \
    --baseline examples/orders/harnesses/local-qwen2.5 \
    --candidate examples/orders/harnesses/local-qwen3.5 --trials 1
```

The local agent works end to end, but on a 6 GB laptop GPU each run takes 5-15 minutes, so its
results are not committed. In the first local run qwen2.5 deleted `subtotal` while rewriting
`pricing.py`, and the tool scored it as a failed run (works 0), as designed.

## What it measures

| Dimension                             | How                                                                                                                                | Why this way                                            |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Works** (guardrail)           | the repo's own tests, restored from a pristine copy, must all pass                                                                 | an agent cannot pass by editing tests                   |
| **Business intent** (guardrail) | hidden acceptance tests written from the request, copied in only after the agent exits                                             | the agent cannot see or overfit them                    |
| **Conventions**                 | deterministic AST rules from the team's AGENTS.md (Decimal money, domain errors, no print, module logger, type hints, tests added) | reproducible, explainable per violation; no LLM opinion |
| **Cost**                        | USD, tokens, wall time per task from the agent's own output                                                                        | quality that costs 3x may not be worth it               |

Guardrails: if *works* or *intent* gets worse the verdict is `REGRESSION`, whatever else improved.

## Why you can trust the verdict

- **Paired, repeated, with uncertainty.** Every task runs N times per arm. Differences are
  computed per task (so task difficulty cancels) and a task+trial bootstrap gives a 95% CI.
  A metric only "moves" when its CI excludes zero.
- **A/A calibration.** `calibrate` compares the baseline with itself. A trustworthy tool must
  answer `INCONCLUSIVE` there; the spread it sees becomes a noise floor that later deltas must beat.
- **Isolation, verified.** Each run gets a private workspace *and* a private home
  (`HOME`, `USERPROFILE`, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`), so your personal `~/.claude`,
  plugins and hooks do not leak into the comparison. Runs live outside the user profile
  because Claude Code also reads `CLAUDE.md` from every *parent* directory; the tool scans the
  ancestors and refuses to run if any instruction file is found. Claude's `init` event is
  checked on every run: an unexpected plugin or MCP server aborts the evaluation.
- **No gaming.** Hidden tests arrive after the agent exits; pytest runs with an empty ini and
  `--noconftest`; edited or deleted original tests are restored and reported as tampering.
- **Failures count.** A timed-out or crashed run scores 0 quality; it is never silently dropped.
- **Interleaved arms** (A1 B1 A2 B2 ...), so rate limits or provider drift hit both arms equally.
- **Evidence.** Every cell in the report links to the run record, the agent's diff and its
  (credential-redacted) log.

## Layout

```
src/harness_eval/
  cli.py          evaluate / calibrate commands, exit codes
  config.py       suite.yaml + harness.yaml loading, content hashing for the cache
  workspace.py    isolated run dirs, ancestor scan, credentials copy/delete, git baseline + diff
  agents.py       claude / codex / crewai / replay adapters -> one AgentResult
  scorers.py      works, intent, conventions, tampering
  runner.py       cached run matrix, budget cap, contamination check, log redaction
  stats.py        paired task+trial bootstrap, noise floor, verdict rules
  report.py       Markdown + HTML report
  local_agent.py  CrewAI + Ollama coding agent
  mcp_server.py   workspace MCP server (list/read/write files, run tests), jailed to the workspace
examples/orders/  sample service, 5 tasks with hidden tests, 4 harnesses, committed results
tests/            pytest; replay agents prove REGRESSION / IMPROVEMENT / TRADE-OFF / A/A for $0
docs/             one-pager (md + pdf), banner + architecture images (assets/)
process/          how this was built: AGENTS.md, prompts, session transcript, where the agent was wrong
```

## Writing your own suite

```yaml
# suite.yaml
name: my-service
repo: repo                 # starting code (copied fresh per run)
tests: tests               # existing tests -> "works"
source: src                # where conventions are checked
conventions: [no-print, domain-errors, decimal-money, type-hints, module-logger, tests-added]
tasks:
  - id: add-refunds
    prompt: |
      Business request, written the way an engineer would hand it to the agent.
    hidden_tests: tasks/refunds_test.py
```

```yaml
# harnesses/<name>/harness.yaml   (+ workspace/ overlaid on the repo, + optional home/)
agent: claude          # claude | codex | crewai | replay
model: sonnet
max_turns: 30
timeout_s: 600
```

## Development

```bash
uv run pytest -q     # ~3 min; no agent calls
```

## Limitations

See [docs/one-pager.pdf](docs/one-pager.pdf) ([markdown](docs/one-pager.md)) for what was cut and why. In short: conventions are
only as good as the rules you encode, five tasks detect only large effects, and the
convention rules shipped here are Python-specific examples.
