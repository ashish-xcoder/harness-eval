# AGENTS.md — building harness-eval

Instructions for coding agents working on this repo (this file drove the build session in `process/`).

## What this is
`harness-eval` answers one question for a harness maintainer: *did this change to the coding-agent
harness (AGENTS.md, skills, MCP, hooks, model, agent) make the produced code better or worse?*
Trust is the product. Every feature is judged by "does this make the verdict more trustworthy?"

## Rules
- Python 3.12, run everything through `uv run` (no system Python on the dev machine).
- Core deps stay tiny: typer, pyyaml, pytest. Heavy deps (crewai, mcp) live in the `local` extra only.
- Deterministic first. A score that can be computed from files/tests beats an LLM opinion. The LLM judge is cut.
- Never trust a single run. Every comparison is paired per task, repeated over trials, with a bootstrap CI.
- An agent must never see hidden acceptance tests, and must never be able to pass by editing tests.
- Runs must be isolated from the developer's own harness (global CLAUDE.md, plugins, hooks). Verify, don't assume.
- Credentials copied into run homes are deleted in `finally`. Never write them under `examples/`.
- Every paid run is cached; re-running `evaluate` must never re-pay for a finished run.
- Windows is the dev host: use `pathlib`, `shutil.which`, no shell=True, normalise CRLF before hashing.
- No "Co-Authored-By"/AI attribution lines in commits, docs or code.

## Layout
- `src/harness_eval/` — cli, config, agents, workspace, scorers, stats, report, local_agent, mcp_server
- `examples/` — orders-service repo, 5 tasks with hidden tests, harness variants, committed results
- `tests/` — pytest; uses the `replay` agent so the whole pipeline runs for $0 in seconds

## Definition of done for a change
1. `uv run pytest -q` green.
2. `uv run harness-eval evaluate` on committed example results re-renders the report with zero agent calls.
3. If a verdict rule changed: the A/A test still says INCONCLUSIVE and the known-bad test still says REGRESSION.
