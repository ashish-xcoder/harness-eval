# harness-eval

**Did this change to our coding-agent harness make the code better or worse?**

`harness-eval` runs the same set of real coding tasks with your current harness (baseline) and
with the changed one (candidate), scores every result on four dimensions, and gives a verdict a
harness maintainer can act on: `IMPROVEMENT`, `REGRESSION`, `TRADE-OFF` or `INCONCLUSIVE`,
backed by confidence intervals and an evidence trail down to each agent's diff.

A *harness* is everything around the model: `AGENTS.md`/`CLAUDE.md`, skills, MCP servers,
hooks, settings, the model, the agent CLI itself. In this tool a harness is just a directory,
so any of those changes is evaluated the same way.

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
docs/             one-page write-up
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
